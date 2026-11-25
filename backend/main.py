
import os
import sqlite3
import joblib
import pandas as pd

from pathlib import Path
from datetime import datetime
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# ==========================================
# FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="Intelligent Industrial Machine Failure Prediction System",
    description="AI-powered industrial machine failure prediction API",
    version="1.0.0"
)


# ==========================================
# CORS CONFIGURATION
# ==========================================

origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174"
]

frontend_origin = os.getenv("FRONTEND_ORIGIN")

if frontend_origin:
    origins.extend(
        origin.strip()
        for origin in frontend_origin.split(",")
        if origin.strip()
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ==========================================
# FILE PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "industrial_machine_model.joblib"
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "machine_history.db")))

FEATURES = [
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]"
]

model = None


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

def initialize_database():

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
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


def get_connection():
    return sqlite3.connect(DB_PATH, timeout=30)


# ==========================================
# STARTUP
# ==========================================

@app.on_event("startup")
def startup():

    global model

    if not MODEL_PATH.exists():
        raise FileNotFoundError("Trained model file not found.")

    model = joblib.load(MODEL_PATH)

    initialize_database()


# ==========================================
# INPUT VALIDATION
# ==========================================

class MachineInput(BaseModel):

    machine_id: str = Field(min_length=1, max_length=100)

    machine_type: Literal["L", "M", "H"]

    air_temperature: float
    process_temperature: float
    rotational_speed: float
    torque: float
    tool_wear: float


# ==========================================
# HOME ROUTE
# ==========================================

@app.get("/")
def home():

    return {
        "message": "Industrial Machine Failure Prediction API",
        "status": "Online"
    }


# ==========================================
# MODEL STATUS
# ==========================================

@app.get("/model-status")
def model_status():

    return {
        "model_loaded": model is not None,
        "model_type": type(model).__name__ if model is not None else None,
        "features": list(model.feature_names_in_) if model is not None else [],
        "classes": model.classes_.tolist() if model is not None else []
    }


# ==========================================
# MACHINE FAILURE PREDICTION
# ==========================================

@app.post("/predict")
def predict_machine(data: MachineInput):

    if model is None:
        raise HTTPException(
            status_code=503,
            detail="ML model is not loaded."
        )

    values = {
        "Type": data.machine_type,
        "Air temperature [K]": data.air_temperature,
        "Process temperature [K]": data.process_temperature,
        "Rotational speed [rpm]": data.rotational_speed,
        "Torque [Nm]": data.torque,
        "Tool wear [min]": data.tool_wear
    }

    input_df = pd.DataFrame([values], columns=FEATURES)

    try:
        prediction = int(model.predict(input_df)[0])

        probabilities = model.predict_proba(input_df)[0]
        classes = list(model.classes_)

        if 1 not in classes:
            raise ValueError("Failure class not found in model.")

        failure_index = classes.index(1)
        failure_probability = float(probabilities[failure_index])

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {error}"
        )

    status = "Failure" if prediction == 1 else "Normal"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:

        with get_connection() as conn:

            conn.execute("""
                INSERT INTO predictions (
                    machine_id,
                    timestamp,
                    machine_type,
                    air_temperature,
                    process_temperature,
                    rotational_speed,
                    torque,
                    tool_wear,
                    prediction,
                    failure_probability
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.machine_id,
                timestamp,
                data.machine_type,
                data.air_temperature,
                data.process_temperature,
                data.rotational_speed,
                data.torque,
                data.tool_wear,
                prediction,
                failure_probability
            ))

    except sqlite3.Error as error:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {error}"
        )

    return {
        "machine_id": data.machine_id,
        "prediction": prediction,
        "status": status,
        "failure_probability": failure_probability,
        "failure_probability_percent": round(
            failure_probability * 100, 2
        ),
        "timestamp": timestamp,
        "message": "Prediction completed and saved successfully."
    }


# ==========================================
# MACHINE PREDICTION HISTORY
# ==========================================

@app.get("/history")
def get_prediction_history(limit: int = 100):

    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 500."
        )

    try:

        with get_connection() as conn:

            cursor = conn.execute("""
                SELECT
                    id,
                    machine_id,
                    timestamp,
                    machine_type,
                    air_temperature,
                    process_temperature,
                    rotational_speed,
                    torque,
                    tool_wear,
                    prediction,
                    failure_probability
                FROM predictions
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))

            columns = [
                description[0]
                for description in cursor.description
            ]

            records = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

        return {
            "total_returned": len(records),
            "history": records
        }

    except sqlite3.Error as error:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {error}"
        )
