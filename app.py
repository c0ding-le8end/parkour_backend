from flask import Flask, request, jsonify, make_response,g
from database import db,init_db
from models import User, Street, Parking_history, Surveys
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from sqlalchemy import desc
from flask_cors import CORS
from functools import wraps
import sys

app = Flask(__name__)
CORS(app, origins=["*"], methods=["GET", "POST", "PUT", "DELETE"], supports_credentials=True,
     allow_headers=['X-CSRFToken'])
app.config['SECRET_KEY'] = 'thisissecret'

app.config['WTF_CSRF_TIME_LIMIT'] = 3600
from flask_wtf.csrf import CSRFProtect, generate_csrf, session, validate_csrf

app.config[
    'WTF_CSRF_SECRET_KEY'] = 'erenYeager'

app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='None',
)

csrf = CSRFProtect(app)


# engine = db.create_engine('mysql+pymysql://root:epsilon1630@localhost/PARKING_MANAGEMENT')

# metadata = db.MetaData()
# streets = db.Table('STREET', metadata, autoload=True, autoload_with=engine)
#
#


@app.route('/', methods=['Get'])
def get_streets():
    streets = Street.query.all()
    resultList = []
    for street in streets:
        coordinates= street.coordinate_string.strip('][').replace(')','').replace('(','').split(',')
        refined_coordinates=[]
        lat_lang=[]
        for coordinate in coordinates:
            if len(lat_lang)==2:
                refined_coordinates.append(lat_lang)
                lat_lang=[]
            lat_lang.append(float(coordinate))

        d = {'streetName': street.street_name, 'startLatitude': street.start_latitude,
             'startLongitude': street.start_longitude,
             'stopLatitude': street.stop_latitude, 'stopLongitude': street.stop_longitude, 'id': street.street_id,
             'availableSpaces': street.available_parking_spaces,
             'coordinateString': refined_coordinates}
        resultList.append(d)
    response = jsonify(resultList)
    return response



def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('jwt')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])

            current_user = User.query.filter(User.user_id == data['user_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!', 'x-access-token': token}), 401

        return f(current_user, *args, **kwargs)

    return decorated


@app.route('/validate', methods=['POST'])
@token_required
def validate(current_user):
    user_data = {}
    user_data['user_id'] = current_user.user_id
    user_data['name'] = current_user.name
    user_data['email'] = current_user.email
    user_data['status_of_last_booking'] = current_user.status_of_last_booking
    users_parking_record = Parking_history.query.filter(Parking_history.user_id == current_user.user_id).order_by(
        desc(Parking_history.estimated_start_time)).all()
    parking_history = []
    for record in users_parking_record:
        data = {}
        data['date'] = None if record.estimated_start_time == None else record.estimated_start_time.strftime("%d %B %Y")
        data['start_time'] = None if record.start_time == None else record.start_time.strftime("%I:%M%p")
        data['end_time'] = None if record.end_time == None else record.end_time.strftime("%I:%M%p")
        data['status_of_parking'] = record.status_of_parking
        street = Street.query.filter(Street.street_id == record.street_id).first()
        data['street_name'] = street.street_name
        parking_history.append(data)
    user_data['parking_history'] = parking_history
    survey=Surveys.query.filter(Surveys.user_id == current_user.user_id).first()
    if survey==None:
        survey_given="false"
    else:
        survey_given="true"
    parking_record = Parking_history.query.filter(Parking_history.booking_id == current_user.id_of_last_booking).first()
    if parking_record == None:
        estimated_start_time = None
        start_time_of_previous_booking = None
        street_name = None
    else:
        estimated_start_time = str(parking_record.estimated_start_time)
        street = Street.query.filter(Street.street_id == parking_record.street_id).first()
        street_name = street.street_name
        start_time_of_previous_booking = str(parking_record.start_time)

    return jsonify(
        {'validToken': 'true', 'userData': user_data, 'estimated_start_time_of_previous_booking': estimated_start_time,
         'start_time': start_time_of_previous_booking,
         'street_name': street_name,'survey_given':survey_given})


