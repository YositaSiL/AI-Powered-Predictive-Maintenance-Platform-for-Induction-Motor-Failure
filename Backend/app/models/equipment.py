from sqlalchemy import Column, Integer, Float
from Backend.app.database import Base


class Equipment(Base):
    __tablename__ = "astra_case"

    id = Column(Integer, primary_key=True, index=True)

    udi = Column(Integer)

    air_temperature = Column(Float)
    process_temperature = Column(Float)

    rotational_speed = Column(Integer)
    torque = Column(Float)

    tool_wear = Column(Integer)

    pressure = Column(Float)
    vibration = Column(Float)
    electrical_current = Column(Float)

    machine_failure = Column(Integer)

    twf = Column(Integer)
    hdf = Column(Integer)
    pwf = Column(Integer)
    osf = Column(Integer)
    rnf = Column(Integer)