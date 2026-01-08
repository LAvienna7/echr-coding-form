import json
import os
import re
from datetime import datetime
from typing import Dict, Any, List

import pandas as pd
import streamlit as st

# ------------------------------------------------------------
# ECHR ARTICLE 8 - CODING FORM
# Saves one JSON per case (or per Sub-Unit A/B/C)
# Exports a flat CSV for analysis.
# ------------------------------------------------------------

DATA_DIR = "case_forms"
os.makedirs(DATA_DIR, exist_ok=True)

# Edit this list to match your final dataset.
DEFAULT_CASES = [
    {"Case_ID": "Malone v. United Kingdom", "App_No": "8691/79", "Year": 1984, "Chamber": "CH"},
    {"Case_ID": "Huvig v. France", "App_No": "11105/84", "Year": 1990, "Chamber": "CH"},
    {"Case_ID": "Kruslin v. France", "App_No": "11801/85", "Year": 1990, "Chamber": "CH"},
    {"Case_ID": "Halford v. United Kingdom", "App_No": "20605/92", "Year": 1997, "Chamber": "CH"},
    {"Case_ID": "Amann v. Switzerland", "App_No": "27798/95", "Year": 2000, "Chamber": "GC"},
    {"Case_ID": "P.G. and J.H. v. United Kingdom", "App_No": "44787/98", "Year": 2001, "Chamber": "CH"},
    {"Case_ID": "Copland v. United Kingdom", "App_No": "62617/00", "Year": 2007, "Chamber": "CH"},
    {"Case_ID": "Liberty and Others v. United Kingdom", "App_No": "58243/00", "Year": 2008, "Chamber": "CH"},
    {"Case_ID": "Kennedy v. the United Kingdom", "App_No": "26839/05", "Year": 2010, "Chamber": "CH"},
    {"Case_ID": "Uzun v. Germany", "App_No": "35623/05", "Year": 2010, "Chamber": "CH"},
    {"Case_ID": "Dragojević v. Croatia", "App_No": "68955/11", "Year": 2015, "Chamber": "CH"},
    {"Case_ID": "Roman Zakharov v. Russia", "App_No": "47143/06", "Year": 2015, "Chamber": "GC"},
    {"Case_ID": "Szabó and Vissy v. Hungary", "App_No": "37138/14", "Year": 2016, "Chamber": "CH"},
    {"Case_ID": "Libert v. France", "App_No": "588/13", "Year": 2018, "Chamber": "CH"},
    {"Case_ID": "Breyer v. Germany", "App_No": "50001/12", "Year": 2020, "Chamber": "CH"},
    {"Case_ID": "Big Brother Watch and Others v. United Kingdom", "App_No": "58170/13, 62322/14, 24960/15", "Year": 2021, "Chamber": "GC"},
    {"Case_ID": "Centrum för Rättvisa v. Sweden", "App_No": "35252/08", "Year": 2021, "Chamber": "GC"},
    {"Case_ID": "Ekimdzhiev and Others v. Bulgaria", "App_No": "70078/12", "Year": 2022, "Chamber": "CH"},
    {"Case_ID": "Pietrzak and Bychawska-Siniarska and Others v. Poland", "App_No": "72038/17 & 25237/18", "Year": 2024, "Chamber": "CH"},
    {"Case_ID": "Macharik v. Czech Republic", "App_No": "51409/19", "Year": 2025, "Chamber": "CH"},
    {"Case_ID": "Klass and Others v. Germany", "App_No": "5029/71", "Year": 1978, "Chamber": "CH"},
]

OUTCOME_OPTIONS = ["V", "NV", "P"]  # Violation / No violation / Partial
YESNO_OPTIONS = ["YES", "NO", "PART", "UNK"]

INTERFERENCE_TYPES = {
    "TI": "targeted interception (content)",
    "CLD": "covert listening device",
    "BI": "bulk interception regime",
    "CDA": "communications data acquisition (metadata)",
    "RET": "retention or retention plus access regime",
    "FILE": "intelligence file / public authority data storage",
    "GPS": "location tracking",
}

REVIEW_POSTURE = {"IND": "individual measure review", "REG": "abstracto regime review"}
CONTEXT_TRIGGER = {"NS": "national security", "CP": "crime prevention", "OTH": "other"}
PRIMARY_DRIVER = {
    "LWF": "lawfulness / quality of law",
    "SG": "safeguards design (end-to-end)",
    "PROP": "proportionality / fair balance",
    "REM": "remedies / review deficit",
}

