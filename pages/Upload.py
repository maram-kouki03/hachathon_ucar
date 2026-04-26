"""
pages/Upload.py — Pipeline complet : fichier → texte → JSON → Supabase
"""
import json
import streamlit as st

from utils.extractor import extract_text
from utils.ai import extract_with_ai
from utils.db import insert_data

_CSS = """
<style>
.upload-hero {
    background: linear-gradient(135deg, rgba(10,20,40,0.97) 0%, rgba(15,30,60,0.95) 100%);
    border: 1px solid rgba(99,179,237,0.12); border-radius: 16px;
    padding: 24px 32px; margin-bottom: 22px;
}
.step-bar {
    display: flex; gap: 0; margin-bottom: 28px; border-radius: 10px; overflow: hidden;
    border: 1px solid rgba(99,179,237,0.1);
}
.step {
    flex: 1; padding: 10px 6px; text-align: center;
    font-family: 'Syne', sans-serif; font-size: 0.72rem; font-weight: 700;
    letter-spacing: 0.5px; color: #3a5f7a; background: rgba(10,22,40,0.7);
    border-right: 1px solid rgba(99,179,237,0.08); transition: all 0.3s;
}
.step:last-child { border-right: none; }
.step.active  { background: rgba(99,179,237,0.12); color: #63b3ed; }
.step.done    { background: rgba(104,211,145,0.08); color: #68d391; }
.step.error   { background: rgba(252,129,129,0.08); color: #fc8181; }

.json-preview {
    background: rgba(5,12,22,0.9); border: 1px solid rgba(99,179,237,0.12);
    border-radius: 10px; padding: 16px; font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem; color: #63b3ed; max-height: 360px; overflow-y: auto;
    white-space: pre-wrap; word-break: break-word;
}
.field-row {
    display: flex; gap: 8px; align-items: center; padding: 7px 10px;
    border-radius: 6px; font-family: 'DM Sans', sans-serif; font-size: 0.82rem;
    border-bottom: 1px solid rgba(99,179,237,0.05);
}
.field-key   { color: #63b3ed; font-weight: 600; min-width: 180px; }
.field-val   { color: #e2e8f0; }
.field-null  { color: #3a5f7a; font-style: italic; }
.section-hdr {
    font-family: 'Syne', sans-serif; font-size: 0.7rem; font-weight: 700;
    color: #3a5f7a; text-transform: uppercase; letter-spacing: 1.5px;
    padding: 10px 10px 4px; border-top: 1px solid rgba(99,179,237,0.08);
    margin-top: 4px;
}
.stat-pill {
    display: inline-flex; align-items: center; gap: 5px;
    background: rgba(99,179,237,0.08); border: 1px solid rgba(99,179,237,0.15);
    border-radius: 20px; padding: 3px 10px;
    font-family: 'DM Sans', sans-serif; font-size: 0.75rem; color: #63b3ed;
    margin-right: 6px; margin-bottom: 6px;
}
.success-box {
    background: rgba(104,211,145,0.08); border: 1px solid rgba(104,211,145,0.2);
    border-radius: 12px; padding: 18px 20px; margin-top: 12px;
    font-family: 'DM Sans', sans-serif; font-size: 0.88rem; color: #68d391;
}
.error-box {
    background: rgba(252,129,129,0.08); border: 1px solid rgba(252,129,129,0.2);
    border-radius: 12px; padding: 18px 20px; margin-top: 12px;
    font-family: 'DM Sans', sans-serif; font-size: 0.88rem; color: #fc8181;
}
.warn-box {
    background: rgba(246,173,85,0.08); border: 1px solid rgba(246,173,85,0.2);
    border-radius: 12px; padding: 14px 18px; margin-bottom: 12px;
    font-family: 'DM Sans', sans-serif; font-size: 0.85rem; color: #f6ad55;
}
</style>
"""

# ── Helpers ──────────────────────────────────────────────────────────────────

