# Admission AI — AI-Based Student Admission Prediction System

A full-stack, ML-powered admission prediction and college recommendation platform.

## Stack
- Frontend: React + Vite + Tailwind CSS + Recharts
- Backend: FastAPI + SQLAlchemy + JWT auth
- ML: Scikit-learn + XGBoost, compared automatically; SHAP for explainability
- Database: PostgreSQL (SQLite fallback for local dev)

## What's included
- Signup/login (JWT + bcrypt), role-based access (student/admin)
- Student profile
- AI admission prediction with SHAP "why this prediction?" explanation
- College Predictor with filters + Safe/Target/Reach recommendations
- Cutoff trend data per college
- Student dashboard (cards + prediction trend chart)
- Admin dashboard: add/edit/delete colleges, upload CSV dataset, train model
  (Logistic Regression vs Random Forest vs XGBoost, best one auto-selected by ROC-AUC)
- Seed script with demo colleges + cutoff history + admin account
- Synthetic dataset generator so you can train immediately without needing
  real historical admission data on day one

## New in this version
- **AI chatbot** ("Ask Admission AI", floating button): understands Hinglish like
  "mere 68k rank hai, UP se hu aur CSE chahiye", remembers rank/state/branch during
  the chat, explains your last prediction, and shows Safe/Target/Reach colleges.
  All numbers come from the app's own DB + ML, never invented. Optional: set
  `ANTHROPIC_API_KEY` (and `CHATBOT_MODEL`) on the backend so an LLM phrases the
  answer more naturally; without a key the rule-based reply is used.
- **Saved colleges** (heart button) + Saved page
- **Compare colleges** (up to 4): side-by-side table + cutoff trend chart
- **PDF report**: Dashboard -> "Download PDF Report" (profile, latest prediction with
  factors, history, recommendations, saved colleges, model ROC-AUC note)

## What's still not included
- Email verification / forgot-password (needs an email service such as SMTP/Resend)
- Deadline tracker, alerts/notifications, dark mode

---

## 1. Local setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

# generate demo data + train a first model
cd ..
mkdir -p ml/datasets
python ml/generate_synthetic_data.py
python ml/train.py

# seed colleges + admin user, then run the API
cd backend
python seed.py
uvicorn app.main:app --reload --port 8000
```
API docs available at `http://localhost:8000/docs`.

Demo admin login: `admin@admission-ai.com` / `Admin@123` — **change this password
before going live.**

### Frontend
```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```
Open `http://localhost:5173`.

---

## 2. Deployment

### Backend → Render
1. Push this repo to GitHub (whole repo, keep `ml/` next to `backend/`).
2. Render → New + → Web Service → connect repo. **Leave Root Directory blank.**
3. Build command: `pip install -r backend/requirements.txt`
4. Start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Environment variables:
   - `DATABASE_URL` → Supabase Postgres connection string
   - `SECRET_KEY` → long random string
   - `PYTHON_VERSION` → `3.12.3`
   - `ANTHROPIC_API_KEY` → optional, only for LLM-phrased chatbot replies
6. Nothing else to run manually: on first boot the app seeds demo colleges +
   admin user and trains a first model automatically (takes ~30-60s).
   Render free disk is ephemeral, so the model retrains on each restart; for
   real data, upload your CSV in Admin and retrain, or commit `backend/ml_artifacts/`.

Free tier cold-starts after inactivity (~30-50s). Show a loading state in the UI.
**Change the admin password** (`seed.py`) before sharing the link publicly.

### Database → Supabase (recommended) or Render Postgres
- Supabase free tier doesn't expire (Render's free Postgres is a 90-day trial).
- Create a project, copy the connection string, set it as `DATABASE_URL` on
  the backend service. Use the `postgresql://` (session pooler) URI.

### Frontend → Vercel
1. Vercel → New Project → import the repo, root directory `frontend`.
2. Framework preset: Vite.
3. Environment variable: `VITE_API_URL` = your Render backend URL
   (e.g. `https://admission-ai-backend.onrender.com`).
4. Deploy.

### CORS
In `backend/app/main.py`, replace `allow_origins=["*"]` with your actual
Vercel domain before going live.

---

## 3. Replacing synthetic data with real data
Upload a CSV via **Admin → Dataset Management** with these columns:
```
student_score, entrance_rank, category, state, college, branch, cutoff, year, admitted
```
Then click **Train Model**. The backend validates, cleans, retrains all
three algorithms, and activates whichever scores highest on ROC-AUC —
metrics are shown in the admin panel so you never have to claim an
accuracy number you can't back up.
