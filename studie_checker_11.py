import streamlit as st

# ─────────────────────────────────────────────
# CHA2DS2-VA SCORE BEREKENING
# C  Congestive HF          +1
# H  Hypertension            +1
# A2 Age ≥ 75               +2
# D  Diabetes                +1
# S2 Stroke/TIA             +2
# V  Vascular disease        +1
# A  Age 65–74              +1
# ─────────────────────────────────────────────

def bereken_cha2ds2va(p):
    score = 0
    if p["hartfalen_opname"]:           score += 1
    if p["systolisch"] >= 130:          score += 1  # hypertensie
    if p["leeftijd"] >= 75:             score += 2
    elif p["leeftijd"] >= 65:           score += 1
    if p["dmii"]:                       score += 1
    if p["infarct_tia_vaatlijden"]:     score += 2  # stroke/TIA/vaatlijden
    return score


# ─────────────────────────────────────────────
# STUDIE LOGICA
# ─────────────────────────────────────────────

def check_attain_outcomes(p):
    redenen = []
    if p["leeftijd"] < 50:
        redenen.append("Leeftijd < 50 jaar")
    if p["bmi"] < 25:
        redenen.append("BMI < 25 kg/m²")
    if not p["infarct_tia_vaatlijden"]:
        redenen.append("Geen infarct/TIA/vaatlijden (ASCVD/CKD vereist)")
    if p["dmii"] and p["hba1c"] > 10.0:
        redenen.append("DM II met HbA1c > 10% (exclusie)")
    if p["egfr"] < 20:
        redenen.append("eGFR < 20 ml/min/1.73m² (exclusie)")
    if p["glp1_recent"]:
        redenen.append("GLP-1 RA / amylin analoog < 90 dagen geleden (exclusie)")
    return len(redenen) == 0, redenen


def check_baxduo(p):
    redenen = []
    if p["leeftijd"] < 40:
        redenen.append("Leeftijd < 40 jaar")
    if not p["dmii"]:
        redenen.append("Geen type 2 diabetes mellitus")
    if not p["infarct_tia_vaatlijden"]:
        redenen.append("Geen CV disease (CAD/CVD/PAD)")
    if p["systolisch"] < 130:
        redenen.append("Systolische bloeddruk < 130 mmHg (vereist ≥ 130 mmHg)")
    risicofactor = (
        p["leeftijd"] >= 70 or
        p["egfr"] < 60 or
        p["ntprobnp"] > 125 or
        p["af_type"] != "Geen"
    )
    if not risicofactor:
        redenen.append("Geen aanvullende risicofactor (≥70jr / eGFR<60 / NT-proBNP>125 / AF)")
    if p["hartfalen_opname"]:
        redenen.append("Opgenomen met hartfalen (exclusiecriterium)")
    if p["egfr"] < 30:
        redenen.append("eGFR < 30 ml/min/1.73m² (exclusie)")
    return len(redenen) == 0, redenen


def check_polaris(p):
    redenen = []
    if p["leeftijd"] < 40:
        redenen.append("Leeftijd < 40 jaar")
    if p["bmi"] < 27:
        redenen.append("BMI < 27 kg/m²")
    if not p["hartfalen_opname"]:
        redenen.append("Geen opname voor hartfalen in afgelopen jaar")
    if p["egfr"] < 15:
        redenen.append("eGFR < 15 ml/min/1.73m² (exclusie)")
    heeft_af = p["af_type"] != "Geen"
    bnp_drempel = (600 if heeft_af else 300) if p["bmi"] < 35 else (400 if heeft_af else 200)
    if p["ntprobnp"] < bnp_drempel:
        redenen.append(
            f"NT-proBNP < {bnp_drempel} pg/mL "
            f"(BMI {'≥' if p['bmi'] >= 35 else '<'}35, {'met' if heeft_af else 'zonder'} AF)"
        )
    if p["dmii"] and p["hba1c"] > 10.0:
        redenen.append("DM II met HbA1c > 10% (exclusie)")
    if p["glp1_recent"]:
        redenen.append("GLP-1 RA / GIP RA / amylin analoog < 90 dagen geleden (exclusie)")
    return len(redenen) == 0, redenen


