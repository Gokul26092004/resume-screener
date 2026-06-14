from groq import Groq
import os
from dotenv import load_dotenv
import PyPDF2

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

    # Remove NUL characters and clean text
    text = text.replace("\x00", "")
    text = text.replace("\0", "")
    text = "".join(char for char in text if char.isprintable() or char in "\n\r\t")
    return text

def parse_resume(file_path: str) -> dict:
    resume_text = extract_text_from_pdf(file_path)

    prompt = f"""
    You are a resume parser. Extract ONLY the information that is explicitly written in the resume below.
    Do NOT make up or assume any information.
    Return ONLY a valid JSON object with these fields:
    - name (string)
    - email (string)
    - phone (string)
    - skills (list of strings)
    - experience (list of strings, empty list if none found)
    - education (list of strings)

    Resume text:
    {resume_text}

    Return ONLY the JSON object. No explanation, no markdown, no code blocks.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "raw_text": resume_text,
        "ai_response": response.choices[0].message.content
    }