import io
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from app.database import get_db
from app import models, auth
from app.routers.colleges import match_colleges

router = APIRouter(prefix="/report", tags=["Report"])

BRAND = colors.HexColor("#4f46e5")


def _table(data, col_widths=None):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


@router.get("/pdf")
def download_report(user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    profile = db.query(models.StudentProfile).filter(models.StudentProfile.user_id == user.id).first()
    history = (db.query(models.PredictionHistory)
               .filter(models.PredictionHistory.user_id == user.id)
               .order_by(models.PredictionHistory.created_at.desc()).limit(10).all())
    saved = (db.query(models.SavedCollege).filter(models.SavedCollege.user_id == user.id).all())
    model_v = db.query(models.ModelVersion).filter(models.ModelVersion.is_active == True).first()

    styles = getSampleStyleSheet()
    h2 = styles["Heading2"]
    h2.textColor = BRAND
    body = styles["BodyText"]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm, title="Admission Report")
    el = []
    el.append(Paragraph("Admission AI - Prediction Report", styles["Title"]))
    el.append(Paragraph(f"{user.name} ({user.email}) &nbsp;|&nbsp; Generated {datetime.now():%d %b %Y, %H:%M}", body))
    el.append(Spacer(1, 12))

    # Profile
    el.append(Paragraph("Academic Profile", h2))
    if profile:
        rows = [["Field", "Value"],
                ["Category", profile.category or "-"], ["State", profile.state or "-"],
                ["10th %", profile.tenth_pct if profile.tenth_pct is not None else "-"],
                ["12th %", profile.twelfth_pct if profile.twelfth_pct is not None else "-"],
                ["Diploma %", profile.diploma_pct if profile.diploma_pct is not None else "-"],
                ["Entrance exam", profile.entrance_exam or "-"],
                ["Entrance rank", profile.entrance_rank if profile.entrance_rank is not None else "-"],
                ["Preferred branch", profile.preferred_branch or "-"],
                ["Preferred state", profile.preferred_state or "-"],
                ["Budget (max)", f"Rs. {int(profile.budget_max):,}" if profile.budget_max else "-"]]
        el.append(_table(rows, [6 * cm, 10 * cm]))
    else:
        el.append(Paragraph("Profile not filled yet.", body))
    el.append(Spacer(1, 12))

    # Latest prediction + factors
    el.append(Paragraph("Latest AI Prediction", h2))
    if history:
        last = history[0]
        el.append(Paragraph(f"<b>Admission probability: {round(last.probability * 100)}%</b> ({last.label})", body))
        try:
            factors = json.loads(last.explanation or "[]")[:5]
        except Exception:
            factors = []
        if factors:
            rows = [["Factor", "Effect", "Impact"]] + [
                [f["feature"], "Increases chance" if f["direction"] == "positive" else "Reduces chance",
                 f"{abs(f['impact']):.3f}"] for f in factors]
            el.append(Spacer(1, 6))
            el.append(_table(rows, [6 * cm, 5 * cm, 4 * cm]))
    else:
        el.append(Paragraph("No predictions made yet.", body))
    el.append(Spacer(1, 12))

    # History
    if history:
        el.append(Paragraph("Prediction History (last 10)", h2))
        rows = [["Date", "Probability", "Result"]] + [
            [h.created_at.strftime("%d %b %Y %H:%M") if h.created_at else "-",
             f"{round(h.probability * 100)}%", h.label] for h in history]
        el.append(_table(rows, [6 * cm, 4 * cm, 6 * cm]))
        el.append(Spacer(1, 12))

    # Recommendations
    if profile and profile.entrance_rank:
        matches = match_colleges(db, profile.entrance_rank, profile.category or "General",
                                 state=profile.preferred_state or None,
                                 branch=profile.preferred_branch or None)
        if matches:
            el.append(Paragraph("College Recommendations", h2))
            rows = [["College", "Branch", "Bucket", "Est. chance", "Last cutoff"]]
            for bucket in ("Safe", "Target", "Reach"):
                for m in [x for x in matches if x.category_bucket == bucket][:3]:
                    rows.append([m.name, m.branch, bucket, f"{round(m.estimated_chance * 100)}%", f"{m.previous_cutoff:,}"])
            el.append(_table(rows, [5.5 * cm, 2 * cm, 2 * cm, 3 * cm, 3.5 * cm]))
            el.append(Spacer(1, 12))

    # Saved colleges
    if saved:
        el.append(Paragraph("Saved Colleges", h2))
        rows = [["College", "Branch", "State", "Fees"]] + [
            [s.college.name, s.college.branch, s.college.state, f"Rs. {int(s.college.fees):,}"] for s in saved]
        el.append(_table(rows, [7 * cm, 2.5 * cm, 3 * cm, 3.5 * cm]))
        el.append(Spacer(1, 12))

    # Honest disclaimer
    note = "All figures are statistical estimates, not guarantees of admission."
    if model_v:
        note += (f" Active model: {model_v.algorithm} ({model_v.version}), validation ROC-AUC "
                 f"{model_v.roc_auc}. Reliability depends on the quality of the training dataset.")
    el.append(Paragraph(f"<font size=8 color='#64748b'>{note}</font>", body))

    doc.build(el)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf",
                             headers={"Content-Disposition": 'attachment; filename="admission-report.pdf"'})