@app.route('/survey', methods=['POST'])
@token_required
def post_survey(current_user):
    survey_form = request.form
    check_existence = Surveys.query.filter(Surveys.user_id == current_user.user_id).first()
    if check_existence != None:
        return make_response(jsonify({'surveyAlreadyGiven': 'true'}), 300)
    survey = Surveys(user_id=current_user.user_id, answer1=survey_form.get('answer1'),
                     answer2=survey_form.get('answer2'), answer3=survey_form.get('answer3'),
                     review=survey_form.get('review'))
    db.add(survey)
    db.commit()
    return jsonify({'status': 'success'})





@app.route('/book', methods=['POST'])
@token_required
def book_parking(current_user):
    booking_data = request.form
    if booking_data.get('parking_status') != None:
        user = User.query.filter(User.user_id == current_user.user_id).first()
        parking_record = Parking_history.query.filter(Parking_history.booking_id == user.id_of_last_booking).first()
        if user.status_of_last_booking == 'invalid' or parking_record.status_of_parking == 'invalid':
            return jsonify({'order_expired': 'true'})
        parking_record.status_of_parking = booking_data.get('parking_status')

        user.status_of_last_booking = booking_data.get('parking_status')
        if parking_record.status_of_parking == 'completed':
            parking_record.end_time = datetime.datetime.now()
        elif parking_record.status_of_parking == 'started':
            parking_record.start_time = datetime.datetime.now()
        db.commit()
        return jsonify({'query': 'success', 'parking_status': booking_data.get('parking_status'),
                        'start_time': str(parking_record.start_time)})
    date_time_str = booking_data.get("estimated_start_time")
    date_time_str = datetime.datetime.now().strftime('%d:%m:%y') + ' ' + date_time_str
    date_time_obj = datetime.datetime.strptime(date_time_str, '%d:%m:%y %I:%M%p')
    if datetime.datetime.now() + datetime.timedelta(minutes=6) > date_time_obj:
        return make_response(jsonify("an error occured. Try again "), 400)
    parking_record = Parking_history(current_user.user_id, booking_data.get('street_id'), datetime.datetime.now(),
                                     date_time_obj)
    user = User.query.filter(User.user_id == current_user.user_id).first()
    db.add(parking_record)
    db.flush()
    user.id_of_last_booking = parking_record.booking_id
    user.status_of_last_booking = "pending"
    db.commit()
    return jsonify({'status_of_parking': "pending", "booking": "confirmed",
                    "estimated_start_time": str(parking_record.estimated_start_time)})


