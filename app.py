
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

from pathlib import Path
from datetime import datetime

# ==========================================================
# QUANTA - INDUSTRIAL MACHINE INTELLIGENCE SYSTEM
# ==========================================================

st.set_page_config(
    page_title="QUANTA | Machine Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

MODEL_PATH = Path("industrial_machine_model.joblib")
DB_PATH = Path("machine_history.db")

FEATURES = [
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]"
]

# ==========================================================
# MODEL
# ==========================================================

@st.cache_resource
def load_model():
    if not MODEL_PATH.exists():
        st.error(
            "Model file not found. Keep industrial_machine_model.joblib "
            "in the same folder as app.py."
        )
        st.stop()

    return joblib.load(MODEL_PATH)


model = load_model()


# ==========================================================
# DATABASE
# ==========================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


def create_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                machine_type TEXT NOT NULL,
                air_temperature REAL,
                process_temperature REAL,
                rotational_speed REAL,
                torque REAL,
                tool_wear REAL,
                prediction INTEGER,
                failure_probability REAL
            )
        """)
        conn.commit()


def save_prediction(machine_id, values, prediction, probability):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO predictions (
                machine_id, timestamp, machine_type,
                air_temperature, process_temperature,
                rotational_speed, torque, tool_wear,
                prediction, failure_probability
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            machine_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            values["Type"],
            values["Air temperature [K]"],
            values["Process temperature [K]"],
            values["Rotational speed [rpm]"],
            values["Torque [Nm]"],
            values["Tool wear [min]"],
            int(prediction),
            float(probability)
        ))
        conn.commit()


def get_history():
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT * FROM predictions ORDER BY id DESC",
            conn
        )


create_database()


# ==========================================================
# THEME AND STYLING
# ==========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
    --bg: #080c14;
    --panel: rgba(19, 29, 44, 0.82);
    --panel2: rgba(27, 40, 59, 0.72);
    --border: rgba(160, 181, 207, 0.15);
    --white: #edf3fa;
    --muted: #91a0b5;
    --cyan: #65e5d3;
    --violet: #a78bfa;
    --amber: #f5bd68;
    --coral: #ff7e83;
}

.stApp {
    background:
        radial-gradient(ellipse at 78% 0%, rgba(56, 119, 151, .17), transparent 33%),
        radial-gradient(ellipse at 5% 55%, rgba(91, 70, 154, .12), transparent 35%),
        linear-gradient(145deg, #080c14, #0b1220 55%, #080d16);
    color: var(--white);
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3, h4 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--white) !important;
}

p, label, span {
    font-family: 'DM Sans', sans-serif;
}

.block-container {
    max-width: 1500px;
    padding-top: 2.1rem;
    padding-bottom: 4rem;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #101a29, #0a111c);
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] > div {
    padding-top: 1.5rem;
}

[data-testid="stSidebar"] p {
    color: var(--muted);
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(30, 46, 65, .85), rgba(14, 24, 38, .9));
    border: 1px solid var(--border);
    border-radius: 17px;
    padding: 18px 20px;
    min-height: 115px;
    box-shadow: 0 12px 30px rgba(0,0,0,.15);
}

[data-testid="stMetricLabel"] {
    color: var(--muted) !important;
}

[data-testid="stMetricValue"] {
    color: var(--white) !important;
    font-family: 'Space Grotesk', sans-serif;
}

[data-testid="stMetricDelta"] {
    color: var(--cyan) !important;
}

div.stButton > button,
div.stDownloadButton > button {
    border-radius: 11px;
    border: 1px solid rgba(101, 229, 211, .45);
    background: rgba(101, 229, 211, .12);
    color: #e5fffa;
    font-weight: 600;
    min-height: 43px;
    transition: all .2s ease;
}

div.stButton > button:hover,
div.stDownloadButton > button:hover {
    border-color: var(--cyan);
    background: rgba(101, 229, 211, .23);
    color: white;
    transform: translateY(-1px);
}

div[data-testid="stForm"] {
    background: rgba(17, 28, 43, .75);
    border: 1px solid var(--border);
    border-radius: 19px;
    padding: 20px;
}

input, textarea {
    color: var(--white) !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 14px;
}

hr {
    border-color: var(--border);
}

.eyebrow {
    color: var(--cyan);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.page-title {
    font-family: 'Space Grotesk', sans-serif;
    color: var(--white);
    font-size: clamp(34px, 4vw, 49px);
    font-weight: 700;
    letter-spacing: -1.5px;
    line-height: 1.1;
    margin-bottom: 10px;
}

.page-subtitle {
    color: var(--muted);
    font-size: 14px;
    margin-bottom: 26px;
}

.glass {
    background: linear-gradient(145deg, rgba(31, 47, 67, .83), rgba(13, 23, 37, .91));
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 23px;
    box-shadow: 0 16px 45px rgba(0,0,0,.20);
    backdrop-filter: blur(18px);
}

.glass-small {
    background: linear-gradient(145deg, rgba(29, 44, 63, .78), rgba(14, 24, 38, .92));
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 18px;
}

.card-label {
    color: var(--muted);
    font-size: 11px;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    font-weight: 600;
}

.card-value {
    color: var(--white);
    font-family: 'Space Grotesk', sans-serif;
    font-size: 30px;
    font-weight: 700;
    margin-top: 9px;
}

.card-note {
    color: var(--muted);
    font-size: 12px;
    margin-top: 4px;
}

.cyan {
    color: var(--cyan);
}

.violet {
    color: var(--violet);
}

.amber {
    color: var(--amber);
}

.coral {
    color: var(--coral);
}

.orbit {
    width: 205px;
    height: 205px;
    margin: 18px auto;
    border-radius: 50%;
    border: 1px solid rgba(101,229,211,.32);
    background:
        radial-gradient(circle, rgba(101,229,211,.18) 0%, rgba(101,229,211,.04) 43%, transparent 70%);
    box-shadow:
        0 0 45px rgba(101,229,211,.12),
        inset 0 0 40px rgba(101,229,211,.10);
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
}

.orbit:before, .orbit:after {
    content: "";
    position: absolute;
    width: 255px;
    height: 85px;
    border: 1px solid rgba(167,139,250,.42);
    border-radius: 50%;
    transform: rotate(-28deg);
}

.orbit:after {
    transform: rotate(52deg);
    border-color: rgba(101,229,211,.30);
}

.orbit-core {
    width: 95px;
    height: 95px;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 30%, #a5fff0, #2a9b91 48%, #102d40);
    box-shadow: 0 0 40px rgba(101,229,211,.4);
    display: flex;
    justify-content: center;
    align-items: center;
    color: #06131a;
    font-size: 30px;
    font-weight: 700;
    z-index: 2;
}

.result-normal {
    color: var(--cyan);
    font-size: 25px;
    font-weight: 700;
}

.result-failure {
    color: var(--coral);
    font-size: 23px;
    font-weight: 700;
}

.info-line {
    display: flex;
    justify-content: space-between;
    border-bottom: 1px solid var(--border);
    padding: 10px 0;
    color: var(--muted);
    font-size: 13px;
}

.info-line strong {
    color: var(--white);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(24, 37, 54, .75);
    border-radius: 10px;
    padding: 9px 18px;
}

.stTabs [aria-selected="true"] {
    border-bottom: 2px solid var(--cyan) !important;
}

</style>
""", unsafe_allow_html=True)


