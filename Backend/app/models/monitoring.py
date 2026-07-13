from sqlalchemy import Column, Integer, Float, String, DateTime, Text
from sqlalchemy.sql import func

from Backend.app.database import Base


class MotorSensorData(Base):
    __tablename__ = "motor_sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    motor_id = Column(Integer, nullable=False, index=True)
    temperature = Column(Float, nullable=False)
    vibration = Column(Float, nullable=False)
    electrical_current = Column(Float, nullable=False)
    pressure = Column(Float, nullable=False)
    rpm = Column(Float, nullable=False)
    torque = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    motor_id = Column(Integer, nullable=False, index=True)
    alert_type = Column(String(80), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    source = Column(String(80), default="monitoring_engine")


class MotorAnalysisHistory(Base):
    __tablename__ = "motor_analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    motor_id = Column(Integer, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    health_score = Column(Float, nullable=False)
    failure_probability = Column(Float, nullable=False)
    rul = Column(Float, nullable=False)
    trend = Column(String(20), nullable=False)
    recommendation = Column(Text, nullable=False)
