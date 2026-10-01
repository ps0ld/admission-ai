"""
Seeds the database with demo colleges, multi-year cutoffs, and an admin user.
Run once after setting up the database: python seed.py
"""
from app.database import SessionLocal, Base, engine
from app import models, auth

Base.metadata.create_all(bind=engine)
db = SessionLocal()

STATES = ["UP", "Delhi", "MP", "Bihar", "Rajasthan", "Maharashtra"]
BRANCHES = ["CSE", "IT", "ECE", "ME", "CE"]

if db.query(models.College).count() == 0:
    colleges = []
    for i, name in enumerate(["Alpha Institute of Technology", "Beta Engineering College",
                               "Gamma University", "Delta Polytechnic", "Epsilon Tech",
                               "Zeta College of Engineering", "Eta Institute", "Theta University"]):
        for branch in BRANCHES[:3]:
            college = models.College(
                name=name,
                branch=branch,
                state=STATES[i % len(STATES)],
                city="City " + str(i + 1),
                ownership="Government" if i % 2 == 0 else "Private",
                fees=float(50000 + i * 15000),
                exam="JEE" if i % 2 == 0 else "State CET",
            )
            db.add(college)
            colleges.append(college)
    db.commit()

    import random
    for college in colleges:
        base = random.randint(15000, 55000)
        for j, year in enumerate([2023, 2024, 2025, 2026]):
            trend = base + j * random.randint(500, 2500)
            db.add(models.CutoffRecord(college_id=college.id, year=year, category="General", closing_rank=trend))
    db.commit()
    print(f"Seeded {len(colleges)} colleges with cutoff history.")
else:
    print("Colleges already seeded, skipping.")

if not db.query(models.User).filter(models.User.email == "admin@admission-ai.com").first():
    admin_user = models.User(
        name="Admin",
        email="admin@admission-ai.com",
        hashed_password=auth.hash_password("Admin@123"),
        role="admin",
    )
    db.add(admin_user)
    db.commit()
    print("Seeded admin user -> email: admin@admission-ai.com | password: Admin@123 (change this!)")
else:
    print("Admin user already exists, skipping.")

db.close()
