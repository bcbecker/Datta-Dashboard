import uuid
from datetime import datetime
from flask import request
from flask_restx import Api, Resource, fields
from flask_jwt_extended import (create_access_token, get_jwt_identity, jwt_required)
from .models import User, JWTBlocklist


users_api = Api(version="1.0", title="Users API")


'''
Flask-Restx models for associated user request format
'''

signup_user_model = users_api.model('SignupModel', {"username": fields.String(required=True, min_length=5, max_length=50),
                                                    "email": fields.String(required=True, min_length=5, max_length=100),
                                                    "password": fields.String(required=True, min_length=8, max_length=50),
                                                    })

login_user_model = users_api.model('LoginModel', {"email": fields.String(required=True, min_length=5, max_length=100),
                                                  "password": fields.String(required=True, min_length=8, max_length=50),
                                                  })

update_user_model = users_api.model('UpdateModel', {"userID": fields.String(required=True, min_length=5, max_length=50),
                                                    "username": fields.String(required=True, min_length=5, max_length=50),
                                                    "email": fields.String(required=True, min_length=5, max_length=100)
                                                    })


@users_api.route('/api/users/signup')
class Signup(Resource):
    '''
    Takes signup_user_model as input and creates a new user based on the data
    '''
    @users_api.expect(signup_user_model)
    def post(self):

        request_data = request.form
        _username = request_data.get('username')
        _email = request_data.get('email')
        _password = request_data.get('password')

        user = User.query.filter_by(email=_email).first()

        if not user:
            new_user = User(
                public_id=str(uuid.uuid4()),
                username=_username,
                email=_email,
                jwt_auth=False
            )

            new_user.set_password(_password)
            new_user.save()

            return ({'msg': 'Successfully registered.',
                     'user': new_user.to_json(),
                     }, 201)
        else:
            return ({'msg': 'User already exists!'}, 202)


@users_api.route('/api/users/login')
class Login(Resource):
    '''
    Takes login_user_model as input and logs user in, creating JWT for auth
    '''
    @users_api.expect(login_user_model)
    def post(self):

        request_data = request.form
        _email = request_data.get('email')
        _password = request_data.get('password')

        user = User.query.filter_by(email=_email).first()

        if not user:
            return ({'msg': 'User not found'}, 401)

        if user.check_password(_password):
            token = create_access_token(identity=user.email)  # should be public_id
            user.jwt_auth = True
            user.save()

            return ({'msg': 'Successfully logged in.',
                     'user': user.to_json(),
                     'token': token}, 200)

        return ({'msg': 'Could not verify credentials'}, 403)


@users_api.route('/api/users/update')
class UpdateUser (Resource):
    '''
    Takes update_user_model as input and updates their data if they provide a valid JWT
    '''
    @users_api.expect(update_user_model)
    @jwt_required()
    def post(self):

        request_data = request.form
        _new_username = request_data.get('username')
        _new_email = request_data.get('email')
        _new_password = request_data.get('password')

        user = User.query.filter_by(email=get_jwt_identity()).first()

        if _new_username:
            user.username = _new_username
        if _new_email:
            user.email = _new_email
        if _new_password:
            user.password = user.set_password(_new_password)

        user.save()

        return ({'msg': 'Successfully updated user.',
                 'user': user.to_json()}, 200)


@users_api.route('/api/users/logout')
class LogoutUser(Resource):
    '''
    Logs user out, adding their JWT to JWTBlocklist
    '''
    @jwt_required()
    def post(self):

        _jwt_token = request.headers["Authorization"]
        jwt_token_blocked = JWTBlocklist(jwt_token= _jwt_token, time_created=datetime.utcnow())
        jwt_token_blocked.save()

        user = User.query.filter_by(email=get_jwt_identity()).first()
        user.jwt_auth = False
        user.save()

        return ({'msg': 'Successfully logged out.',
                 'user': user.to_json()}, 200)