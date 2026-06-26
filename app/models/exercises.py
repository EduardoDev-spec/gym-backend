from ..database import Base
from sqlalchemy import Column, Integer, String, ForeignKey

class Exercises(Base):
    __tablename__ = 'exercises'

    id = Column(Integer, primary_key=True, index=True)
    name_exercises = Column(String, nullable=False)
    workout_type = Column(String, nullable=False)
    sets = Column(Integer, nullable=False)
    reps = Column(Integer, nullable=False)
    weight = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)