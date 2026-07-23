from database import SessionLocal, engine
import models

# Ensure the database tables exist
models.Base.metadata.create_all(bind=engine)

# Open a session to talk to SQLite
db = SessionLocal()

# 1. Define the items you want to insert
sample_materials = [
    models.Material(
        course="BCA",
        semester="1st Sem",
        subject="DBMS",
        material_type="PYQ",
        title="2025 DBMS Question Paper",
        file_url="/uploads/dbms_2025_pyq.pdf"
    ),
    models.Material(
        course="BCA",
        semester="1st Sem",
        subject="DBMS",
        material_type="Notes",
        title="DBMS Unit 1 Complete Notes",
        file_url="/uploads/dbms_unit1_notes.pdf"
    ),
    models.Material(
        course="BCA",
        semester="2nd Sem",
        subject="Data Structures",
        material_type="Q&A",
        title="Data Structures Important Q&A",
        file_url="/uploads/ds_qa.pdf"
    )
]

# 2. Add and commit all items to the database
db.add_all(sample_materials)
db.commit()

print("✅ Data inserted successfully into study_companion.db!")

# Close session
db.close()