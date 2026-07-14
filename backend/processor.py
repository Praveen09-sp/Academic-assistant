import PyPDF2
import os
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

# --- OCR CONFIGURATION ---
# Ensure these paths match your local BCA Lab/Home PC installation
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# POPPLER_PATH is CRITICAL for pdf2image to work on Windows
POPPLER_PATH = r'C:\Program Files\poppler-24.02.0\Library\bin' 

def extract_text_from_pdf(file_path: str):
    """
    Goal: Extracts text from digital PDFs or triggers OCR for scanned/handwritten notes.
    Optimized for BCA Final Project Demo stability.
    """
    text = ""
    try:
        # 1. Try Standard Digital Extraction first (Fastest)
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        # 2. SMART CHECK: Trigger OCR if digital text is empty or too short (Scanned PDF)
        if len(text.strip()) < 50:
            print(f"🔍 Digital text missing in {os.path.basename(file_path)}. Starting OCR...")
            
            # Use a slightly lower DPI (200) for demo speed, but keep quality high enough for AI
            # 'thread_count' helps speed up the conversion process
            pages = convert_from_path(
                file_path, 
                dpi=200, 
                poppler_path=POPPLER_PATH,
                thread_count=2 
            ) 
            
            ocr_text = ""
            for page_image in pages:
                # Use Tesseract with '--psm 1' (Automatic page segmentation) for better layout detection
                ocr_text += pytesseract.image_to_string(page_image, config='--psm 1')
                # Explicitly close the image to save RAM during the demo
                page_image.close() 
            
            return ocr_text.strip()

        return text.strip()
    
    except Exception as e:
        print(f"❌ PDF Extraction Error: {e}")
        # Return a snippet so main.py knows extraction failed but didn't crash
        return ""

def extract_text_from_image(file_path: str):
    """
    Goal: Directly extracts text from JPG/PNG images of handwritten notes.
    Essential for 'Specific Topic' summaries from photo-based notes.
    """
    try:
        # Open image and use Tesseract to convert to string
        with Image.open(file_path) as img:
            text = pytesseract.image_to_string(img, config='--psm 3')
            return text.strip()
    except Exception as e:
        print(f"❌ Image OCR Error: {e}")
        return ""

if __name__ == "__main__":
    # Test block for local debugging
    # print(extract_text_from_pdf("test_notes.pdf"))
    pass