"""
Generates a synthetic admission dataset for demo/training purposes.
Replace this with real historical admission data (CSV) via the admin
dataset-upload feature once you have credible data. Columns match the
schema described in the project plan:
student_score, entrance_rank, category, state, college, branch, cutoff, year, admitted
"""
import os
import numpy as np
import pandas as pd

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PATH = os.path.join(OUT_DIR, "synthetic_admissions.csv")

np.random.seed(42)

STATES = ["UP", "Delhi", "MP", "Bihar", "Rajasthan", "Maharashtra"]
BRANCHES = ["CSE", "IT", "ECE", "ME", "CE"]
CATEGORIES = ["General", "OBC", "SC", "ST", "EWS"]
COLLEGES = [f"College {c}" for c in "ABCDEFGHIJ"]

CATEGORY_RANK_RELAXATION = {
    "General": 0,
    "EWS": 2000,
    "OBC": 5000,
    "SC": 12000,
    "ST": 15000,
}

N = 6000
rows = []
for _ in range(N):
    college = np.random.choice(COLLEGES)
    branch = np.random.choice(BRANCHES)
    state = np.random.choice(STATES)
    category = np.random.choice(CATEGORIES)
    year = np.random.choice([2023, 2024, 2025, 2026])

    base_cutoff = np.random.randint(15000, 60000)
    cutoff = max(500, base_cutoff - CATEGORY_RANK_RELAXATION.get(category, 0))

    rank = int(np.random.normal(loc=cutoff, scale=cutoff * 0.35))
    rank = max(1, rank)

    student_score = np.clip(np.random.normal(loc=78, scale=10), 40, 99)

    # Admission probability rule-of-thumb for label generation (ground truth
    # simulation only — the model learns the pattern, it isn't hardcoded).
    admitted = 1 if rank <= cutoff * np.random.uniform(0.95, 1.05) else 0

    rows.append({
        "student_score": round(student_score, 2),
        "entrance_rank": rank,
        "category": category,
        "state": state,
        "college": college,
        "branch": branch,
        "cutoff": cutoff,
        "year": year,
        "admitted": admitted,
    })

df = pd.DataFrame(rows)
df.to_csv(OUT_PATH, index=False)
print(f"Generated {len(df)} rows -> {OUT_PATH}")
print(df["admitted"].value_counts(normalize=True))
