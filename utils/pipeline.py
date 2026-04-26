from utils.extractor import extract_text
from utils.ai import extract_with_ai
import json

def process_file(file):
    # 1. extract raw text
    raw_text = extract_text(file)

    # 2. AI structuring
    structured = extract_with_ai(raw_text)

    # 3. convert string → dict
    try:
        data = json.loads(structured)
    except:
        data = {"error": "AI returned invalid JSON"}

    return data