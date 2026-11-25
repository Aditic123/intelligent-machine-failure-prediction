
# Industrial Machine Health Intelligence System

import streamlit as st
import pandas as pd
import joblib

# Load trained machine learning model
model = joblib.load("industrial_machine_model.joblib")

# Page configuration
st.set_page_config(
    page_title="Industrial Machine Health",
    page_icon="⚙️",
    layout="wide"
)

# Application title
st.title("⚙️ Industrial Machine Health Intelligence System")

st.write(
    "An AI-powered system for predicting industrial machine failure "
    "using machine operating conditions."
)

st.divider()

# Machine input section
st.subheader("Enter Machine Operating Parameters")

col1, col2 = st.columns(2)

with col1:
    machine_type = st.selectbox(
        "Machine Type",
        ["L", "M", "H"]
    )

    air_temp = st.number_input(
        "Air Temperature (K)",
        min_value=295.0,
        max_value=305.0,
        value=300.0,
        step=0.1
    )

    process_temp = st.number_input(
        "Process Temperature (K)",
        min_value=305.0,
        max_value=315.0,
        value=310.0,
        step=0.1
    )

with col2:
    rotational_speed = st.number_input(
        "Rotational Speed (rpm)",
        min_value=1000,
        max_value=3000,
        value=1500
    )

    torque = st.number_input(
        "Torque (Nm)",
        min_value=3.0,
        max_value=80.0,
        value=40.0,
        step=0.1
    )

    tool_wear = st.number_input(
        "Tool Wear (min)",
        min_value=0,
        max_value=260,
        value=100
    )

st.divider()

# Prediction section
if st.button("Predict Machine Health", type="primary"):

    input_data = pd.DataFrame([{
        "Type": machine_type,
        "Air temperature [K]": air_temp,
        "Process temperature [K]": process_temp,
        "Rotational speed [rpm]": rotational_speed,
        "Torque [Nm]": torque,
        "Tool wear [min]": tool_wear
    }])

    prediction = model.predict(input_data)[0]

    failure_probability = model.predict_proba(
        input_data
    )[0][1]

    st.subheader("Machine Health Assessment")

    st.metric(
        "Estimated Failure Probability",
        f"{failure_probability * 100:.2f}%"
    )

    if prediction == 1:
        st.error(
            "⚠️ Potential Machine Failure Detected!"
        )

        st.warning(
            "The model predicts a possible machine failure. "
            "Further inspection by a qualified technician is recommended."
        )

    else:
        st.success(
            "✅ No Machine Failure Predicted"
        )

        st.info(
            "The model predicts normal operation for the supplied inputs."
        )

    st.caption(
        "This is a machine-learning prediction, not a confirmed "
        "physical diagnosis or a calibrated real-world failure probability."
    )
