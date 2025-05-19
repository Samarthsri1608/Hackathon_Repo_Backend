import spacy
from spacy.matcher import PhraseMatcher
import fitz  # PyMuPDF
import json

nlp = spacy.load("en_core_web_sm")
matcher = PhraseMatcher(nlp.vocab)

# Load skill keywords from JSON
with open("skills.json", "r") as f:
    skill_keywords = json.load(f)["skills"]

patterns = [nlp.make_doc(skill) for skill in skill_keywords]
matcher.add("SKILLS", patterns)

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = "\n".join([page.get_text() for page in doc])
    return text

def extract_skills_from_text(text):
    doc = nlp(text)
    matches = matcher(doc)
    return list(set([doc[start:end].text for _, start, end in matches]))