GT_CHECKS = [
    ("GT_Accessibility", "accessibility"),
    ("GT_Foreseeability", "foreseeability"),
    ("GT_ScopeClarity", "scope clarity"),
    ("GT_Authorisation", "authorisation"),
    ("GT_Oversight", "oversight"),
    ("GT_ExPostReview", "ex post review"),
    ("GT_Notification", "notification"),
    ("GT_RetentionDestruction", "retention and destruction"),
    ("GT_Remedies", "remedies"),
    ("GT_ProportionalityFairBalance", "proportionality / fair balance"),
]

FACTOR_SET = [
    "AUTH",
    "OVERS",
    "REVIEW",
    "NOTICE",
    "RETAIN",
    "DESTROY",
    "SELECTOR",
    "SHARING",
    "SCOPE",
    "FORESEE",
    "REMEDY",
    "PROP",
    "NA",
]


def safe_filename(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    keep = "".join(c for c in s if c.isalnum() or c in (" ", "-", "_"))
    return keep.replace(" ", "_")


def case_path(case_id: str, subunit_id: str) -> str:
    base = safe_filename(case_id)
    su = subunit_id if subunit_id else "NA"
    return os.path.join(DATA_DIR, f"{base}__{su}.json")


def load_case(case_id: str, subunit_id: str) -> Dict[str, Any]:
    p = case_path(case_id, subunit_id)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_case(payload: Dict[str, Any]) -> None:
    p = case_path(payload["Case_ID"], payload.get("SubUnit_ID", "NA"))
    payload["last_saved_utc"] = datetime.utcnow().isoformat()
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def list_saved() -> List[str]:
    return sorted([fn for fn in os.listdir(DATA_DIR) if fn.endswith(".json")])


def to_dataframe() -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for fn in list_saved():
        with open(os.path.join(DATA_DIR, fn), "r", encoding="utf-8") as f:
            rows.append(json.load(f))
    if not rows:
        return pd.DataFrame()
    return pd.json_normalize(rows)


def word_count(text: str) -> int:
    if not text:
        return 0
    return len([w for w in re.split(r"\s+", text.strip()) if w])


# ----------------------------
# UI
# ----------------------------
st.set_page_config(page_title="ECHR Art 8 - Coding Form", layout="wide")
st.title("ECHR Article 8 - Case Dossier Form")
st.caption("Interactive form. Saves one JSON per case (or per Sub-Unit A/B/C). Export CSV for analysis.")

# Initialise cases in session
if "cases" not in st.session_state:
    st.session_state["cases"] = DEFAULT_CASES

left, right = st.columns([1.05, 2.0], gap="large")

with left:
    st.subheader("Cases")

    # Add custom case
    with st.expander("Add a case to the list"):
        new_name = st.text_input("Case_ID (new)")
        new_app = st.text_input("App_No (new)")
        new_year = st.number_input("Year (new)", min_value=1900, max_value=2100, value=2021)
        new_chamber = st.selectbox("Chamber (new)", ["CH", "GC"], index=0)
        if st.button("Add case"):
            if new_name.strip():
                st.session_state["cases"].append({
                    "Case_ID": new_name.strip(),
                    "App_No": new_app.strip(),
                    "Year": int(new_year),
                    "Chamber": new_chamber,
                })
                st.success("Added.")
            else:
                st.warning("Please provide a Case_ID.")

    case_labels = [f'{c["Case_ID"]} ({c["Year"]})' for c in st.session_state["cases"]]
    idx = st.selectbox("Select case", list(range(len(st.session_state["cases"]))), format_func=lambda i: case_labels[i])
    base_case = st.session_state["cases"][idx]

    st.caption("If multi-regime, code each regime as Sub-Unit A/B/C.")
    subunit = st.selectbox("SubUnit_ID", ["NA", "A", "B", "C"], index=0)

    existing = load_case(base_case["Case_ID"], subunit)
    st.write("Saved file:", case_path(base_case["Case_ID"], subunit))

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Load saved"):
            st.session_state["loaded_payload"] = existing
            st.success("Loaded saved JSON into the form.")
    with c2:
        if st.button("Clear loaded"):
            st.session_state.pop("loaded_payload", None)
            st.success("Cleared.")

    st.divider()
    st.subheader("Export")
    df = to_dataframe()
    st.write(f"Saved dossiers: {len(df)}")

    if st.button("Prepare CSV export"):
        if df.empty:
            st.warning("No saved dossiers yet.")
        else:
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV",
                data=csv_bytes,
                file_name="echr_coding_export.csv",
                mime="text/csv",
            )

    if st.button("Prepare JSONL export"):
        if df.empty:
            st.warning("No saved dossiers yet.")
        else:
            rows = df.to_dict(orient="records")
            jsonl = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows).encode("utf-8")
            st.download_button(
                "Download JSONL",
                data=jsonl,
                file_name="echr_coding_export.jsonl",
                mime="application/jsonl",
            )

    with st.expander("Show saved files"):
        st.write(list_saved())

