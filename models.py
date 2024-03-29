from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
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
    time_of_booking = Column(DateTime)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    bill_amount = Column(Integer)
    status_of_parking = Column(String(15))
    user = relationship('User', backref='parking_history')

    def __init__(self, user_id, time_of_booking, start_time=None, end_time=None,
                 status_of_parking="pending", bill_amount=None):
        self.user_id = user_id
        self.time_of_booking = time_of_booking
        self.start_time = start_time
        self.end_time = end_time
        self.status_of_parking = status_of_parking
        self.bill_amount = bill_amount


class Otp_repository(Base):
    __tablename__ = 'otp_repository'
    id = Column(Integer, primary_key=True)
    user_id = Column(
        String(50),
        ForeignKey('user.user_id', ondelete='CASCADE'),
        nullable=False
    )
    otp = Column(Integer)

    def __init__(self, user_id):
        self.user_id = user_id
        self.otp = None
