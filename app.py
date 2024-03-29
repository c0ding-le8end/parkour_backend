from flask import Flask, request, jsonify, make_response
from database import db, init_db
from models import User, Parking_history, Otp_repository
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from sqlalchemy import desc
from flask_cors import CORS
from functools import wraps
import random
import sys

app = Flask(__name__)
CORS(app, origins=["*"], methods=["GET", "POST", "PUT", "DELETE"], supports_credentials=True,
     allow_headers=['X-CSRFToken', 'Authorization'])
app.config['SECRET_KEY'] = 'thisissecret'
list_of_parking_spaces = []


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization').split(" ")[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])

            current_user = User.query.filter(User.user_id == data['user_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!', 'x-access-token': token}), 401

        return f(current_user, *args, **kwargs)

    return decorated


@app.route('/validate', methods=['GET'])
@token_required
def validate(current_user):
    user_data = {}
    user_data['user_id'] = current_user.user_id
    user_data['name'] = current_user.name
    user_data['email'] = current_user.email
    user_data['status_of_last_booking'] = current_user.status_of_last_booking
    users_parking_record = Parking_history.query.filter(Parking_history.user_id == current_user.user_id).order_by(
        desc(Parking_history.start_time)).all()
    parking_history = []
    for record in users_parking_record:
        data = {
            'start_time': None if record.start_time == None else record.start_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
            'end_time': None if record.end_time == None else record.end_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
            'status_of_parking': record.status_of_parking,
            'cost': record.bill_amount}
        parking_history.append(data)
    user_data['parking_history'] = parking_history
    parking_record = Parking_history.query.filter(Parking_history.booking_id == current_user.id_of_last_booking).first()

    if parking_record == None:
        start_time_of_previous_booking = None
        end_time_of_previous_booking = None
        bill_amount = 0
    else:
        start_time_of_previous_booking = str(parking_record.start_time)
        end_time_of_previous_booking = str(parking_record.end_time)
        bill_amount = parking_record.bill_amount

    return jsonify(
        {'details': user_data,
         'start_time_of_previous_booking': start_time_of_previous_booking,
         'end_time_of_previous_booking': end_time_of_previous_booking,
         'bill_amount_of_previous_booking': bill_amount
         })


@app.route('/test', methods=['GET'])
def test():
    return jsonify({"hello": "hello"})


@app.route('/book', methods=['POST'])
@token_required
def book_parking(current_user):
    booking_data = request.form
    if booking_data.get("status") == "finished":
        otp = str(random.randint(1000, 9999))
        otp_record = Otp_repository.query.filter(Otp_repository.user_id == current_user.user_id).first()
        otp_record.otp = otp
        parking_record = Parking_history.query.filter(
            Parking_history.booking_id == current_user.id_of_last_booking).first()
        parking_record.status_of_parking = "finished"
        db.flush()
        db.commit()
        return jsonify({'otp': otp})
    else:
        checkin_time_str = booking_data.get("checkInTime")
        checkin_time_str = checkin_time_str
        checkin_time_obj = datetime.datetime.strptime(checkin_time_str, '%Y-%m-%d %H:%M:%S.%f')
        checkout_time_str = booking_data.get("checkOutTime")
        checkout_time_str = checkout_time_str
        checkout_time_obj = datetime.datetime.strptime(checkout_time_str, '%Y-%m-%d %H:%M:%S.%f')
        parking_records = Parking_history.query.filter(
            (((Parking_history.start_time < checkin_time_obj) & (checkin_time_obj < Parking_history.end_time)) |
             ((Parking_history.start_time < checkout_time_obj) & (
                     checkout_time_obj < Parking_history.end_time))) & Parking_history.status_of_parking != "ended").all()
        # return make_response(jsonify({'message': len(parking_records)}), 400)

        if len(parking_records) == 2:
            return make_response(jsonify({'message': 'parking spaces unavailable at this time'}), 409)
        parking_record = Parking_history(current_user.user_id, datetime.datetime.now(),
                                         checkin_time_obj, checkout_time_obj, "booked",
                                          (checkout_time_obj - checkin_time_obj).total_seconds() * 20 / 3600)
        otp = str(random.randint(1000, 9999))
        otp_record = Otp_repository.query.filter(Otp_repository.user_id == current_user.user_id).first()
        otp_record.otp = otp
        db.add(parking_record)
        db.flush()
        user = User.query.filter(User.user_id == current_user.user_id).first()
        user.status_of_last_booking = "booked"
        user.id_of_last_booking = parking_record.booking_id
        db.flush()
        db.commit()
        return make_response(jsonify({'user_id': current_user.user_id, "otp": otp}), 200)
    # if booking_data.get('parking_status') != None:
    #     user = User.query.filter(User.user_id == current_user.user_id).first()
    #     parking_record = Parking_history.query.filter(Parking_history.booking_id == user.id_of_last_booking).first()
    #     if user.status_of_last_booking == 'invalid' or parking_record.status_of_parking == 'invalid':
    #         return jsonify({'order_expired': 'true'})
    #     parking_record.status_of_parking = booking_data.get('parking_status')
    #
    #     user.status_of_last_booking = booking_data.get('parking_status')
    #     if parking_record.status_of_parking == 'completed':
    #         parking_record.end_time = datetime.datetime.now()
    #     elif parking_record.status_of_parking == 'started':
    #         parking_record.start_time = datetime.datetime.now()
    #     db.commit()
    #     return jsonify({'query': 'success', 'parking_status': booking_data.get('parking_status'),
    #                     'start_time': str(parking_record.start_time)})
    # date_time_str = booking_data.get("estimated_start_time")
    # date_time_str = datetime.datetime.now().strftime('%d:%m:%y') + ' ' + date_time_str
    # date_time_obj = datetime.datetime.strptime(date_time_str, '%d:%m:%y %I:%M%p')
    # if datetime.datetime.now() + datetime.timedelta(minutes=6) > date_time_obj:
    #     return make_response(jsonify("an error occured. Try again "), 400)
    # parking_record = Parking_history(current_user.user_id, booking_data.get('street_id'), datetime.datetime.now(),
    #                                  date_time_obj)
    # user = User.query.filter(User.user_id == current_user.user_id).first()
    # db.add(parking_record)
    # db.flush()
    # user.id_of_last_booking = parking_record.booking_id
    # user.status_of_last_booking = "pending"
    # db.commit()
    # return jsonify({'status_of_parking': "pending", "booking": "confirmed",
    #                 "estimated_start_time": str(parking_record.estimated_start_time)})


