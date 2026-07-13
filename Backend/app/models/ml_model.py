from pathlib import Path
import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = PROJECT_ROOT / "saved_models" / "maintenance_model.pkl"

if not MODEL_PATH.exists():
    from Backend.app.train_model import train_model

    train_model()

model = joblib.load(MODEL_PATH)