def _parse_json_safe(raw: str) -> dict | None:
    """Try to parse JSON; strip markdown fences if needed."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(l for l in lines if not l.startswith("```"))
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _count_filled(data: dict) -> tuple[int, int]:
    """Return (filled, total) leaf values across nested dict."""
    total = filled = 0
    for v in data.values():
        if isinstance(v, dict):
            f, t = _count_filled(v)
            filled += f
            total += t
        else:
            total += 1
            if v not in (None, "", "null"):
                filled += 1
    return filled, total


def _render_steps(step: int, error: bool = False):
    labels = ["① Upload", "② Extraction", "③ Structuration IA", "④ Vérification", "⑤ Supabase"]
    html = '<div class="step-bar">'
    for i, lbl in enumerate(labels):
        if error and i == step:
            cls = "error"
        elif i < step:
            cls = "done"
        elif i == step:
            cls = "active"
        else:
            cls = ""
        html += f'<div class="step {cls}">{lbl}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def _render_json_preview(data: dict):
    """Render a human-friendly preview of the structured JSON."""
    section_icons = {
        "metadata":       ("📋", "Métadonnées"),
        "academic":       ("🎓", "Académique"),
        "employment":     ("💼", "Emploi"),
        "finance":        ("💰", "Finance"),
        "hr":             ("👥", "Ressources Humaines"),
        "research":       ("🔬", "Recherche"),
        "infrastructure": ("🏗", "Infrastructure"),
        "partnerships":   ("🤝", "Partenariats"),
        "esg":            ("🌱", "ESG / Environnement"),
    }
    for key, fields in data.items():
        icon, label = section_icons.get(key, ("📂", key.title()))
        st.markdown(f'<div class="section-hdr">{icon} {label}</div>', unsafe_allow_html=True)
        if isinstance(fields, dict):
            for field, val in fields.items():
                is_null = val in (None, "", "null")
                val_cls = "field-null" if is_null else "field-val"
                display = "—" if is_null else str(val)
                st.markdown(
                    f'<div class="field-row">'
                    f'<span class="field-key">{field}</span>'
                    f'<span class="{val_cls}">{display}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    st.markdown(_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="upload-hero">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
                <div style="font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:#e2e8f0;">
                    📥 Import de Données
                </div>
                <div style="font-family:'DM Sans',sans-serif; font-size:0.85rem; color:#3a5f7a; margin-top:4px;">
                    Importez vos documents institutionnels · Extraction IA automatique · Stockage Supabase
                </div>
            </div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:#63b3ed;
                        background:rgba(99,179,237,0.06); border:1px solid rgba(99,179,237,0.12);
                        border-radius:8px; padding:8px 14px; text-align:center;">
                PIPELINE ACTIF<br><span style="color:#63b3ed;">● MISTRAL AI</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Session state ─────────────────────────────────────────────────────────
    for k, v in {
        "upload_step": 0,
        "upload_text": "",
        "upload_json": None,
        "upload_error": "",
        "upload_inserted": False,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

    step = st.session_state.upload_step

    _render_steps(step, error=bool(st.session_state.upload_error))

    # ── Sidebar history hint ──────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("---")
        st.markdown("""
        <div style="padding: 0 4px 8px; font-family:'Syne',sans-serif; font-size:0.65rem;
                    color:#3a5f7a; text-transform:uppercase; letter-spacing:2px; font-weight:700;">
            Import rapide
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family:'DM Sans',sans-serif; font-size:0.75rem; color:#2a4a6a; line-height:1.6;">
            Formats supportés :<br>
            📄 PDF (rapports, bilans)<br>
            📊 Excel / CSV (tableaux de données)<br>
            🖼️ Images JPG/PNG (documents scannés)<br><br>
            Le pipeline extrait automatiquement les KPIs et les envoie dans Supabase.
        </div>
        """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 0 — Upload
    # ═══════════════════════════════════════════════════════════════════════════
    if step == 0:
        st.markdown("#### 📂 Sélectionnez votre fichier")

        col_up, col_info = st.columns([2, 1])

        with col_up:
            uploaded = st.file_uploader(
                "Glissez-déposez ou cliquez pour parcourir",
                type=["pdf", "xlsx", "xls", "csv", "png", "jpg", "jpeg"],
                key="file_uploader",
                label_visibility="collapsed",
            )

        with col_info:
            st.markdown("""
            <div class="warn-box">
                <strong>Conseils pour de meilleurs résultats :</strong><br>
                • Privilégiez les PDF textuels aux scans<br>
                • Les Excel avec en-têtes clairs sont traités rapidement<br>
                • Les images doivent être nettes (≥ 300 dpi)
            </div>
            """, unsafe_allow_html=True)

        if uploaded:
            suffix = uploaded.name.split(".")[-1].lower()
            size_kb = round(uploaded.size / 1024, 1)
            st.markdown(
                f'<span class="stat-pill">📄 {uploaded.name}</span>'
                f'<span class="stat-pill">📦 {size_kb} KB</span>'
                f'<span class="stat-pill">🔖 {suffix.upper()}</span>',
                unsafe_allow_html=True,
            )

            if st.button("🚀 Lancer le pipeline", type="primary", use_container_width=False):
                # ── Step 1 : Extract text ─────────────────────────────────────
                with st.spinner("⚙️ Extraction du texte en cours…"):
                    try:
                        text = extract_text(uploaded)
                    except Exception as e:
                        st.session_state.upload_error = f"Extraction échouée : {e}"
                        st.session_state.upload_step = 1
                        st.rerun()

                if not text or text.strip() == "" or text == "Unsupported file":
                    st.session_state.upload_error = (
                        "Aucun texte extrait. Vérifiez que le fichier n'est pas corrompu "
                        "et qu'il contient du texte lisible."
                    )
                    st.session_state.upload_step = 1
                    st.rerun()

                st.session_state.upload_text = text
                st.session_state.upload_error = ""
                st.session_state.upload_step = 2
                st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 1 — Extraction error
    # ═══════════════════════════════════════════════════════════════════════════
    elif step == 1:
        st.markdown(f'<div class="error-box">❌ {st.session_state.upload_error}</div>', unsafe_allow_html=True)
        if st.button("↩ Réessayer", type="primary"):
            st.session_state.upload_step = 0
            st.session_state.upload_error = ""
            st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 2 — Text extracted, launch Mistral
    # ═══════════════════════════════════════════════════════════════════════════
    elif step == 2:
        text = st.session_state.upload_text
        n_chars = len(text)

        st.markdown("#### ✅ Texte extrait avec succès")
        st.markdown(
            f'<span class="stat-pill">📝 {n_chars:,} caractères extraits</span>',
            unsafe_allow_html=True,
        )

        with st.expander("👁 Aperçu du texte brut (500 premiers caractères)"):
            st.code(text[:500], language=None)

        if st.button("🤖 Structurer avec Mistral AI", type="primary", use_container_width=False):
            with st.spinner("🧠 Mistral analyse le document… (peut prendre 10-30 s)"):
                try:
                    # Limiter à 8000 chars pour éviter le dépassement de token
                    raw_json = extract_with_ai(text[:8000])
                except Exception as e:
                    st.session_state.upload_error = f"Erreur Mistral API : {e}"
                    st.session_state.upload_step = 1
                    st.rerun()

            parsed = _parse_json_safe(raw_json)

            if parsed is None:
                # Retry once with a stricter prompt reminder
                st.warning("⚠️ JSON invalide reçu, nouvelle tentative…")
                try:
                    raw_json2 = extract_with_ai(text[:4000])
                    parsed = _parse_json_safe(raw_json2)
                except Exception:
                    parsed = None

            if parsed is None:
                st.session_state.upload_error = (
                    "Mistral n'a pas retourné un JSON valide après 2 tentatives. "
                    "Essayez avec un fichier contenant plus de données structurées."
                )
                st.session_state.upload_step = 1
                st.rerun()

            st.session_state.upload_json = parsed
            st.session_state.upload_error = ""
            st.session_state.upload_step = 3
            st.rerun()

        if st.button("↩ Recommencer", use_container_width=False):
            st.session_state.upload_step = 0
            st.session_state.upload_text = ""
            st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 3 — JSON preview + validation
    # ═══════════════════════════════════════════════════════════════════════════
    elif step == 3:
        data = st.session_state.upload_json
        filled, total = _count_filled(data)
        pct = round(filled / total * 100) if total else 0

        st.markdown("#### 📊 Données structurées par Mistral AI")

        col_stats, col_edit = st.columns([1, 2])
        with col_stats:
            st.markdown(
                f'<span class="stat-pill">✅ {filled}/{total} champs remplis</span>'
                f'<span class="stat-pill">📈 {pct}% de complétude</span>',
                unsafe_allow_html=True,
            )
            if pct < 30:
                st.markdown(
                    '<div class="warn-box">⚠️ Moins de 30% des champs sont remplis. '
                    "Le document ne contient peut-être pas assez de données UCAR.</div>",
                    unsafe_allow_html=True,
                )

        # Metadata quick-edit (institution & year are critical)
        with col_edit:
            meta = data.get("metadata", {})
            new_inst = st.text_input(
                "Institution (requis)",
                value=meta.get("institution") or "",
                key="edit_institution",
                placeholder="Ex : ENIT, IPEIT, ESSECT…",
            )
            new_year = st.text_input(
                "Année (requis)",
                value=str(meta.get("year") or ""),
                key="edit_year",
                placeholder="Ex : 2024",
            )
            if new_inst:
                data["metadata"]["institution"] = new_inst
            if new_year:
                data["metadata"]["year"] = new_year

        # Friendly preview
        tab_friendly, tab_raw = st.tabs(["📋 Vue structurée", "{ } JSON brut"])
        with tab_friendly:
            _render_json_preview(data)
        with tab_raw:
            st.markdown(
                f'<div class="json-preview">{json.dumps(data, ensure_ascii=False, indent=2)}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        col_confirm, col_back = st.columns([1, 4])

        with col_confirm:
            confirm = st.button("💾 Enregistrer dans Supabase", type="primary", use_container_width=True)
        with col_back:
            if st.button("↩ Recommencer", use_container_width=False):
                for k in ["upload_step", "upload_text", "upload_json", "upload_error", "upload_inserted"]:
                    st.session_state[k] = 0 if k == "upload_step" else "" if k in ("upload_text", "upload_error") else None if k == "upload_json" else False
                st.rerun()

        if confirm:
            if not data.get("metadata", {}).get("institution"):
                st.error("❌ Le champ **Institution** est obligatoire avant d'enregistrer.")
            else:
                with st.spinner("📡 Envoi vers Supabase…"):
                    try:
                        result = insert_data(data)
                        if result is None:
                            raise ValueError("insert_data() a retourné None — vérifiez les logs.")
                    except Exception as e:
                        st.session_state.upload_error = f"Erreur Supabase : {e}"
                        st.session_state.upload_step = 1
                        st.rerun()

                st.session_state.upload_inserted = True
                st.session_state.upload_step = 4
                st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 4 — Success
    # ═══════════════════════════════════════════════════════════════════════════
    elif step == 4:
        data = st.session_state.upload_json or {}
        inst = data.get("metadata", {}).get("institution", "Inconnu")
        year = data.get("metadata", {}).get("year", "")
        filled, total = _count_filled(data)

        st.markdown(f"""
        <div class="success-box">
            <div style="font-size:1.6rem; margin-bottom:8px;">✅ Données enregistrées avec succès !</div>
            <div><strong>Institution :</strong> {inst}</div>
            <div><strong>Année :</strong> {year}</div>
            <div><strong>Champs importés :</strong> {filled}/{total}</div>
            <div style="margin-top:10px; font-size:0.8rem; opacity:0.7;">
                Le dashboard se mettra à jour automatiquement lors du prochain chargement.
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_new, col_dash = st.columns(2)
        with col_new:
            if st.button("📥 Importer un autre fichier", type="primary", use_container_width=True):
                for k in ["upload_step", "upload_text", "upload_json", "upload_error", "upload_inserted"]:
                    st.session_state[k] = 0 if k == "upload_step" else "" if k in ("upload_text", "upload_error") else None if k == "upload_json" else False
                st.rerun()
        with col_dash:
            if st.button("🏢 Voir le dashboard", use_container_width=True):
                st.session_state.current_page = "overview"
                st.rerun()