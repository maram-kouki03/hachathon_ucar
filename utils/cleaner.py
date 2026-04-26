import json
import re

def safe_parse(text):
    try:
        return json.loads(text)
    except:
        # JSON repair
        try:
            text = re.sub(r"```json|```", "", text)
            return json.loads(text)
        except:
            return None