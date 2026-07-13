from Backend.app.database import engine
from Backend.app.models.equipment import Equipment
from Backend.app.models.monitoring import MotorSensorData, Alert, MotorAnalysisHistory
from Backend.app.database import Base


def init_db():
    Base.metadata.create_all(bind=engine)
    return True
