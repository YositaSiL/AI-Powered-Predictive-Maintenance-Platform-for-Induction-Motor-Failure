from pathlib import Path
import joblib
import warnings

from sklearn.exceptions import InconsistentVersionWarning

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = PROJECT_ROOT / "saved_models" / "maintenance_model.pkl"


def _load_model():
    if not MODEL_PATH.exists():
        from Backend.app.train_model import train_model
        train_model()

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InconsistentVersionWarning)
            return joblib.load(MODEL_PATH)
    except Exception:
        from Backend.app.train_model import train_model
        train_model()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InconsistentVersionWarning)
            return joblib.load(MODEL_PATH)


model = _load_model()