from pathlib import Path

import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "Dataset" / "Astra_Case.csv"
MODEL_PATH = PROJECT_ROOT / "saved_models" / "maintenance_model.pkl"

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)


def train_model():
    df = pd.read_csv(DATASET_PATH)

    features = [
        "air_temperature",
        "process_temperature",
        "rotational_speed",
        "torque",
        "tool_wear",
        "pressure",
        "vibration",
        "electrical_current"
    ]

    X = df[features]
    y = df["machine_failure"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42
    )

    model.fit(X_train, y_train)

    pred = model.predict(X_test)

    print("Accuracy:", accuracy_score(y_test, pred))

    joblib.dump(model, MODEL_PATH)

    print(f"Model Saved to {MODEL_PATH}")
    return model


if __name__ == "__main__":
    train_model()