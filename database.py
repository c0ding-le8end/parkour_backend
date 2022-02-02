from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime


engine = create_engine('mysql+pymysql://bc3c42ec0d4186:80127fc7@eu-cdbr-west-02.cleardb.net/heroku_9c873aff64513d1')
db = scoped_session(sessionmaker(autocommit=False,
                                 autoflush=False,
                                 bind=engine))
Base = declarative_base()
Base.query = db.query_property()


def init_db():
    import models
    Base.metadata.create_all(bind=engine)


def check():
    import models as m
    date_time_str = "3:30PM"
    date_time_str=datetime.now().strftime('%d:%m:%y')+' '+date_time_str
    date_time_obj = datetime.strptime(date_time_str, '%d:%m:%y %I:%M%p')
    u = m.Parking_history("619777f8-c50a-441e-bc71-ca2f073f5aab", "W0172", datetime.now(), datetime.now())
    user = m.User.query.filter(m.User.user_id == "619777f8-c50a-441e-bc71-ca2f073f5aab").first()
    db.add(u)
    db.flush()
    user.id_of_last_booking = u.booking_id
    user.status_of_last_booking = "pending"
    db.commit()
    print("The type of the date is now", type(date_time_obj))
    print("The date is", date_time_obj)
    d={'1':1}
    print("here")
    print(d.get('apple')!=None)
    print(date_time_str)
    # parking_record = m.Parking_history.query.filter(m.Parking_history.booking_id == 7).first()
    # s='Thu, 20 Jan 2022 13:03:00 GMT'
    # d=datetime.strptime(s,'%b, %d %Y %H:%M:%S %z')
    # s=d.strftime('%I:%M%p')
    # print(datetime.now())
    # s=str(parking_record.estimated_start_time)
    # print(s)
    # print(parking_record.estimated_start_time)

def check2():
    import models as m
    date_time_str = "3:30PM"
    date_time_str=datetime.now().strftime('%d:%m:%y')+' '+date_time_str
    date_time_obj = datetime.strptime(date_time_str, '%d:%m:%y %I:%M%p')
    u = m.Parking_history("e266d638-e215-4673-99e2-fb837c6f11e6", datetime.now(), datetime.now().time())
    user = m.User.query.filter(m.User.user_id == "e266d638-e215-4673-99e2-fb837c6f11e6").first()
    db.add(u)
    db.flush()
    user.id_of_last_booking = u.booking_id
    user.status_of_last_booking = "pending"
    db.commit()
    print("The type of the date is now", type(date_time_obj))
    print("The date is", date_time_obj)
    print(date_time_str)