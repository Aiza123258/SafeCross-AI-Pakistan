from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from utils.predictor import predict_severity

from .database import engine, get_db
from .models import Base, Prediction


# Create database tables automatically
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="SafeCross AI Backend",
    description="AI-powered road accident prediction and safety backend",
    version="1.0.0"
)


class SeverityRequest(BaseModel):
    weather: str
    road_condition: str
    accident_cause: str
    traffic_density: str
    vehicles_involved: int
    nearby_accidents: int
    hour: int
    day_of_week: int
    is_night: int
    latitude: Optional[float] = 0.0
    longitude: Optional[float] = 0.0
    month: Optional[int] = 6


@app.get("/")
def root():
    return {
        "message": "SafeCross AI Backend is running",
        "status": "success"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/predict/severity")
def predict_severity_api(
    data: SeverityRequest,
    db: Session = Depends(get_db)
):
    result = predict_severity(
        weather=data.weather,
        road_condition=data.road_condition,
        accident_cause=data.accident_cause,
        traffic_density=data.traffic_density,
        vehicles_involved=data.vehicles_involved,
        nearby_accidents=data.nearby_accidents,
        hour=data.hour,
        day_of_week=data.day_of_week,
        is_night=data.is_night,
        latitude=data.latitude,
        longitude=data.longitude,
        month=data.month
    )

    severity = result.get("severity", "Unknown")

    probabilities = result.get("probabilities", {})
    confidence = probabilities.get(severity, 0.0)

    prediction = Prediction(
        severity=severity,
        confidence=float(confidence)
    )

    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    return {
        "status": "success",
        "prediction": result,
        "database": {
            "saved": True,
            "prediction_id": prediction.id
        }
    }


@app.get("/predictions")
def get_predictions(
    db: Session = Depends(get_db)
):
    predictions = (
        db.query(Prediction)
        .order_by(Prediction.id.desc())
        .all()
    )

    return {
        "status": "success",
        "count": len(predictions),
        "predictions": [
            {
                "id": prediction.id,
                "severity": prediction.severity,
                "confidence": prediction.confidence,
                "created_at": prediction.created_at
            }
            for prediction in predictions
        ]
    }


@app.get("/predictions/{prediction_id}")
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db)
):
    prediction = (
        db.query(Prediction)
        .filter(Prediction.id == prediction_id)
        .first()
    )

    if not prediction:
        return {
            "status": "error",
            "message": "Prediction not found"
        }

    return {
        "status": "success",
        "prediction": {
            "id": prediction.id,
            "severity": prediction.severity,
            "confidence": prediction.confidence,
            "created_at": prediction.created_at
        }
    }