import uuid
from flask import request
from flask_restx import Api, Resource, fields
from flask_jwt_extended import (
    create_access_token, get_jwt_identity, jwt_required)
from .models import User


users_api = Api(version="1.0", title="Users API")


'''
Flask-Restx models for associated user request format
'''

signup_model = users_api.model('SignupModel', {"username": fields.String(required=True, min_length=5, max_length=50),
                                               "email": fields.String(required=True, min_length=5, max_length=100),
                                               "password": fields.String(required=True, min_length=8, max_length=50),
                                               })

login_model = users_api.model('LoginModel', {"email": fields.String(required=True, min_length=5, max_length=100),
                                             "password": fields.String(required=True, min_length=8, max_length=50),
                                             })

update_model = users_api.model('UpdateModel', {"userID": fields.String(required=True, min_length=5, max_length=50),
                                               "username": fields.String(required=True, min_length=5, max_length=50),
                                               "email": fields.String(required=True, min_length=5, max_length=100)
                                               })


@users_api.route('/api/users/signup')
class Signup(Resource):
    '''
    Takes signup_model as input and creates a new user
    '''
    @users_api.expect(signup_model)
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
            new_user.save_user()

            return ({'msg': 'Successfully registered.',
                     'user': new_user.to_JSON(),
                     }, 201)
        else:
            return ({'msg': 'User already exists!'}, 202)


@users_api.route('/api/users/login')
class Login(Resource):
    '''
    Takes login_model as input and logs user in with JWT
    '''
    @users_api.expect(login_model)
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
            user.save_user()

            return ({'user': user.to_JSON(),
                     'token': token,
                     'msg': 'Successfully logged in.'}, 200)

        return ({'msg': 'Could not verify credentials'}, 403)
