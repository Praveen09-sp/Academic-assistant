import json
import os
import shutil
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse 
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# ... after app = FastAPI() ...
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Server is running"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For your BCA demo, "*" allows all. 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PDF GENERATION IMPORTS ---
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit

# --- IMPORT CUSTOM MODULES ---
from processor import extract_text_from_pdf
from ai_logic import generate_study_material, generate_secure_quiz
from database import init_db, save_to_history, get_all_history, save_feedback, get_history_by_id

# --- MODELS ---
class LoginRequest(BaseModel):
    username: str
    password: str

class FeedbackRequest(BaseModel):
    history_id: int
    rating: int
    comment: str

# HARDCODED ADMIN CREDENTIALS
ADMIN_USER = "admin"
ADMIN_PASS = "bca123"

# --- PDF STYLING HELPERS ---
def draw_header(c, doc_title, width, height):
    c.setFillColorRGB(0.1, 0.2, 0.4) 
    c.rect(0, height-85, width, 85, fill=1)
    c.setFillColorRGB(1, 1, 1) 
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height-40, "BCA ACADEMIC COMPANION")
    c.setFont("Helvetica", 10)
    c.drawString(50, height-65, f"Material Source: {doc_title} | Student Revision Pack")
    c.setFillColorRGB(0, 0, 0)

def check_page_break(c, y, height, width, doc_title):
    if y < 80:
        c.showPage()
        draw_header(c, doc_title, width, height)
        return height - 120 
    return y

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # Initialize the SQLite Study Database
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def calculate_q_count(text: str):
    word_count = len(text.split())
    return max(5, min(25, word_count // 500))

# --- AUTHENTICATION ENDPOINTS (Simplified for Admin) ---

@app.post("/login")
async def login(credentials: LoginRequest):
    # Fixed validation for project simplicity
    if credentials.username == ADMIN_USER and credentials.password == ADMIN_PASS:
        return {
            "status": "success", 
            "user": ADMIN_USER, 
            "token": "admin_session_token"
        }
    raise HTTPException(status_code=401, detail="Invalid Student Credentials")

# --- ACADEMIC ENDPOINTS ---

@app.post("/upload")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    target_topic: str = Form(None)
):
    combined_text = ""
    filenames = []

    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        filenames.append(file.filename)
        combined_text += f"\n {extract_text_from_pdf(file_path)}"

    if not combined_text.strip():
        raise HTTPException(status_code=400, detail="No readable text found.")

    try:
        needed_questions = calculate_q_count(combined_text)
        study_data = generate_study_material(combined_text, target_topic=target_topic, num_questions=needed_questions)
        secure_quiz = generate_secure_quiz(combined_text)
        
        full_package = {**study_data, "secure_quiz": secure_quiz}
        batch_name = filenames[0] if filenames else "Academic Session"
        study_json = json.dumps(full_package)
        
        # We no longer pass 'username' from the frontend; 
        # database.py handles the 'admin' tag internally.
        history_id = save_to_history(batch_name, study_json)
        
        return {"id": history_id, **full_package}
    except Exception as e:
        print(f"❌ Upload Error: {e}")
        return {"id": 0, "summary": "Error during processing.", "notes": [], "important_questions": {}}

@app.get("/history")
async def fetch_history():
    # Database logic now defaults to fetching 'admin' records
    return get_all_history()

@app.get("/quiz/{history_id}")
async def get_quiz(history_id: int):
    record = get_history_by_id(history_id)
    if not record:
        raise HTTPException(status_code=404, detail="Session not found")
    # record[2] is the 'content' column containing the JSON string
    data = json.loads(record[2]) if isinstance(record[2], str) else record[2]
    return data.get("secure_quiz", [])

@app.get("/download/{history_id}")
async def download_pdf(history_id: int):
    record = get_history_by_id(history_id)
    if not record:
        raise HTTPException(status_code=404, detail="Session not found")
    
    filename, content_json = record[0], record[2] # Adjusting based on fetchone() order
    content = json.loads(content_json)
    
    pdf_filename = f"BCA_Revision_{history_id}.pdf"
    pdf_path = os.path.join(UPLOAD_DIR, pdf_filename)
    
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    draw_header(c, filename, width, height)
    y = height - 120

    # Summary
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Executive Summary")
    y -= 20
    c.setFont("Helvetica", 11)
    summary_text = content.get("summary", "No summary provided.")
    for line in simpleSplit(summary_text, "Helvetica", 11, width-100):
        y = check_page_break(c, y, height, width, filename)
        c.drawString(50, y, line)
        y -= 15

    # Section-Wise Q&A (Condensed logic)
    y -= 30
    q_data = content.get("important_questions", {})
    for label, key in [("2 Marks", "2_marks"), ("5 Marks", "5_marks"), ("10 Marks", "10_marks")]:
        questions = q_data.get(key, [])
        if not questions: continue
        y = check_page_break(c, y, height, width, filename)
        c.setFont("Helvetica-BoldOblique", 12)
        c.drawString(50, y, f"--- Section: {label} ---")
        y -= 20
        for item in questions:
            y = check_page_break(c, y, height, width, filename)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y, f"Q: {item.get('q')}")
            y -= 15
            c.setFont("Helvetica", 10)
            for aline in simpleSplit(f"A: {item.get('a')}", "Helvetica", 10, width-120):
                y = check_page_break(c, y, height, width, filename)
                c.drawString(70, y, aline)
                y -= 14
            y -= 10

    c.save()
    return FileResponse(pdf_path, media_type='application/pdf', filename=pdf_filename)

@app.post("/feedback")
async def submit_feedback(f: FeedbackRequest):
    if f.history_id > 0:
        # database.py handles tagging this to 'admin'
        save_feedback(f.history_id, f.rating, f.comment)
        return {"status": "success"}
    return {"status": "ignored"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)