from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, ForeignKey, DateTime, Time
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = 'user'
    user_id = Column(String(50), primary_key=True)
    name = Column(String(50))
    phone_number = Column(String(10))
    email = Column(String(320))
    password = Column(String(256))
    id_of_last_booking = Column(Integer)
    status_of_last_booking = Column(String(15))

    def __init__(self, user_id, name, phone_number, email, password):
        self.user_id = user_id
        self.name = name
        self.phone_number = phone_number
        self.email = email
        self.password = password




class Parking_history(Base):
    __tablename__ = 'parking_history'
    booking_id = Column(Integer, primary_key=True)

    user_id = Column(
        String(50),
        ForeignKey('user.user_id', ondelete='CASCADE'),
        nullable=False
    )
    street_id = Column(
        String(40),
        ForeignKey('street.street_id', ondelete='CASCADE'),
        nullable=False
    )
    time_of_booking = Column(DateTime)
    estimated_start_time = Column(DateTime)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status_of_parking = Column(String(15))
    user = relationship('User', backref='parking_history')
    street = relationship('Street', backref='parking_history')

    def __init__(self, user_id, street_id, time_of_booking, estimated_start_time, start_time=None, end_time=None,
                 status_of_parking="pending"):
        self.user_id = user_id
        self.street_id = street_id
        self.time_of_booking = time_of_booking
        self.estimated_start_time = estimated_start_time
        self.start_time = start_time
        self.end_time = end_time
        self.status_of_parking = status_of_parking


class Surveys(Base):
    __tablename__ = 'surveys'
    id=Column(Integer,primary_key=True)
    user_id = Column(
        String(50),
        ForeignKey('user.user_id', ondelete='CASCADE'),
        nullable=False
    )
    answer1 = Column(String(3), nullable=False)
    answer2 = Column(String(1), nullable=False)
    answer3 = Column(String(3), nullable=False)
    review = Column(String(256))
    user = relationship('User', backref='Surveys')

    def __init__(self, user_id, answer1,answer2,answer3,review=None):
        self.user_id = user_id
        self.answer1=answer1
        self.answer2=answer2
        self.answer3=answer3
        self.review=review
