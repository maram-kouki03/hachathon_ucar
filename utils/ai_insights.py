"""
utils/ai_insights.py — Tous les appels IA via Mistral uniquement.
"""
import os
import json
import requests
import streamlit as st

from dotenv import load_dotenv
load_dotenv()


def _call_mistral(messages: list, max_tokens: int = 800) -> str:
    api_key = os.getenv("MISTRAL_API_KEY") or st.secrets.get("MISTRAL_API_KEY", "")
    if not api_key:
        return "[Mistral indisponible : MISTRAL_API_KEY non définie]"
    try:
        resp = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "mistral-small-latest",
                "messages": messages,
                "temperature": 0.4,
                "max_tokens": max_tokens,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as ex:
        return f"[Mistral indisponible: {str(ex)[:100]}]"


def _prompt(content: str, system: str = None, max_tokens: int = 700) -> str:
    """Helper : appel simple avec un prompt utilisateur + system optionnel."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": content})
    return _call_mistral(messages, max_tokens=max_tokens)


# ── Executive insight (bandeau dashboard) ────────────────────────────────────

def generate_executive_insight(context: dict = None) -> str:
    ctx = context or {}
    return _prompt(
        f"Tu es l'assistant analytique de l'Université de Carthage (UCAR). "
        f"Génère UNE SEULE phrase d'alerte ou d'insight executive concise (max 180 caractères) "
        f"pour le bandeau du dashboard de direction. "
        f"Contexte: {json.dumps(ctx, ensure_ascii=False)}",
        max_tokens=120,
    )


# ── Analyse par domaine ───────────────────────────────────────────────────────

def generate_domain_insight(domain: str, data: dict = None) -> str:
    return _prompt(
        f"Tu es analyste senior à l'Université de Carthage.\n"
        f"Génère une analyse structurée du domaine **{domain}** basée sur ces données réelles UCAR.\n"
        f"Données: {json.dumps(data or {}, ensure_ascii=False)}\n\n"
        "Structure: état actuel avec métriques, tendances, alertes (max 2), recommandations (max 3).\n"
        "Format markdown avec titres et puces. Maximum 350 mots.",
        max_tokens=700,
    )


# ── Narrative de prédiction ───────────────────────────────────────────────────

def generate_prediction_narrative(target: str, institution: str, pred_result: dict) -> str:
    return _prompt(
        f"Tu es un analyste prédictif à l'UCAR.\n"
        f"Génère une analyse narrative des prédictions pour **{target}** à **{institution}**.\n"
        f"Résultats: {json.dumps(pred_result, ensure_ascii=False)}\n\n"
        "Include: interprétation de la tendance, facteurs explicatifs (3 max), risques, "
        "recommandation stratégique. Texte fluide en français, max 250 mots.",
        max_tokens=500,
    )


# ── Analyse comparative ───────────────────────────────────────────────────────

def generate_comparative_analysis(inst_a: str, inst_b: str, df) -> str:
    row_a = df[df["Institution"] == inst_a].to_dict("records")
    row_b = df[df["Institution"] == inst_b].to_dict("records")
    data_a = row_a[0] if row_a else {}
    data_b = row_b[0] if row_b else {}
    return _prompt(
        f"Compare **{inst_a}** et **{inst_b}** de l'UCAR.\n"
        f"Données {inst_a}: {json.dumps(data_a, ensure_ascii=False)}\n"
        f"Données {inst_b}: {json.dumps(data_b, ensure_ascii=False)}\n\n"
        "Structure: points forts de chaque institution, points d'amélioration, "
        "recommandations de partage, conclusion et score comparatif. "
        "Format markdown structuré, max 300 mots.",
        max_tokens=600,
    )


# ── Chatbot conversationnel ───────────────────────────────────────────────────

SYSTEM_PROMPT = """Tu es l'assistant intelligent UCAR (Université de Carthage).
Tu as accès aux données institutionnelles de plus de 30 établissements.
Réponds en français, de manière concise et structurée.
Utilise des emojis pour structurer la réponse.
Si des données précises ne sont pas disponibles dans le contexte fourni, indique-le clairement.
Ne fabrique pas de chiffres."""


def answer_question_mistral(question: str, history: list = None, db_context: str = "") -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if db_context:
        messages.append({"role": "system", "content": f"Données disponibles:\n{db_context}"})
    if history:
        for msg in history[-8:]:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
    messages.append({"role": "user", "content": question})
    return _call_mistral(messages, max_tokens=800)


# ── Résumé de rapport ─────────────────────────────────────────────────────────

def generate_report_summary(report_content: str) -> str:
    return _prompt(
        "Génère une synthèse exécutive en 3 points clés (bullet points) du rapport suivant.\n"
        "Chaque point doit être une phrase d'action ou d'alerte.\n"
        "Format: • Point 1\n• Point 2\n• Point 3\n\n"
        f"Rapport:\n{report_content[:2000]}",
        max_tokens=200,
    )