# ==========================================================
# PLOTLY THEME
# ==========================================================

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(
        color="#dce7f3",
        family="DM Sans"
    ),
    margin=dict(l=15, r=15, t=35, b=15),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color="#b7c5d6")
    ),
    xaxis=dict(
        gridcolor="rgba(150,170,195,.10)",
        zerolinecolor="rgba(150,170,195,.12)"
    ),
    yaxis=dict(
        gridcolor="rgba(150,170,195,.10)",
        zerolinecolor="rgba(150,170,195,.12)"
    )
)


def style_chart(fig, height=330):
    fig.update_layout(**PLOT_LAYOUT, height=height)
    return fig


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def get_prediction(values):
    input_df = pd.DataFrame([values], columns=FEATURES)

    prediction = int(model.predict(input_df)[0])

    probability = 0.0

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(input_df)[0]
        classes = list(model.classes_)

        if 1 in classes:
            probability = float(probabilities[classes.index(1)])

    return prediction, probability


def get_summary(history):
    total = len(history)

    if total == 0:
        return 0, 0, 0, 0.0

    failures = int((history["prediction"] == 1).sum())
    normal = total - failures
    rate = failures / total * 100

    return total, normal, failures, rate


def page_heading(label, title, subtitle):
    st.markdown(
        f'<div class="eyebrow">{label}</div>'
        f'<div class="page-title">{title}</div>'
        f'<div class="page-subtitle">{subtitle}</div>',
        unsafe_allow_html=True
    )