@app.route('/signup', methods=['POST'])
@csrf.exempt
def create_user():
    data = request.form
    check_email_existence = User.query.filter(User.email == data.get('email')).first()
    if check_email_existence != None:
        return make_response(jsonify({'message': 'Account already exists'}), 500)
    hashed_password = generate_password_hash(data['password'], method='sha256')
    if data.get('name') == None or data.get('phone_number') == None or data.get('email') == None:
        return make_response(jsonify({'message': 'Invalid data'}), 500)
    new_user = User(user_id=str(uuid.uuid4()), name=data.get('name'), phone_number=data.get('phone_number'),
                    email=data.get('email'), password=hashed_password, )
    db.add(new_user)
    db.flush()
    db.commit()
    token = jwt.encode(
        {'user_id': new_user.user_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)},
        app.config['SECRET_KEY'])
    csrf = generate_csrf(app.config['WTF_CSRF_SECRET_KEY'])
    user_data = {}
    user_data['user_id'] = new_user.user_id
    user_data['name'] = new_user.name
    user_data['email'] = new_user.email
    user_data['status_of_last_booking'] = ""
    user_data['parking_history'] = []
    response = make_response(jsonify({'csrf': csrf, 'userData': user_data,
                                      'estimated_start_time_of_previous_booking': None,
                                      'start_time': None,
                                      'timeLimit': app.config['WTF_CSRF_TIME_LIMIT'],'survey_given':"false"}, ))
    response.set_cookie(key='jwt', value=token, httponly=True, samesite="None", domain='127.0.0.1', secure=True)

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
@csrf.exempt
def login():
    auth = request.form

    if not auth or not auth.get('email') or not auth.get('password'):
        response = make_response(jsonify({'status': 'Enter valid credentials'}),
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

            csrf = generate_csrf(app.config['WTF_CSRF_SECRET_KEY'])
            user_data = {}
            user_data['user_id'] = user.user_id
            user_data['name'] = user.name
            user_data['email'] = user.email
            user_data['status_of_last_booking'] = user.status_of_last_booking
            users_parking_record = Parking_history.query.filter(Parking_history.user_id == user.user_id).order_by(
                desc(Parking_history.estimated_start_time)).all()
            parking_history = []
            for record in users_parking_record:
                data = {}
                data['date'] = None if record.estimated_start_time == None else record.estimated_start_time.strftime(
                    "%d %B %Y")
                data['start_time'] = None if record.start_time == None else record.start_time.strftime("%I:%M%p")
                data['end_time'] = None if record.end_time == None else record.end_time.strftime("%I:%M%p")
                data['status_of_parking'] = record.status_of_parking
                street = Street.query.filter(Street.street_id == record.street_id).first()
                data['street_name'] = street.street_name
                parking_history.append(data)
            user_data['parking_history'] = parking_history
            survey=Surveys.query.filter(Surveys.user_id == user.user_id).first()
            if survey==None:
                survey_given="false"
            else:
                survey_given="true"
            parking_record = Parking_history.query.filter(Parking_history.booking_id == user.id_of_last_booking).first()

            if parking_record == None:
                street_name = None
                start_time_of_previous_booking=None
                estimated_start_time=None
            else:
                estimated_start_time = str(parking_record.estimated_start_time)
                street = Street.query.filter(Street.street_id == parking_record.street_id).first()
                street_name = street.street_name
                start_time_of_previous_booking = str(parking_record.start_time)
            response = make_response(jsonify({'csrf': csrf, 'userData': user_data,
                                              'estimated_start_time_of_previous_booking': estimated_start_time,
                                              'start_time': start_time_of_previous_booking,
                                              'timeLimit': app.config['WTF_CSRF_TIME_LIMIT'],
                                              'street_name':street_name,'survey_given':survey_given}, ))

            response.set_cookie(key='jwt', value=token, httponly=True, samesite="None", domain='127.0.0.1', secure=False)
        else:
            response = make_response(jsonify({'status': 'Enter valid credentials'}),
                                     401)  # {'WWW-Authenticate': 'Basic realm="Login required!"'})

    return response


@app.route('/logout', methods=['GET'])
def logout():
    response = make_response(jsonify({'logOutResult': 'success'}))
    response.set_cookie(key='jwt', value="", httponly=True, samesite="None", domain='127.0.0.1', secure=True)
    response.set_cookie(key='session', value="", httponly=True, samesite="None", domain='127.0.0.1', secure=True)
    return response


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.remove()



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
 # app.run(host='127.0.0.1', port=5000, debug=True)


# @app.route('/users', methods=['GET'])
# @token_required
# def get_all_users(current_user):
#     users = User.query.all()
#
#     output = []
#
#     for user in users:
#         user_data = {}
#         user_data['user_id'] = user.user_id
#         user_data['name'] = user.name
#         user_data['password'] = user.password
#         output.append(user_data)
#     response = jsonify({'users': output})
#     return response
#
#
# @app.route('/user', methods=['GET'])
# @token_required
# def get_one_user(current_user):
#     # user = User.query.filter_by(user_id=user_id).first()
#     #
#     # if not user:
#     #     return jsonify({'message': 'No user found!'})
#
#     user_data = {}
#     user_data['user_id'] = current_user.user_id
#     user_data['name'] = current_user.name
#     user_data['email'] = current_user.email
#
#     return jsonify({'user': user_data})
# @app.route('/user/<user_id>', methods=['PUT'])
# @token_required
# def promote_user(current_user, user_id):
#
#     user = User.query.filter_by(user_id=user_id).first()
#
#     if not user:
#         return jsonify({'message': 'No user found!'})
#
#     user.admin = True
#     db.commit()
#
#     return jsonify({'message': 'The user has been promoted!'})