def check_roxi_everest(p):
    redenen = []
    if p["af_type"] == "Geen":
        redenen.append("Geen atriumfibrilleren of flutter (vereist)")
        return False, redenen

    score = p["cha2ds2va_score"]

    if score < 2:
        redenen.append(f"CHA2DS2-VA score {score} — minimaal 2 vereist")
    elif score == 2:
        # Bij score = 2: OAC-naïef OF minimaal één aanvullende risicofactor
        aanvullend = (
            p["oac_naief"] or
            p["leeftijd"] >= 80 or
            p["egfr"] < 50 or
            p["ernstige_bloeding_vg"] or
            p["antiplatelet"] or
            p["gewicht_onder_60kg"] or
            p["stroke_tia_embolie_vg"]
        )
        if not aanvullend:
            redenen.append(
                "Score 2: vereist OAC-naïef OF ≥1 risicofactor "
                "(≥80jr / eGFR<50 / ernstige bloeding / antiplatelet / ≤60kg / stroke-TIA-embolie)"
            )
    # score ≥ 3: direct geschikt, geen extra voorwaarden

    if p["egfr"] < 15:
        redenen.append("eGFR < 15 mL/min/1.73m² (exclusie)")
    if p["systolisch"] > 180:
        redenen.append("Systolische bloeddruk > 180 mmHg (exclusie)")
    return len(redenen) == 0, redenen
    return len(redenen) == 0, redenen


def check_ambience(p):
    redenen = []
    if p["leeftijd"] < 45:
        redenen.append("Leeftijd < 45 jaar")
    if p["bmi"] < 27:
        redenen.append("BMI < 27 kg/m²")
    if not p["infarct_tia_vaatlijden"]:
        redenen.append("Geen ASCVD (MI, PAD of stroke)")
    risico_ok = (
        p["hartfalen_opname"] or
        p["egfr"] < 60 or
        p["uacr"] > 30 or
        p["af_type"] != "Geen"
    )
    if not risico_ok:
        redenen.append("Geen aanvullend risicocriterium (HF-opname / eGFR<60 / UACR>30 / AF)")
    if p["t1dm"]:
        redenen.append("Diabetes mellitus type I (exclusie)")
    if p["glp1_recent"]:
        redenen.append("GLP-1 RA / GIP RA / amylin analoog < 3 maanden geleden (exclusie)")
    if p["egfr"] < 15:
        redenen.append("eGFR < 15 mL/min/1.73m² of dialyse (exclusie)")
    return len(redenen) == 0, redenen


STUDIES = {
    "ATTAIN-OUTCOMES": {
        "omschrijving": "Orforglipron (oraal GLP-1 RA) bij obesitas + ASCVD/CKD vs placebo · Eli Lilly",
        "check": check_attain_outcomes,
    },
    "BaxDuo Prevent HF": {
        "omschrijving": "Baxdrostat + dapagliflozin bij T2DM + CV disease ter preventie van hartfalen · AstraZeneca",
        "check": check_baxduo,
    },
    "POLARIS NN9490-8266": {
        "omschrijving": "GLP-1/GIP RA bij stabiel hartfalen met verlaagde EF en obesitas · Novo Nordisk",
        "check": check_polaris,
    },
    "ROXI-EVEREST": {
        "omschrijving": "REGN7508 (factor XI remmer) bij atriumfibrilleren · Regeneron",
        "check": check_roxi_everest,
    },
    "AMBIENCE": {
        "omschrijving": "GLP-1/GIP RA bij ASCVD + obesitas en verhoogd cardiometabool risico",
        "check": check_ambience,
    },
}

# ─────────────────────────────────────────────
# PAGINA OPMAAK
# ─────────────────────────────────────────────