def metric_card(label, value, note, color="cyan"):
    st.markdown(
        f"""
        <div class="glass-small">
            <div class="card-label">{label}</div>
            <div class="card-value {color}">{value}</div>
            <div class="card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def status_label(value):
    return "Failure" if int(value) == 1 else "Normal"


# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:

    st.markdown("""
    <div style="padding:8px 5px 18px 5px;">
        <div style="font-size:33px;font-family:'Space Grotesk';
                    font-weight:700;letter-spacing:3px;color:#65e5d3;">
            QUANTA
        </div>
        <div style="font-size:9px;letter-spacing:2px;color:#91a0b5;">
            INDUSTRIAL INTELLIGENCE
        </div>
        <div style="font-size:11px;color:#64758a;margin-top:7px;">
            QUANTUM-INSPIRED SYSTEMS
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown(
        '<div class="eyebrow">NAVIGATION</div>',
        unsafe_allow_html=True
    )

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Machine Assessment",
            "Prediction History",
            "Analytics",
            "About System"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown(
        '<div class="eyebrow">SYSTEM MONITOR</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="glass-small">
        <div style="color:#65e5d3;font-size:13px;font-weight:700;">
            ● MODEL ONLINE
        </div>
        <div style="color:#91a0b5;font-size:11px;margin-top:7px;">
            Random Forest Classifier
        </div>
        <div style="color:#91a0b5;font-size:11px;">
            SQLite Database Connected
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    st.caption("QUANTA · VERSION 2.0")
    st.caption("Industrial Machine Health Intelligence")


# ==========================================================
# DATA
# ==========================================================

history = get_history()
total, normal, failures, failure_rate = get_summary(history)


# ==========================================================
# PAGE 1: OVERVIEW
# ==========================================================

if page == "Overview":

    page_heading(
        "QUANTUM-INSPIRED INDUSTRIAL MONITORING",
        "Intelligence in Motion.",
        "A predictive maintenance environment for understanding machine health and operational behaviour."
    )

    # Main spatial hero section

    left, right = st.columns([1.25, 0.85], gap="large")

    with left:
        st.markdown("""
        <div class="glass" style="min-height:350px;">
            <div class="eyebrow">THE QUANTA ENGINE</div>
            <div style="font-family:'Space Grotesk';font-size:31px;
                        font-weight:700;margin-top:12px;">
                Machine Health Intelligence
            </div>
            <div style="color:#91a0b5;font-size:13px;max-width:560px;
                        line-height:1.8;margin-top:10px;">
                Transform operational parameters into meaningful
                machine health predictions using a trained Random
                Forest classification model.
            </div>
            <div style="display:flex;gap:35px;flex-wrap:wrap;margin-top:30px;">
                <div>
                    <div class="card-value cyan">98.15%</div>
                    <div class="card-note">TEST ACCURACY</div>
                </div>
                <div>
                    <div class="card-value violet">97.02%</div>
                    <div class="card-note">ROC-AUC</div>
                </div>
                <div>
                    <div class="card-value amber">06</div>
                    <div class="card-note">INPUT FEATURES</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("""
        <div class="glass" style="text-align:center;min-height:350px;">
            <div class="eyebrow">QUANTUM-INSPIRED CORE</div>
            <div class="orbit">
                <div class="orbit-core">Q</div>
            </div>
            <div style="font-family:'Space Grotesk';font-size:20px;
                        font-weight:600;">QUANTA CORE</div>
            <div class="card-note">PREDICTIVE INTELLIGENCE ENGINE</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("### Operational Snapshot")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card("TOTAL ASSESSMENTS", total, "Recorded predictions", "cyan")

    with c2:
        metric_card("NORMAL", normal, "Normal predictions", "cyan")

    with c3:
        metric_card("FAILURE", failures, "Failure predictions", "coral")

    with c4:
        metric_card("FAILURE RATE", f"{failure_rate:.1f}%", "Of recorded assessments", "amber")

    st.markdown("")
    st.markdown("### Machine Intelligence Workspace")

    a, b, c = st.columns(3)

    with a:
        st.markdown("""
        <div class="glass-small" style="min-height:170px;">
            <div class="eyebrow">01 · EVALUATE</div>
            <h3>Machine Assessment</h3>
            <div class="card-note">
                Enter six machine parameters and generate a health prediction.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with b:
        st.markdown("""
        <div class="glass-small" style="min-height:170px;">
            <div class="eyebrow">02 · TRACK</div>
            <h3>Prediction History</h3>
            <div class="card-note">
                Explore saved assessments, search records and export data.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c:
        st.markdown("""
        <div class="glass-small" style="min-height:170px;">
            <div class="eyebrow">03 · ANALYSE</div>
            <h3>System Analytics</h3>
            <div class="card-note">
                Understand prediction distribution and sensor patterns.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("### Recent Activity")

    if history.empty:
        st.info("No assessments recorded yet. Visit Machine Assessment to begin.")
    else:
        recent = history.head(5).copy()
        recent["Status"] = recent["prediction"].apply(status_label)
        recent["Failure Probability"] = (
            recent["failure_probability"] * 100
        ).round(2).astype(str) + "%"

        st.dataframe(
            recent[[
                "machine_id",
                "timestamp",
                "machine_type",
                "Status",
                "Failure Probability"
            ]].rename(columns={
                "machine_id": "Machine ID",
                "timestamp": "Date & Time",
                "machine_type": "Type"
            }),
            use_container_width=True,
            hide_index=True
        )


# ==========================================================
# PAGE 2: MACHINE ASSESSMENT
# ==========================================================

elif page == "Machine Assessment":

    page_heading(
        "SENSOR INPUT AND MODEL INFERENCE",
        "Machine Assessment.",
        "Configure operational parameters and evaluate the predicted machine condition."
    )

    input_col, result_col = st.columns([1.15, 0.85], gap="large")

    with input_col:

        st.markdown("""
        <div class="eyebrow">INPUT CONFIGURATION</div>
        <h3>Operational Parameters</h3>
        <p style="color:#91a0b5;font-size:13px;">
            Enter the machine identity and sensor readings below.
        </p>
        """, unsafe_allow_html=True)

        with st.form("quanta_assessment"):

            machine_id = st.text_input(
                "Machine ID",
                value="MACHINE-001"
            )

            machine_type = st.selectbox(
                "Machine Type",
                ["L", "M", "H"],
                format_func=lambda x: {
                    "L": "L · Low",
                    "M": "M · Medium",
                    "H": "H · High"
                }[x]
            )

            st.markdown("#### Thermal readings")

            air_temp = st.number_input(
                "Air Temperature (K)",
                min_value=250.0,
                max_value=350.0,
                value=300.0,
                step=0.1
            )

            process_temp = st.number_input(
                "Process Temperature (K)",
                min_value=250.0,
                max_value=400.0,
                value=310.0,
                step=0.1
            )

            st.markdown("#### Mechanical readings")

            rotational_speed = st.number_input(
                "Rotational Speed (rpm)",
                min_value=500,
                max_value=3000,
                value=1500,
                step=10
            )

            torque = st.number_input(
                "Torque (Nm)",
                min_value=1.0,
                max_value=100.0,
                value=40.0,
                step=0.5
            )

            tool_wear = st.number_input(
                "Tool Wear (min)",
                min_value=0,
                max_value=300,
                value=100,
                step=1
            )

            submitted = st.form_submit_button(
                "RUN MACHINE ANALYSIS",
                use_container_width=True
            )

        if submitted:

            if not machine_id.strip():
                st.error("Please enter a Machine ID.")

            elif process_temp < air_temp:
                st.error("Process temperature should not be lower than air temperature.")

            else:
                values = {
                    "Type": machine_type,
                    "Air temperature [K]": air_temp,
                    "Process temperature [K]": process_temp,
                    "Rotational speed [rpm]": rotational_speed,
                    "Torque [Nm]": torque,
                    "Tool wear [min]": tool_wear
                }

                prediction, probability = get_prediction(values)

                save_prediction(
                    machine_id.strip(),
                    values,
                    prediction,
                    probability
                )

                st.session_state.latest_prediction = {
                    "machine_id": machine_id.strip(),
                    "prediction": prediction,
                    "probability": probability,
                    "values": values
                }

                st.success("Analysis completed. Prediction saved to database.")

    with result_col:

        st.markdown("""
        <div class="eyebrow">MODEL INFERENCE</div>
        <h3>Assessment Output</h3>
        """, unsafe_allow_html=True)

        latest = st.session_state.get("latest_prediction")

        if latest is None:

            st.markdown("""
            <div class="glass" style="text-align:center;min-height:340px;">
                <div class="orbit">
                    <div class="orbit-core">Q</div>
                </div>
                <h3>Awaiting Input</h3>
                <p class="card-note">
                    Submit the sensor readings to generate a prediction.
                </p>
            </div>
            """, unsafe_allow_html=True)

        else:

            prediction = latest["prediction"]
            probability = latest["probability"]

            st.markdown('<div class="glass">', unsafe_allow_html=True)

            st.markdown(
                f'<div class="card-label">MACHINE · {latest["machine_id"]}</div>',
                unsafe_allow_html=True
            )

            if prediction == 1:
                st.markdown(
                    '<div class="result-failure">⚠ FAILURE RISK DETECTED</div>',
                    unsafe_allow_html=True
                )
                st.error("The model predicts a possible machine failure.")
            else:
                st.markdown(
                    '<div class="result-normal">✓ NORMAL CONDITION</div>',
                    unsafe_allow_html=True
                )
                st.success("The model predicts a normal machine condition.")

            st.markdown("#### Estimated Failure Probability")

            gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=probability * 100,
                number={
                    "suffix": "%",
                    "font": {"color": "#edf3fa", "size": 34}
                },
                gauge={
                    "axis": {
                        "range": [0, 100],
                        "tickcolor": "#91a0b5"
                    },
                    "bar": {"color": "#65e5d3"},
                    "bgcolor": "rgba(0,0,0,0)",
                    "borderwidth": 0,
                    "steps": [
                        {"range": [0, 30], "color": "rgba(101,229,211,.15)"},
                        {"range": [30, 70], "color": "rgba(245,189,104,.17)"},
                        {"range": [70, 100], "color": "rgba(255,126,131,.18)"}
                    ]
                }
            ))

            gauge.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#edf3fa",
                height=230,
                margin=dict(l=20, r=20, t=25, b=5)
            )

            st.plotly_chart(gauge, use_container_width=True)

            st.markdown(
                '<div class="info-line"><span>Machine Type</span>'
                f'<strong>{latest["values"]["Type"]}</strong></div>'
                '<div class="info-line"><span>Rotational Speed</span>'
                f'<strong>{latest["values"]["Rotational speed [rpm]"]} rpm</strong></div>'
                '<div class="info-line"><span>Tool Wear</span>'
                f'<strong>{latest["values"]["Tool wear [min]"]} min</strong></div>',
                unsafe_allow_html=True
            )

            st.caption(
                "Model score, not a calibrated real-world failure probability. "
                "This prediction does not replace professional inspection."
            )

            st.markdown('</div>', unsafe_allow_html=True)


# ==========================================================
# PAGE 3: PREDICTION HISTORY
# ==========================================================

elif page == "Prediction History":

    page_heading(
        "ASSESSMENT DATABASE",
        "Prediction History.",
        "Explore, filter and export previously recorded machine assessments."
    )

    total, normal, failures, rate = get_summary(history)

    c1, c2, c3 = st.columns(3)

    with c1:
        metric_card("TOTAL RECORDS", total, "Saved assessments", "cyan")

    with c2:
        metric_card("NORMAL RECORDS", normal, "Normal predictions", "cyan")

    with c3:
        metric_card("FAILURE RECORDS", failures, "Failure predictions", "coral")

    st.markdown("")
    st.markdown("### Record Explorer")

    if history.empty:

        st.info("No prediction records available. Complete a machine assessment first.")

    else:

        f1, f2 = st.columns(2)

        with f1:
            status_filter = st.selectbox(
                "Prediction status",
                ["All", "Normal", "Failure"]
            )

        with f2:
            machine_search = st.text_input(
                "Search Machine ID",
                placeholder="Search by machine ID"
            )

        filtered = history.copy()

        if status_filter == "Normal":
            filtered = filtered[filtered["prediction"] == 0]

        elif status_filter == "Failure":
            filtered = filtered[filtered["prediction"] == 1]

        if machine_search.strip():
            filtered = filtered[
                filtered["machine_id"].str.contains(
                    machine_search.strip(),
                    case=False,
                    na=False
                )
            ]

        filtered["Status"] = filtered["prediction"].apply(status_label)

        filtered["Failure Probability (%)"] = (
            filtered["failure_probability"] * 100
        ).round(2)

        display = filtered.rename(columns={
            "id": "Record ID",
            "machine_id": "Machine ID",
            "timestamp": "Date & Time",
            "machine_type": "Type",
            "air_temperature": "Air Temp (K)",
            "process_temperature": "Process Temp (K)",
            "rotational_speed": "Speed (rpm)",
            "torque": "Torque (Nm)",
            "tool_wear": "Tool Wear (min)"
        })

        st.markdown(
            f'<div class="card-label">SHOWING {len(display)} OF {total} RECORDS</div>',
            unsafe_allow_html=True
        )

        st.dataframe(
            display[[
                "Record ID",
                "Machine ID",
                "Date & Time",
                "Type",
                "Air Temp (K)",
                "Process Temp (K)",
                "Speed (rpm)",
                "Torque (Nm)",
                "Tool Wear (min)",
                "Status",
                "Failure Probability (%)"
            ]],
            use_container_width=True,
            hide_index=True
        )

        csv_data = display.to_csv(index=False).encode("utf-8")

        st.download_button(
            "DOWNLOAD FILTERED RECORDS AS CSV",
            data=csv_data,
            file_name="quanta_prediction_history.csv",
            mime="text/csv"
        )

        st.markdown("---")
        st.markdown("### Database Management")

        if st.button("Clear All Prediction Records"):
            st.session_state.confirm_clear = True

        if st.session_state.get("confirm_clear", False):

            st.warning(
                "This will permanently delete all saved prediction records."
            )

            yes, no = st.columns(2)

            with yes:
                if st.button("Confirm Delete All"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM predictions")
                        conn.commit()

                    st.session_state.confirm_clear = False
                    st.session_state.pop("latest_prediction", None)

                    st.success("Prediction history cleared.")
                    st.rerun()

            with no:
                if st.button("Cancel Deletion"):
                    st.session_state.confirm_clear = False
                    st.rerun()


# ==========================================================
# PAGE 4: ANALYTICS
# ==========================================================

elif page == "Analytics":

    page_heading(
        "DATA VISUALISATION AND INSIGHTS",
        "Analytics Centre.",
        "Explore recorded assessments through interactive visualisations."
    )

    if history.empty:

        st.info(
            "Analytics are currently empty. Generate a few machine assessments "
            "to populate the charts."
        )

    else:

        total, normal, failures, rate = get_summary(history)

        # Analytics metric row

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            metric_card("ASSESSMENTS", total, "Total saved records", "cyan")

        with c2:
            metric_card("NORMAL", normal, "Normal predictions", "cyan")

        with c3:
            metric_card("FAILURE", failures, "Failure predictions", "coral")

        with c4:
            metric_card("FAILURE RATE", f"{rate:.2f}%", "Recorded failure share", "amber")

        st.markdown("")
        st.markdown("### Prediction Intelligence")

        chart_left, chart_right = st.columns(2, gap="large")

        # Donut chart

        with chart_left:

            st.markdown('<div class="card-label">01 · PREDICTION DISTRIBUTION</div>', unsafe_allow_html=True)

            donut = go.Figure(data=[go.Pie(
                labels=["Normal", "Failure"],
                values=[normal, failures],
                hole=0.70,
                marker=dict(
                    colors=["#65e5d3", "#ff7e83"],
                    line=dict(color="#101827", width=4)
                ),
                textinfo="label+percent",
                textfont=dict(color="#edf3fa", size=12),
                hovertemplate="%{label}: %{value}<extra></extra>"
            )])

            donut.update_layout(
                **PLOT_LAYOUT,
                height=340,
                showlegend=True,
                annotations=[dict(
                    text=f"<b>{total}</b><br>Records",
                    x=0.5,
                    y=0.5,
                    font=dict(size=22, color="#edf3fa"),
                    showarrow=False
                )]
            )

            st.plotly_chart(donut, use_container_width=True)

        # Machine type chart

        with chart_right:

            st.markdown('<div class="card-label">02 · MACHINE TYPE DISTRIBUTION</div>', unsafe_allow_html=True)

            type_counts = (
                history["machine_type"]
                .value_counts()
                .reindex(["L", "M", "H"], fill_value=0)
            )

            type_chart = go.Figure(go.Bar(
                x=["Low", "Medium", "High"],
                y=type_counts.values,
                marker=dict(
                    color=["#65e5d3", "#a78bfa", "#f5bd68"],
                    line=dict(width=0),
                    cornerradius=7
                ),
                text=type_counts.values,
                textposition="outside",
                hovertemplate="%{x}: %{y}<extra></extra>"
            ))

            type_chart.update_layout(
                **PLOT_LAYOUT,
                height=340,
                showlegend=False,
                yaxis_title="Number of Assessments"
            )

            st.plotly_chart(type_chart, use_container_width=True)

        st.markdown("---")
        st.markdown("### Failure Analysis")

        p_left, p_right = st.columns(2, gap="large")

        # Probability distribution

        with p_left:

            st.markdown('<div class="card-label">03 · FAILURE PROBABILITY</div>', unsafe_allow_html=True)

            probability_values = history["failure_probability"] * 100

            probability_chart = go.Figure(go.Histogram(
                x=probability_values,
                nbinsx=12,
                marker=dict(
                    color="#a78bfa",
                    line=dict(color="#171e31", width=1)
                ),
                hovertemplate="Probability: %{x:.1f}%<br>Records: %{y}<extra></extra>"
            ))

            probability_chart.update_layout(
                **PLOT_LAYOUT,
                height=320,
                xaxis_title="Estimated Failure Probability (%)",
                yaxis_title="Number of Records",
                showlegend=False
            )

            st.plotly_chart(probability_chart, use_container_width=True)

        # Failure by machine type

        with p_right:

            st.markdown('<div class="card-label">04 · FAILURE BY MACHINE TYPE</div>', unsafe_allow_html=True)

            failure_by_type = (
                history.groupby("machine_type")["prediction"]
                .agg(["count", "sum"])
                .reindex(["L", "M", "H"])
                .fillna(0)
            )

            failure_chart = go.Figure()

            failure_chart.add_trace(go.Bar(
                name="Normal",
                x=["Low", "Medium", "High"],
                y=[
                    failure_by_type.loc[t, "count"] - failure_by_type.loc[t, "sum"]
                    for t in ["L", "M", "H"]
                ],
                marker_color="#65e5d3"
            ))

            failure_chart.add_trace(go.Bar(
                name="Failure",
                x=["Low", "Medium", "High"],
                y=[
                    failure_by_type.loc[t, "sum"]
                    for t in ["L", "M", "H"]
                ],
                marker_color="#ff7e83"
            ))

            failure_chart.update_layout(
                **PLOT_LAYOUT,
                height=320,
                barmode="stack",
                xaxis_title="Machine Type",
                yaxis_title="Number of Predictions"
            )

            st.plotly_chart(failure_chart, use_container_width=True)

        st.markdown("---")
        st.markdown("### Assessment Timeline")

        timeline = history.copy()

        timeline["timestamp"] = pd.to_datetime(timeline["timestamp"])
        timeline["date"] = timeline["timestamp"].dt.date

        daily = (
            timeline.groupby("date")
            .agg(
                Assessments=("id", "count"),
                Failures=("prediction", "sum")
            )
            .sort_index()
            .reset_index()
        )

        trend = go.Figure()

        trend.add_trace(go.Scatter(
            x=daily["date"],
            y=daily["Assessments"],
            name="Assessments",
            mode="lines+markers",
            line=dict(color="#65e5d3", width=3),
            marker=dict(size=8)
        ))

        trend.add_trace(go.Scatter(
            x=daily["date"],
            y=daily["Failures"],
            name="Failures",
            mode="lines+markers",
            line=dict(color="#ff7e83", width=3),
            marker=dict(size=8)
        ))

        trend.update_layout(
            **PLOT_LAYOUT,
            height=350,
            hovermode="x unified",
            xaxis_title="Date",
            yaxis_title="Number of Records"
        )

        st.plotly_chart(trend, use_container_width=True)

        st.markdown("---")
        st.markdown("### Sensor Parameter Overview")

        sensor_data = history[[
            "air_temperature",
            "process_temperature",
            "rotational_speed",
            "torque",
            "tool_wear"
        ]]

        sensor_summary = sensor_data.agg(["mean", "min", "max"]).T

        sensor_summary.columns = [
            "Average",
            "Minimum",
            "Maximum"
        ]

        sensor_summary.index = [
            "Air Temperature (K)",
            "Process Temperature (K)",
            "Rotational Speed (rpm)",
            "Torque (Nm)",
            "Tool Wear (min)"
        ]

        st.dataframe(
            sensor_summary.round(2),
            use_container_width=True
        )

        st.caption(
            "All analytics are calculated from assessments saved in the local database. "
            "They do not represent the original training dataset."
        )


# ==========================================================
# PAGE 5: ABOUT SYSTEM
# ==========================================================

elif page == "About System":

    page_heading(
        "SYSTEM ARCHITECTURE AND DOCUMENTATION",
        "Inside QUANTA.",
        "Understanding the dataset, machine learning model and application architecture."
    )

    # Project introduction

    st.markdown("""
    <div class="glass">
        <div class="eyebrow">PROJECT OVERVIEW</div>
        <div style="font-family:'Space Grotesk';font-size:29px;
                    font-weight:700;margin-top:10px;">
            Industrial Machine Health Intelligence System
        </div>
        <p style="color:#a5b3c5;line-height:1.9;margin-top:12px;">
            QUANTA is a machine learning based predictive maintenance
            prototype. It evaluates machine operating conditions using
            six input parameters and estimates whether a machine may
            experience a failure.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("### Model Performance")

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        metric_card("ACCURACY", "98.15%", "Overall correct predictions", "cyan")

    with m2:
        metric_card("PRECISION", "79.25%", "Positive prediction precision", "violet")

    with m3:
        metric_card("RECALL", "61.76%", "Failure cases detected", "amber")

    with m4:
        metric_card("F1 SCORE", "69.42%", "Precision-recall balance", "coral")

    st.markdown("---")
    st.markdown("### Model Architecture")

    st.markdown("""
    <div class="glass">
        <div style="display:flex;justify-content:center;align-items:center;
                    flex-wrap:wrap;gap:10px;text-align:center;">
            <div class="glass-small" style="min-width:135px;">
                <div class="eyebrow">01</div>
                <b>Sensor Inputs</b>
                <div class="card-note">Six features</div>
            </div>
            <div style="color:#65e5d3;font-size:24px;">→</div>
            <div class="glass-small" style="min-width:135px;">
                <div class="eyebrow">02</div>
                <b>Preprocessing</b>
                <div class="card-note">Encoding + Scaling</div>
            </div>
            <div style="color:#65e5d3;font-size:24px;">→</div>
            <div class="glass-small" style="min-width:135px;">
                <div class="eyebrow">03</div>
                <b>Random Forest</b>
                <div class="card-note">Classification</div>
            </div>
            <div style="color:#65e5d3;font-size:24px;">→</div>
            <div class="glass-small" style="min-width:135px;">
                <div class="eyebrow">04</div>
                <b>Prediction</b>
                <div class="card-note">Normal / Failure</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("### Input Parameters")

    feature_table = pd.DataFrame({
        "Feature": [
            "Type",
            "Air temperature [K]",
            "Process temperature [K]",
            "Rotational speed [rpm]",
            "Torque [Nm]",
            "Tool wear [min]"
        ],
        "Purpose": [
            "Machine quality category",
            "Ambient air temperature",
            "Operating process temperature",
            "Machine rotational speed",
            "Mechanical torque",
            "Accumulated tool wear"
        ]
    })

    st.dataframe(
        feature_table,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")
    st.markdown("### Technology Stack")

    t1, t2, t3 = st.columns(3)

    with t1:
        st.markdown("""
        <div class="glass-small" style="min-height:140px;">
            <div class="eyebrow">MACHINE LEARNING</div>
            <h3>Scikit-learn</h3>
            <div class="card-note">Random Forest, preprocessing and prediction</div>
        </div>
        """, unsafe_allow_html=True)

    with t2:
        st.markdown("""
        <div class="glass-small" style="min-height:140px;">
            <div class="eyebrow">APPLICATION</div>
            <h3>Streamlit + Plotly</h3>
            <div class="card-note">Interactive interface and visual analytics</div>
        </div>
        """, unsafe_allow_html=True)

    with t3:
        st.markdown("""
        <div class="glass-small" style="min-height:140px;">
            <div class="eyebrow">DATABASE</div>
            <h3>SQLite</h3>
            <div class="card-note">Persistent prediction history</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Dataset Information")

    st.markdown("""
    <div class="glass">
        <div class="info-line">
            <span>Dataset</span>
            <strong>AI4I 2020 Predictive Maintenance</strong>
        </div>
        <div class="info-line">
            <span>Dataset Size</span>
            <strong>10,000 records</strong>
        </div>
        <div class="info-line">
            <span>Input Features</span>
            <strong>6 selected features</strong>
        </div>
        <div class="info-line">
            <span>Model Algorithm</span>
            <strong>Random Forest Classifier</strong>
        </div>
        <div class="info-line">
            <span>Database</span>
            <strong>Local SQLite</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    st.warning(
        "Dataset limitation: AI4I 2020 is a synthetic dataset. "
        "QUANTA is a manual-input prototype and does not receive live sensor data. "
        "The model achieved 61.76% recall on the test set, meaning some actual "
        "failure cases were missed. Its predictions must not be used as a "
        "standalone machine-safety decision."
    )

    st.markdown("---")
    st.caption(
        "QUANTA · Quantum-Inspired Industrial Machine Intelligence System · Version 2.0"
    )
