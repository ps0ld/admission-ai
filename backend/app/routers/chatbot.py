"""
Admission counsellor chatbot.

It never invents admission numbers: all colleges/probabilities come from the
same DB + ML code as the rest of the app. A rule-based parser understands
English/Hinglish messages ("mere 68k rank hai, UP se hu aur CSE chahiye").
If ANTHROPIC_API_KEY is set, an LLM rewrites the grounded result into a
friendlier answer; otherwise (or on any failure) the rule-based reply is used.
"""
import json
import os
import re
import urllib.request
from typing import Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, auth
from app.routers.colleges import match_colleges

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

STATE_ALIASES = {
    "UP": ["uttar pradesh"], "Delhi": ["delhi"], "MP": ["madhya pradesh"],
    "Bihar": ["bihar"], "Rajasthan": ["rajasthan"], "Maharashtra": ["maharashtra"],
}
BRANCH_ALIASES = {
    "CSE": ["cse", "computer science", "computer"], "IT": ["information technology"],
    "ECE": ["ece", "electronics"], "ME": ["mechanical", "mech"], "CE": ["civil"],
}
CATEGORIES = ["General", "OBC", "SC", "ST", "EWS"]


class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None


def parse_message(text: str, ctx: dict) -> dict:
    """Extract rank/state/branch/category from a free-text message; keep old context otherwise."""
    ctx = dict(ctx or {})
    low = text.lower()

    m = re.search(r"(\d+(?:\.\d+)?)\s*k\b", low)
    if m:
        ctx["rank"] = int(float(m.group(1)) * 1000)
    else:
        m = re.search(r"\b(\d{3,7})\b", low.replace(",", ""))
        if m:
            ctx["rank"] = int(m.group(1))

    for state, names in STATE_ALIASES.items():
        hit = any(n in low for n in names)
        if state in ("UP", "MP"):  # short codes clash with normal words ("up", "mp")
            hit = hit or bool(re.search(rf"\b{state}\b", text)) or \
                bool(re.search(rf"\b{state.lower()}\b\s*(se|ke|ka|ki|mein|state|domicile|quota)", low))
        else:
            hit = hit or bool(re.search(rf"\b{state.lower()}\b", low))
        if hit:
            ctx["state"] = state
    for branch, names in BRANCH_ALIASES.items():
        if any(re.search(rf"\b{re.escape(n)}\b", low) for n in names) or (branch == "IT" and re.search(r"\bIT\b", text)):
            ctx["branch"] = branch
    for cat in CATEGORIES:
        if re.search(rf"\b{cat.lower()}\b", low):
            ctx["category"] = cat
    return ctx


def _fmt_matches(matches, limit=6):
    lines = []
    for m in matches[:limit]:
        lines.append(f"- {m.name} ({m.branch}): ~{round(m.estimated_chance * 100)}% chance, last cutoff {m.previous_cutoff:,} [{m.category_bucket}]")
    return "\n".join(lines)


def _llm_rewrite(user_msg: str, grounded: str) -> Optional[str]:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None
    body = {
        "model": os.getenv("CHATBOT_MODEL", "claude-sonnet-4-6"),
        "max_tokens": 500,
        "system": ("You are an engineering admission counsellor for Indian students. Reply in the same "
                   "language style as the student (Hinglish if they use it), short and friendly. Use ONLY "
                   "the data provided; never invent colleges, ranks or probabilities. Say these are "
                   "estimates, not guarantees."),
        "messages": [{"role": "user", "content": f"Student message: {user_msg}\n\nData from our system:\n{grounded}"}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text") or None
    except Exception:
        return None


@router.post("")
def chat(payload: ChatRequest, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    text = payload.message.strip()
    low = text.lower()
    ctx = parse_message(text, payload.context or {})
    profile = db.query(models.StudentProfile).filter(models.StudentProfile.user_id == user.id).first()

    # Explain last prediction
    if re.search(r"\b(why|kyu|kyun|explain|samjha)", low) and not re.search(r"\d{3,}", low):
        last = (db.query(models.PredictionHistory).filter(models.PredictionHistory.user_id == user.id)
                .order_by(models.PredictionHistory.created_at.desc()).first())
        if not last:
            return {"reply": "Abhi tak koi prediction nahi hui. Pehle Predict page pe apna rank daalo, phir main explain kar dunga.", "colleges": [], "context": ctx, "source": "rules"}
        factors = json.loads(last.explanation or "[]")[:3]
        grounded = f"Latest prediction: {round(last.probability * 100)}% ({last.label}). Top factors: " + \
                   "; ".join(f"{f['feature']} {'increases' if f['direction'] == 'positive' else 'reduces'} chance" for f in factors)
        reply = _llm_rewrite(text, grounded) or grounded
        return {"reply": reply, "colleges": [], "context": ctx, "source": "llm" if reply != grounded else "rules"}

    # Fall back to saved profile for missing info
    if profile:
        if profile.entrance_rank:
            ctx.setdefault("rank", profile.entrance_rank)
        if profile.category:
            ctx.setdefault("category", profile.category)
        if profile.preferred_branch:
            ctx.setdefault("branch", profile.preferred_branch)
        if profile.preferred_state:
            ctx.setdefault("state", profile.preferred_state)

    wants_colleges = bool(re.search(r"college|option|suggest|recommend|chahiye|chance|milega|milegi|admission|safe|reach|target", low)) or ctx.get("rank")
    if not ctx.get("rank"):
        return {"reply": ("Namaste! Main tumhara Admission AI counsellor hoon. Apna rank batao, jaise: "
                          "\"mere 68k rank hai, UP se hu aur CSE chahiye\" - main matching colleges bata dunga."),
                "colleges": [], "context": ctx, "source": "rules"}

    if not wants_colleges:
        return {"reply": "Rank noted. Kaunsa branch ya state chahiye? Ya seedha bolo 'colleges suggest karo'.", "colleges": [], "context": ctx, "source": "rules"}

    matches = match_colleges(db, int(ctx["rank"]), ctx.get("category", "General"),
                             state=ctx.get("state"), branch=ctx.get("branch"))
    filt = ", ".join(f"{k}={v}" for k, v in ctx.items() if v)
    if not matches:
        return {"reply": f"In filters ({filt}) pe koi college nahi mila. State ya branch filter hata ke try karo.",
                "colleges": [], "context": ctx, "source": "rules"}

    grounded = f"Filters: {filt}\nMatches (best first):\n{_fmt_matches(matches)}"
    rule_reply = f"Rank {int(ctx['rank']):,} ({ctx.get('category', 'General')}) ke hisaab se ye best options hain. " \
                 f"Ye estimates hain, guarantee nahi:\n{_fmt_matches(matches, 5)}"
    reply = _llm_rewrite(text, grounded) or rule_reply
    return {
        "reply": reply,
        "colleges": [m.model_dump() for m in matches[:6]],
        "context": ctx,
        "source": "llm" if reply != rule_reply else "rules",
    }
