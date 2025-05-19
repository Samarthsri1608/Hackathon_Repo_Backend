from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import fitz  # PyMuPDF
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
from pathlib import Path

app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load skill list from skills.json
with open(Path(__file__).parent / "skills.json", "r") as f:
    skill_list = json.load(f)

def extract_text_from_pdf(uploaded_file):
    contents = uploaded_file.file.read()
    with fitz.open(stream=contents, filetype="pdf") as doc:
        text = "\n".join([page.get_text() for page in doc])
    return text

def extract_skills(text):
    text = text.lower()
    found_skills = [skill for skill in skill_list if skill.lower() in text]
    return list(set(found_skills))


@app.post("/extract")
async def extract_skills_from_resume(file: UploadFile = File(...)):
    text = extract_text_from_pdf(file)
    skills = extract_skills(text)
    return {"skills": skills}

@app.post("/match-score")
async def match_score(
    resume: UploadFile = File(...),
    job_description: Optional[UploadFile] = File(None),
    job_description_text: Optional[str] = Form(None),
):
    resume_text = extract_text_from_pdf(resume)
    resume_skills = extract_skills(resume_text)

    if job_description:
        jd_text = extract_text_from_pdf(job_description)
    elif job_description_text:
        jd_text = job_description_text
    else:
        return {"error": "No job description provided."}

    jd_skills = extract_skills(jd_text)

    print("Extracted Resume Skills : ", resume_skills)
    print("Extracted JD Skills : ", jd_skills)

    if not resume_skills or not jd_skills:
        return {"score": 0.0, "matched_skills": [], "resume_skills": resume_skills, "jd_skills": jd_skills}

    vectorizer = CountVectorizer().fit_transform([" ".join(resume_skills), " ".join(jd_skills)])
    vectors = vectorizer.toarray()
    score = cosine_similarity([vectors[0]], [vectors[1]])[0][0]

    print("Match Score : ", round(float(score), 2))

    matched = list(set(resume_skills).intersection(set(jd_skills)))

    return {
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,
        "matched_skills": matched,
        "score": round(float(score), 2)        
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)