@app.route('/checkOtp', methods=['POST'])
def check_otp():
    data = request.form
    user_id, otp = request.form.get('data').split(" ")
    otp_record = Otp_repository.query.filter_by(Otp_repository.user_id == user_id)
    if otp == Otp_repository.otp:
        return jsonify({'signal': 1})
    else:
        return jsonify({'signal': 0})


@app.route('/signup', methods=['POST'])
def create_user():
    data = request.form
    check_email_existence = User.query.filter(User.email == data.get('email')).first()
    if check_email_existence != None:
        return make_response(jsonify({'message': 'Account already exists'}), 500)
    hashed_password = generate_password_hash(data['password'], method='sha256')
    if data.get('name') == None or data.get('phone_number') == None or data.get('email') == None:
        return make_response(jsonify({'message': 'Invalid data'}), 500)
    user_id = str(uuid.uuid4())
    new_user = User(user_id=user_id, name=data.get('name'), phone_number=data.get('phone_number'),
                    email=data.get('email'), password=hashed_password, )

    db.add(new_user)
    db.flush()
    otp_record = Otp_repository(user_id=user_id)
    db.add(otp_record)
    db.flush()
    db.commit()
    token = jwt.encode(
        {'user_id': new_user.user_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)},
        app.config['SECRET_KEY'])
    user_data = {}
    user_data['user_id'] = new_user.user_id
    user_data['name'] = new_user.name
    user_data['email'] = new_user.email
    user_data['status_of_last_booking'] = ""
    user_data['parking_history'] = []
    response = make_response(jsonify({'details': user_data,
                                      'start_time_of_previous_booking': None,
                                      'end_time_of_previous_booking': None,
                                      }, ))
    response.headers.add(_key='Authorization', _value=token)

    return response


@app.route('/user/<user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, user_id):
    user = User.query.filter_by(user_id=user_id).first()

    if not user:
        return jsonify({'message': 'No user found!'})

    db.delete(user)
    db.commit()

    return jsonify({'message': 'The user has been deleted!'})


@app.route('/login', methods=['POST'])
def login():
    auth = request.form

    if not auth or not auth.get('email') or not auth.get('password'):
        response = make_response(jsonify({'status': 'Enter valid credentials', 'auth': auth, 'email': auth.get('email'),
                                          'password': auth.get('password')}),
                                 401)  # , {'WWW-Authenticate': 'Basic realm="Login required!"'})
    else:
        user = User.query.filter_by(email=auth.get('email')).first()

        if not user:
            response = make_response(jsonify({'status': 'Could not find an account associated with the given email'}),
                                     401, )  # {'WWW-Authenticate': 'Basic realm="Login required!"'})

        elif check_password_hash(user.password, auth.get('password')):
            token = jwt.encode(
                {'user_id': user.user_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)},
                app.config['SECRET_KEY'])

            user_data = {'user_id': user.user_id, 'name': user.name, 'email': user.email,
                         'status_of_last_booking': user.status_of_last_booking}
            users_parking_record = Parking_history.query.filter(Parking_history.user_id == user.user_id).all()
            parking_history = []
            for record in users_parking_record:
                data = {
                    'start_time': None if record.start_time == None else record.start_time.strftime("%I:%M%p"),
                    'end_time': None if record.end_time == None else record.end_time.strftime("%I:%M%p"),
                    'status_of_parking': record.status_of_parking}
                parking_history.append(data)
            user_data['parking_history'] = parking_history
            parking_record = Parking_history.query.filter(Parking_history.booking_id == user.id_of_last_booking).first()

            if parking_record == None:
                start_time_of_previous_booking = None
                end_time_of_previous_booking = None
                bill_amount = 0
            else:
                start_time_of_previous_booking = str(parking_record.start_time)
                end_time_of_previous_booking = str(parking_record.end_time)
                bill_amount = parking_record.bill_amount
            response = make_response(jsonify(
                {'details': user_data,
                 'start_time_of_previous_booking': start_time_of_previous_booking,
                 'end_time_of_previous_booking': end_time_of_previous_booking,
                 'bill_amount_of_previous_booking': bill_amount
                 }))
            response.headers.add(_key='Authorization', _value=token)
        else:
            response = make_response(jsonify({'status': 'Enter valid credentials'}),
                                     401)  # {'WWW-Authenticate': 'Basic realm="Login required!"'})

    return response


@app.route('/logout', methods=['GET'])
def logout():
    response = make_response(jsonify({'logOutResult': 'success'}))
    response.headers.remove('Authorization')
    return response


@app.route('/getAvailableSpaces', methods=['GET'])
def available_parking_spaces():
    l = [{"row": 1, "column": 1, "available": "true"}, {"row": 1, "column": 2, "available": "false"}]
    return jsonify({"spaces": l})


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.remove()


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
