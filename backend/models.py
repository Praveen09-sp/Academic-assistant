from sqlalchemy import Column, Integer, String
from database import Base

class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    course = Column(String)       # e.g., "BCA"
    semester = Column(String)     # e.g., "1st Sem"
    subject = Column(String)      # e.g., "DBMS"
    material_type = Column(String)# e.g., "PYQ", "Notes", "Q&A"
    title = Column(String)        # e.g., "2025 DBMS Question Paper"
    file_url = Column(String)     # Link or path to the PDF file