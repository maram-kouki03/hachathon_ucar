
"""
utils/ai.py — Appels Mistral AI pour extraction structurée et chatbot.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MISTRAL_API_KEY", "")
API_URL = "https://api.mistral.ai/v1/chat/completions"


def _mistral_raw(messages: list, temperature: float = 0, max_tokens: int = 2000) -> str:
    """Appel bas niveau à l'API Mistral. Lève une exception si ça échoue."""
    if not API_KEY:
        raise ValueError("MISTRAL_API_KEY non définie dans .env ou les secrets Streamlit.")

    resp = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "mistral-small-latest",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=60,
    )

    if resp.status_code != 200:
        raise ConnectionError(
            f"Mistral API error {resp.status_code}: {resp.text[:200]}"
        )

    return resp.json()["choices"][0]["message"]["content"]


# ── Extraction structurée ─────────────────────────────────────────────────────

EXTRACTION_PROMPT = """Tu es un système IA conçu pour structurer les données universitaires de l'UCAR.

Retourne UNIQUEMENT du JSON valide. Aucun texte avant ou après. Aucune balise markdown.
Si une valeur est absente du texte, utilise null (pas de guillemets, pas de chaîne vide).
Normalise les nombres : retire les espaces, virgules de milliers, symboles %.

Structure attendue :
{{
  "metadata": {{
    "institution": null,
    "department": null,
    "year": null,
    "document_type": null
  }},
  "academic": {{
    "total_students": null,
    "passed_students": null,
    "failed_students": null,
    "attendance_rate": null,
    "success_rate": null,
    "dropout_rate": null,
    "repetition_rate": null,
    "progression": null,
    "exam_results": null
  }},
  "employment": {{
    "employability_rate": null,
    "time_to_employment": null,
    "national_partnership_rate": null,
    "international_partnership_rate": null
  }},
  "finance": {{
    "budget_allocated": null,
    "budget_used": null,
    "cost_per_student": null,
    "budget_execution_rate": null
  }},
  "hr": {{
    "staff_count": null,
    "absenteeism_rate": null,
    "teaching_load": null
  }},
  "research": {{
    "publications": null,
    "projects": null,
    "funding": null
  }},
  "infrastructure": {{
    "classrooms": null,
    "occupancy_rate": null,
    "equipment_status": null
  }},
  "partnerships": {{
    "agreements": null,
    "student_mobility_in": null,
    "student_mobility_out": null
  }},
  "esg": {{
    "energy_consumption": null,
    "carbon_footprint": null,
    "recycling_rate": null,
    "mobility": null
  }}
}}

TEXTE À ANALYSER :
{text}
"""


def extract_with_ai(text: str) -> str:
    """
    Envoie le texte à Mistral et retourne le JSON brut sous forme de chaîne.
    Peut lever une exception — gérez-la dans la page Upload.
    """
    prompt = EXTRACTION_PROMPT.format(text=text)
    return _mistral_raw(
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=2000,
    )


# ── Chatbot conversationnel ───────────────────────────────────────────────────

def call_mistral(prompt: str, temperature: float = 0.3) -> str:
    """Appel générique Mistral pour le dashboard (chatbot, insights, etc.)."""
    try:
        return _mistral_raw(
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=800,
        )
    except Exception as ex:
        return f"[Mistral indisponible : {str(ex)[:100]}]"