st.set_page_config(page_title="Klinische Studie Checker", page_icon="🏥", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; color: #e8edf2; }
    .stApp { background-color: #0f1923; }
    label, .stCheckbox label p, .stRadio label p,
    .stNumberInput label, .stRadio > label,
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] { color: #e8edf2 !important; }
    input[type="number"] {
        background-color: #1e2d3d !important;
        color: #e8edf2 !important;
        border: 1px solid #2e4560 !important;
        border-radius: 6px !important;
    }
    .header-bar {
        background: linear-gradient(135deg, #0a2540 0%, #1a4080 100%);
        color: #e8edf2; padding: 1.4rem 2rem; border-radius: 10px; margin-bottom: 1.8rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.4);
    }
    .header-bar h1 { margin: 0; font-size: 1.5rem; font-weight: 600; color: #ffffff; }
    .header-bar p  { margin: 0.3rem 0 0 0; font-size: 0.88rem; color: #a8c4e0; }
    .invoer-card {
        background: #162233; border-radius: 10px; padding: 1.4rem 1.6rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3); border: 1px solid #1e3550;
    }
    .score-box {
        background: #0d1e2e; border: 1px solid #2e4560; border-radius: 8px;
        padding: 0.7rem 1rem; margin-top: 0.6rem; margin-bottom: 0.2rem;
    }
    .score-box .score-label { font-size: 0.72rem; color: #5a8ab0; text-transform: uppercase; letter-spacing: 0.1em; }
    .score-box .score-value { font-size: 1.6rem; font-weight: 600; color: #e8edf2; line-height: 1.2; }
    .score-box .score-sub   { font-size: 0.75rem; color: #7a9bbf; margin-top: 0.1rem; }
    .studie-card {
        border-radius: 10px; padding: 1rem 1.3rem; margin-bottom: 0.9rem;
        border-left: 5px solid; box-shadow: 0 1px 4px rgba(0,0,0,0.3);
    }
    .studie-ja  { background: #0d2e1a; border-color: #1db870; }
    .studie-nee { background: #2a0f0f; border-color: #e03c3c; }
    .studie-naam { font-weight: 600; font-size: 0.97rem; color: #e8edf2; }
    .studie-omschrijving { font-size: 0.8rem; color: #7a9bbf; margin-top: 0.2rem; }
    .badge-ja  { background:#1db870; color:#fff; padding:3px 11px; border-radius:20px; font-size:0.75rem; font-weight:600; white-space:nowrap; }
    .badge-nee { background:#e03c3c; color:#fff; padding:3px 11px; border-radius:20px; font-size:0.75rem; font-weight:600; white-space:nowrap; }
    .reden-item { font-size: 0.79rem; color: #f08080; margin-top: 0.15rem; padding-left: 0.3rem; }
    .sectie-label {
        font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.12em;
        color: #5a8ab0; font-weight: 600; margin-top: 1.1rem; margin-bottom: 0.1rem;
    }
    hr.sectie-hr { border: none; border-top: 1px solid #1e3550; margin: 0.8rem 0 0.4rem 0; }
    .stAlert { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-bar">
    <h1>🏥 Klinische Studie Checker</h1>
    <p>Vul de patiëntparameters in — de app geeft direct aan voor welke studies de patiënt in aanmerking komt</p>
</div>
""", unsafe_allow_html=True)

col_links, col_resultaten = st.columns([1, 1.35], gap="large")

# ─────────────────────────────────────────────
# INVOER
# ─────────────────────────────────────────────
with col_links:
    st.markdown('<div class="invoer-card">', unsafe_allow_html=True)
    st.markdown("#### 📋 Patiëntparameters")

    st.markdown('<div class="sectie-label">Algemeen</div>', unsafe_allow_html=True)
    leeftijd = st.number_input("Leeftijd (jaren)", 18, 110, 65, 1)
    bmi      = st.number_input("BMI (kg/m²)", 15.0, 65.0, 30.0, 0.1, format="%.1f")

    st.markdown('<hr class="sectie-hr"><div class="sectie-label">Laboratorium</div>', unsafe_allow_html=True)
    egfr     = st.number_input("eGFR (ml/min/1.73m²)", 0, 150, 65, 1)
    uacr     = st.number_input("UACR (mg/g)", 0, 10000, 20, 1)
    ntprobnp = st.number_input("NT-proBNP (pg/mL)", 0, 50000, 150, 10)
    hba1c    = st.number_input("HbA1c (%) — alleen bij DM II", 4.0, 20.0, 7.0, 0.1, format="%.1f")
    systolisch = st.number_input("Systolische bloeddruk (mmHg)", 60, 260, 135, 1)

    st.markdown('<hr class="sectie-hr"><div class="sectie-label">Diagnoses & voorgeschiedenis</div>', unsafe_allow_html=True)
    dmii                  = st.checkbox("Diabetes mellitus type II")
    t1dm                  = st.checkbox("Diabetes mellitus type I")
    infarct_tia_vaatlijden = st.checkbox("Infarct / TIA / vaatlijden (CAD, CVD of PAD)")
    hartfalen_opname      = st.checkbox("Opgenomen met hartfalen in het afgelopen jaar")
    glp1_recent           = st.checkbox("GLP-1 RA / GIP RA / amylin analoog < 3 maanden geleden")

    st.markdown('<hr class="sectie-hr"><div class="sectie-label">Atriumfibrilleren</div>', unsafe_allow_html=True)
    af_type = st.radio(
        "Atriumfibrilleren / flutter",
        options=["Geen", "Paroxysmale atriumflutter", "Permanent"],
        index=0,
        horizontal=False,
    )

    # CHA2DS2-VA score live berekenen en tonen
    _p_score = dict(
        leeftijd=leeftijd, systolisch=systolisch, dmii=dmii,
        hartfalen_opname=hartfalen_opname, infarct_tia_vaatlijden=infarct_tia_vaatlijden,
    )
    cha2ds2va = bereken_cha2ds2va(_p_score)

    score_kleur = "#1db870" if cha2ds2va >= 2 else "#f0a030"
    st.markdown(f"""
    <div class="score-box">
        <div class="score-label">CHA2DS2-VA score (automatisch berekend)</div>
        <div class="score-value" style="color:{score_kleur}">{cha2ds2va}</div>
        <div class="score-sub">
            {"Hartfalen +1 · " if hartfalen_opname else ""}{"Hypertensie +1 · " if systolisch >= 130 else ""}{"Leeftijd ≥75 +2 · " if leeftijd >= 75 else ("Leeftijd 65–74 +1 · " if leeftijd >= 65 else "")}{"DM +1 · " if dmii else ""}{"Vaatlijden/stroke +2" if infarct_tia_vaatlijden else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Extra velden bij score = 2 en AF aanwezig
    if af_type != "Geen" and cha2ds2va == 2:
        st.markdown('<hr class="sectie-hr"><div class="sectie-label">ROXI-EVEREST — aanvullende criteria (score = 2)</div>', unsafe_allow_html=True)
        oac_naief            = st.checkbox("OAC-naïef (nooit anticoagulantia gebruikt)")
        ernstige_bloeding_vg = st.checkbox("Eerdere (niet-traumatische) ernstige bloeding")
        antiplatelet         = st.checkbox("Huidig of gepland mono-/duo-antiplateletgebruik")
        gewicht_onder_60kg   = st.checkbox("Gewicht ≤ 60 kg")
        stroke_tia_embolie_vg = st.checkbox("Eerdere ischemische stroke, TIA of systemische embolie")
    else:
        oac_naief = ernstige_bloeding_vg = antiplatelet = gewicht_onder_60kg = stroke_tia_embolie_vg = False

    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PATIENT DICT
# ─────────────────────────────────────────────
patient = dict(
    leeftijd=leeftijd,
    bmi=bmi,
    egfr=egfr,
    uacr=uacr,
    ntprobnp=ntprobnp,
    hba1c=hba1c,
    systolisch=systolisch,
    dmii=dmii,
    t1dm=t1dm,
    infarct_tia_vaatlijden=infarct_tia_vaatlijden,
    hypertensie_130=systolisch >= 130,
    hartfalen_opname=hartfalen_opname,
    glp1_recent=glp1_recent,
    af_type=af_type,
    cha2ds2va_score=cha2ds2va,
    oac_naief=oac_naief,
    ernstige_bloeding_vg=ernstige_bloeding_vg,
    antiplatelet=antiplatelet,
    gewicht_onder_60kg=gewicht_onder_60kg,
    stroke_tia_embolie_vg=stroke_tia_embolie_vg,
)

# ─────────────────────────────────────────────
# RESULTATEN
# ─────────────────────────────────────────────
with col_resultaten:
    st.markdown("#### 🔍 Resultaten per studie")
    geschikt_count = 0

    for naam, studie in STUDIES.items():
        in_aanmerking, redenen = studie["check"](patient)

        if in_aanmerking:
            geschikt_count += 1
            st.markdown(f"""
            <div class="studie-card studie-ja">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem">
                    <div>
                        <div class="studie-naam">{naam}</div>
                        <div class="studie-omschrijving">{studie['omschrijving']}</div>
                    </div>
                    <span class="badge-ja">✓ In aanmerking</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            redenen_html = "".join([f'<div class="reden-item">· {r}</div>' for r in redenen])
            st.markdown(f"""
            <div class="studie-card studie-nee">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem">
                    <div>
                        <div class="studie-naam">{naam}</div>
                        <div class="studie-omschrijving">{studie['omschrijving']}</div>
                    </div>
                    <span class="badge-nee">✗ Niet geschikt</span>
                </div>
                <div style="margin-top:0.5rem">{redenen_html}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if geschikt_count == 0:
        st.info("⬅️ Deze patiënt komt momenteel voor geen enkele studie in aanmerking.")
    elif geschikt_count == 1:
        st.success("✅ Patiënt komt in aanmerking voor **1 studie**.")
    else:
        st.success(f"✅ Patiënt komt in aanmerking voor **{geschikt_count} studies**.")

    st.markdown("""
    <div style="font-size:0.72rem;color:#4a7a9b;margin-top:1.5rem;line-height:1.5">
    ⚠️ Dit is een screeningshulpmiddel op basis van samengevatte criteria.<br>
    Raadpleeg altijd het volledige studieprotocol voor definitieve eligibiliteitsbeoordeling.
    </div>
    """, unsafe_allow_html=True)