with right:
    st.subheader("Case dossier form")

    loaded = st.session_state.get("loaded_payload", existing) or {}

    # ----------------------------
    # Header
    # ----------------------------
    st.markdown("### 1) Case ID and outcome label")
    col1, col2, col3 = st.columns(3)
    with col1:
        case_id = st.text_input("Case_ID", value=loaded.get("Case_ID", base_case["Case_ID"]))
        app_no = st.text_input("App_No", value=loaded.get("App_No", base_case["App_No"]))
    with col2:
        year = st.number_input("Year", min_value=1900, max_value=2100, value=int(loaded.get("Year", base_case["Year"])))
        chamber = st.selectbox("Chamber", ["CH", "GC"], index=["CH", "GC"].index(loaded.get("Chamber", base_case["Chamber"])))
    with col3:
        merits = st.selectbox("Merits_Judgment", [1], index=0)
        multi = st.selectbox("MultiRegime", [0, 1], index=[0, 1].index(int(loaded.get("MultiRegime", 0))))

    st.markdown("### 2) Outcome")
    col1, col2, col3 = st.columns(3)
    with col1:
        art8_outcome = st.selectbox("Art8_Outcome", OUTCOME_OPTIONS, index=OUTCOME_OPTIONS.index(loaded.get("Art8_Outcome", "V")))
    with col2:
        auto_any = 1 if art8_outcome in ["V", "P"] else 0
        any_violation = st.selectbox(
            "Art8_BinaryAnyViolation",
            [0, 1],
            index=[0, 1].index(int(loaded.get("Art8_BinaryAnyViolation", auto_any))),
        )
    with col3:
        subunit_id = st.selectbox("SubUnit_ID (stored)", ["NA", "A", "B", "C"], index=["NA", "A", "B", "C"].index(loaded.get("SubUnit_ID", subunit)))

    if multi == 1 and subunit_id == "NA":
        st.warning("MultiRegime=1 but SubUnit_ID=NA. Prefer splitting into A/B/C.")

    st.divider()

    # ----------------------------
    # Comparability anchor
    # ----------------------------
    st.markdown("### 3) Comparability anchor - Interference profile")
    c1, c2, c3 = st.columns(3)
    with c1:
        it_primary = st.selectbox(
            "InterferenceType_Primary",
            list(INTERFERENCE_TYPES.keys()),
            format_func=lambda k: f"{k} - {INTERFERENCE_TYPES[k]}",
            index=list(INTERFERENCE_TYPES.keys()).index(loaded.get("InterferenceType_Primary", "TI")),
        )
    with c2:
        posture = st.selectbox(
            "ReviewPosture",
            list(REVIEW_POSTURE.keys()),
            format_func=lambda k: f"{k} - {REVIEW_POSTURE[k]}",
            index=list(REVIEW_POSTURE.keys()).index(loaded.get("ReviewPosture", "IND")),
        )
    with c3:
        trigger = st.selectbox(
            "ContextTrigger",
            list(CONTEXT_TRIGGER.keys()),
            format_func=lambda k: f"{k} - {CONTEXT_TRIGGER[k]}",
            index=list(CONTEXT_TRIGGER.keys()).index(loaded.get("ContextTrigger", "NS")),
        )

    st.divider()

    # ----------------------------
    # Article 8 pathway
    # ----------------------------
    st.markdown("### 4) Article 8 pathway - what the Court actually did")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        step_interf = st.selectbox("Step_Interference", [0, 1], index=[0, 1].index(int(loaded.get("Step_Interference", 1))))
    with c2:
        step_law = st.selectbox("Step_Lawfulness", [0, 1], index=[0, 1].index(int(loaded.get("Step_Lawfulness", 1))))
    with c3:
        step_aim = st.selectbox("Step_LegitimateAim", [0, 1], index=[0, 1].index(int(loaded.get("Step_LegitimateAim", 1))))
    with c4:
        step_nec = st.selectbox("Step_Necessity", [0, 1], index=[0, 1].index(int(loaded.get("Step_Necessity", 1))))

    c5, c6 = st.columns([1, 2])
    with c5:
        driver = st.selectbox(
            "PrimaryDriver",
            list(PRIMARY_DRIVER.keys()),
            format_func=lambda k: f"{k} - {PRIMARY_DRIVER[k]}",
            index=list(PRIMARY_DRIVER.keys()).index(loaded.get("PrimaryDriver", "SG")),
        )
    with c6:
        turning = st.text_input("TurningPoint_1Sentence (max 200 chars)", value=loaded.get("TurningPoint_1Sentence", ""))[:200]

    st.divider()

    # ----------------------------
    # Safeguards matrix
    # ----------------------------
    st.markdown("### 5) Safeguards matrix")
    st.caption("Code as YES/NO/PART/UNK. Use UNK if not addressed in the reasoning.")
    sg1, sg2, sg3, sg4 = st.columns(4)

    def pick(key: str, default: str = "UNK") -> str:
        return loaded.get(key, default)

    with sg1:
        IndepPriorAuth = st.selectbox("IndepPriorAuth", YESNO_OPTIONS, index=YESNO_OPTIONS.index(pick("IndepPriorAuth")))
        ExecOnlyAuth = st.selectbox("ExecOnlyAuth", YESNO_OPTIONS, index=YESNO_OPTIONS.index(pick("ExecOnlyAuth")))
        SelectorCategoriesConstrained = st.selectbox(
            "SelectorCategoriesConstrained (bulk)",
            YESNO_OPTIONS,
            index=YESNO_OPTIONS.index(pick("SelectorCategoriesConstrained")),
        )
    with sg2:
        PersonLinkedSelectorsPreAuth = st.selectbox(
            "PersonLinkedSelectorsPreAuth (bulk)",
            YESNO_OPTIONS,
            index=YESNO_OPTIONS.index(pick("PersonLinkedSelectorsPreAuth")),
        )
        IndepOversight = st.selectbox("IndepOversight", YESNO_OPTIONS, index=YESNO_OPTIONS.index(pick("IndepOversight")))
        ExPostReview = st.selectbox("ExPostReview", YESNO_OPTIONS, index=YESNO_OPTIONS.index(pick("ExPostReview")))
    with sg3:
        Notification = st.selectbox("Notification", YESNO_OPTIONS, index=YESNO_OPTIONS.index(pick("Notification")))
        RetentionLimits = st.selectbox("RetentionLimits", YESNO_OPTIONS, index=YESNO_OPTIONS.index(pick("RetentionLimits")))
        AccessLogging = st.selectbox("AccessLogging", YESNO_OPTIONS, index=YESNO_OPTIONS.index(pick("AccessLogging")))
    with sg4:
        DestructionRules = st.selectbox("DestructionRules", YESNO_OPTIONS, index=YESNO_OPTIONS.index(pick("DestructionRules")))
        SharingRules_ForeignPartners = st.selectbox(
            "SharingRules_ForeignPartners",
            YESNO_OPTIONS,
            index=YESNO_OPTIONS.index(pick("SharingRules_ForeignPartners")),
        )
        RemedyAccess = st.selectbox("RemedyAccess", YESNO_OPTIONS, index=YESNO_OPTIONS.index(pick("RemedyAccess")))

    RemedyEffectiveness = st.selectbox(
        "RemedyEffectiveness",
        ["EFF", "LIM", "NONE", "UNK"],
        index=["EFF", "LIM", "NONE", "UNK"].index(loaded.get("RemedyEffectiveness", "UNK")),
    )

    st.divider()

    # ----------------------------
    # Human ground truth checklist
    # ----------------------------
    st.markdown("### 6) Human ground truth checklist (explicitly addressed)")
    gt_cols = st.columns(5)
    gt_values: Dict[str, int] = {}
    for i, (key, label) in enumerate(GT_CHECKS):
        with gt_cols[i % 5]:
            gt_values[key] = 1 if st.checkbox(label, value=bool(loaded.get(key, 0))) else 0

    st.divider()

    # ----------------------------
    # Sensitivity flags
    # ----------------------------
    st.markdown("### 7) Sensitivity and outlier flags")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        Flag_Journalist = 1 if st.checkbox("Journalist material", value=bool(loaded.get("Flag_Journalist", 0))) else 0
    with f2:
        Flag_LawyerPrivilege = 1 if st.checkbox("Lawyer privilege", value=bool(loaded.get("Flag_LawyerPrivilege", 0))) else 0
    with f3:
        Flag_ThirdPartyCapture = 1 if st.checkbox("Third-party capture", value=bool(loaded.get("Flag_ThirdPartyCapture", 0))) else 0
    with f4:
        Flag_CrossArticleGravity = 1 if st.checkbox("Cross-Article gravity", value=bool(loaded.get("Flag_CrossArticleGravity", 0))) else 0

    st.divider()

    # ----------------------------
    # Human decisive factors
    # ----------------------------
    st.markdown("### 8) Human decisive factors (Top 3)")
    h1, h2, h3 = st.columns(3)
    with h1:
        Human_TopFactor1 = st.selectbox("Human_TopFactor1", FACTOR_SET, index=FACTOR_SET.index(loaded.get("Human_TopFactor1", "NA")))
    with h2:
        Human_TopFactor2 = st.selectbox("Human_TopFactor2", FACTOR_SET, index=FACTOR_SET.index(loaded.get("Human_TopFactor2", "NA")))
    with h3:
        Human_TopFactor3 = st.selectbox("Human_TopFactor3", FACTOR_SET, index=FACTOR_SET.index(loaded.get("Human_TopFactor3", "NA")))

    st.divider()

    # ----------------------------
    # AI facts block
    # ----------------------------
    st.markdown("### 9) Standardised facts block for AI simulation")
    ai_facts = st.text_area(
        "Facts block (120-180 words, fixed order)",
        value=loaded.get("AI_FactsBlock", ""),
        height=170,
    )

    wc = word_count(ai_facts)
    st.caption(f"Word count: {wc}. Target range: 120-180.")
    if wc and (wc < 100 or wc > 220):
        st.warning("Facts block is far from the target range. Consider tightening for comparability.")

    st.divider()

    # ----------------------------
    # Computed keys
    # ----------------------------
    cluster_core = f"{it_primary}_{posture}_{trigger}"
    st.markdown("### Computed clustering keys (preview)")
    st.code(f"ClusterKey_Core: {cluster_core}")

    # ----------------------------
    # Save payload
    # ----------------------------
    payload: Dict[str, Any] = {
        "Case_ID": case_id,
        "App_No": app_no,
        "Year": int(year),
        "Chamber": chamber,
        "Merits_Judgment": merits,
        "MultiRegime": int(multi),
        "SubUnit_ID": subunit_id,
        "Art8_Outcome": art8_outcome,
        "Art8_BinaryAnyViolation": int(any_violation),
        "InterferenceType_Primary": it_primary,
        "ReviewPosture": posture,
        "ContextTrigger": trigger,
        "Step_Interference": int(step_interf),
        "Step_Lawfulness": int(step_law),
        "Step_LegitimateAim": int(step_aim),
        "Step_Necessity": int(step_nec),
        "PrimaryDriver": driver,
        "TurningPoint_1Sentence": turning,
        "IndepPriorAuth": IndepPriorAuth,
        "ExecOnlyAuth": ExecOnlyAuth,
        "SelectorCategoriesConstrained": SelectorCategoriesConstrained,
        "PersonLinkedSelectorsPreAuth": PersonLinkedSelectorsPreAuth,
        "IndepOversight": IndepOversight,
        "ExPostReview": ExPostReview,
        "Notification": Notification,
        "RetentionLimits": RetentionLimits,
        "AccessLogging": AccessLogging,
        "DestructionRules": DestructionRules,
        "SharingRules_ForeignPartners": SharingRules_ForeignPartners,
        "RemedyAccess": RemedyAccess,
        "RemedyEffectiveness": RemedyEffectiveness,
        "Flag_Journalist": int(Flag_Journalist),
        "Flag_LawyerPrivilege": int(Flag_LawyerPrivilege),
        "Flag_ThirdPartyCapture": int(Flag_ThirdPartyCapture),
        "Flag_CrossArticleGravity": int(Flag_CrossArticleGravity),
        "Human_TopFactor1": Human_TopFactor1,
        "Human_TopFactor2": Human_TopFactor2,
        "Human_TopFactor3": Human_TopFactor3,
        "AI_FactsBlock": ai_facts,
        "ClusterKey_Core": cluster_core,
    }
    payload.update(gt_values)

    save_col1, save_col2 = st.columns([1, 1])
    with save_col1:
        if st.button("Save dossier"):
            save_case(payload)
            st.success("Saved JSON dossier.")
    with save_col2:
        if st.button("Save and clear loaded"):
            save_case(payload)
            st.session_state.pop("loaded_payload", None)
            st.success("Saved and cleared loaded state.")

    with st.expander("Show JSON payload"):
        st.json(payload)
