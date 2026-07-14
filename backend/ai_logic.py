import json
import os
import re
from dotenv import load_dotenv
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY")

# Safety check for the key
if not GROQ_KEY:
    # Note: Avoid hardcoding keys in production; always use .env
    GROQ_KEY = "your_fallback_key_here"

client = Groq(api_key=GROQ_KEY.strip())
MODEL_ID = "llama-3.3-70b-versatile"

def clean_text(text):
    """Removes excessive whitespace and non-printable characters."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_optimized_text(text, max_chars=15000):
    """
    Truncates text to fit within context windows while ensuring 
    we don't cut off in the middle of a word.
    """
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')
    return truncated[:last_space]

@retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=2, min=2, max=10),
    before_sleep=lambda retry_state: print(f"⚠️ Groq Busy. Retrying in {retry_state.next_action.sleep}s...")
)
def call_groq_api(prompt):
    """Calls Groq Llama 3 with JSON mode enabled and strict system instructions."""
    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a BCA Academic Professor specializing in Computer Science. "
                        "You MUST respond ONLY with a valid JSON object. No conversational filler."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.15 
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"❗ API Call Error: {e}")
        raise e

# --- SECURE QUIZ GENERATION ---
def generate_secure_quiz(text):
    """Generates MCQs with BCA Academic Standards."""
    cleaned = clean_text(text)
    short_text = get_optimized_text(cleaned, max_chars=8000)

    prompt = f"""
    Generate a 5-question multiple-choice quiz based on the technical text below.
    
    STRICT RULES:
    1. **Uniformity**: All 4 options must be similar in length and technical complexity.
    2. **Difficulty**: Focus on 'Why' and 'How' rather than simple 'What' questions.
    
    JSON STRUCTURE:
    {{
      "quiz": [
        {{
          "question": "string",
          "options": ["opt1", "opt2", "opt3", "opt4"],
          "correct": "exact string match"
        }}
      ]
    }}

    TEXT:
    {short_text}
    """
    try:
        print(f"🔒 Generating Secure Integrity Quiz...")
        result = call_groq_api(prompt)
        return result.get("quiz", [])
    except:
        return []

# --- ADAPTIVE STUDY MATERIAL GENERATION ---
def generate_study_material(text, target_topic=None, num_questions=5):
    """
    Processes extracted text and returns a full Study Suite with 
    questions categorized by BCA exam marks (2, 5, 10 marks).
    """
    cleaned = clean_text(text)
    short_text = get_optimized_text(cleaned, max_chars=18000) 

    focus_msg = f"TARGET FOCUS: {target_topic}" if target_topic else "Focus: General Comprehensive Review"
    
    prompt = f"""
    {focus_msg}
    Analyze the text and create a BCA-level exam preparation suite in JSON.
    
    REQUIREMENTS:
    - Summary: 3-5 technical sentences explaining core concepts.
    - Notes: Comprehensive bullet points for revision.
    - Important Questions: Group exactly {num_questions} questions into weightage categories:
        1. "2_marks": Brief definitions or simple logic (Short Answers).
        2. "5_marks": Detailed explanations with technical steps (Medium Answers).
        3. "10_marks": Deep architecture, comparisons, or full system explanations (Long Answers).
    
    JSON FORMAT:
    {{
      "summary": "...",
      "notes": ["pt1", "pt2"],
      "important_questions": {{
          "2_marks": [{{ "q": "...", "a": "..." }}],
          "5_marks": [{{ "q": "...", "a": "..." }}],
          "10_marks": [{{ "q": "...", "a": "..." }}]
      }},
      "schedule": [{{ "time": "9:00 AM", "task": "..." }}]
    }}

    TEXT:
    {short_text}
    """

    try:
        print(f"🚀 Generating Adaptive Study Suite with Mark Weightage...")
        data = call_groq_api(prompt)
        
        # Structure validation
        iq = data.get("important_questions", {})
        if not isinstance(iq, dict):
            # Fallback if AI provides a list instead of a mark-wise dict
            iq = {"2_marks": [], "5_marks": [], "10_marks": []}

        final_data = {
            "summary": data.get("summary", "Summary generation failed."),
            "notes": data.get("notes", ["No notes generated."]),
            "important_questions": iq,
            "schedule": data.get("schedule", [])
        }
                
        return final_data

    except Exception as e:
        print(f"❌ Critical Logic Failure in ai_logic: {e}")
        return {
            "summary": "Error analyzing document content.",
            "notes": ["System was unable to parse the technical complexity."],
            "important_questions": {"2_marks": [], "5_marks": [], "10_marks": []},
            "schedule": []
        }