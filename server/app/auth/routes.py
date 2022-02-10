import uuid
from flask import current_app, request, jsonify, make_response
from flask_restx import Api, Resource, fields
from flask_jwt_extended import (
    create_access_token, get_jwt_identity, jwt_required, get_jwt,
    set_access_cookies, unset_access_cookies, get_csrf_token)
from ..models import User
from .utils import is_token_in_blocklist


auth = Api(version="1.0", title="User Auth")


'''
Flask-Restx models for associated user request format
'''

signup_user_model = auth.model('SignupModel', {"username": fields.String(required=True, min_length=3, max_length=50),
                                               "email": fields.String(required=True, min_length=5, max_length=75),
                                               "password": fields.String(required=True, min_length=8, max_length=50),
                                               })

login_user_model = auth.model('LoginModel', {"email": fields.String(required=True, min_length=5, max_length=75),
                                             "password": fields.String(required=True, min_length=8, max_length=50),
                                             })

update_user_model = auth.model('UpdateModel', {"username": fields.String(required=True, min_length=3, max_length=50),
                                               "email": fields.String(required=True, min_length=5, max_length=75)
                                               })


@auth.route('/api/users/signup')
class Signup(Resource):
    '''
    Takes signup_user_model as input and creates a new user based on the data,
    if user doesn't already exist
    '''
    @auth.expect(signup_user_model, validate=True)
    def post(self):

        request_data = request.get_json()
        _username = request_data.get('username')
        _email = request_data.get('email')
        _password = request_data.get('password')

        user = User.query.filter_by(email=_email).first()

        if not user:
            new_user = User(
                public_id=str(uuid.uuid4()),
                username=_username,
                email=_email
            )

            new_user.set_password(_password)
            new_user.save()

            return ({'success': True,
                     'msg': 'Successfully registered.',
                     'user': new_user.username,
                     }, 201)
        else:
            return ({'success': False,
                     'msg': 'User already exists!'
                     }, 202)


@auth.route('/api/users/login')
class Login(Resource):
    '''
    Takes login_user_model as input and logs user in if passwords match,
    creating JWT for auth to be sent to protected endpoints
    '''
    @auth.expect(login_user_model, validate=True)
    def post(self):

        request_data = request.get_json()
        _email = request_data.get('email')
        _password = request_data.get('password')

        user = User.query.filter_by(email=_email).first()

        if not user:
            return ({'success': False,
                     'msg': 'User not found'
                     }, 401)

        if user.check_password(_password):
            token = create_access_token(identity=user.public_id)

            response = jsonify({'success': True,
                                'msg': 'Successfully logged in.',
                                'user': user.to_json()
                                })

            set_access_cookies(response, token)
            return make_response(response, 200)

        return ({'success': False,
                 'msg': 'Could not verify credentials'
                 }, 403)


@auth.route('/api/users/update')
class UpdateUser (Resource):
    '''
    Takes update_user_model as input and updates their data if they provide a valid JWT
    and the user exists
    '''
    @auth.expect(update_user_model)
    @jwt_required()
    def put(self):

        request_data = request.get_json()
        _new_username = request_data.get('username')
        _new_email = request_data.get('email')

        user = User.query.filter_by(public_id=get_jwt_identity()).first()

        if not user:
            return ({'success': False,
                     'msg': 'User not found'
                     }, 401)

        if _new_username:
            user.username = _new_username
        if _new_email:
            user.email = _new_email

        user.save()

        return ({'success': True,
                 'msg': 'Successfully updated user.',
                 'user': user.to_json()
                 }, 200)


@auth.route('/api/users/logout')
class LogoutUser(Resource):
    '''
    Logs user out, adding their JWT to redis_blocklist
    '''
    @jwt_required()
    def post(self):

        user = User.query.filter_by(public_id=get_jwt_identity()).first()

        if user:
            user.public_id = str(uuid.uuid4())
            user.save()

            _jti = get_jwt()['jti']
            current_app.redis_blocklist.setex(_jti, current_app.TTL, '')

            response = jsonify({'success': True,
                                'msg': 'Successfully logged out.',
                                'user': user.username
                                })

            unset_access_cookies(response)
            return make_response(response, 200)

        return ({'success': False,
                 'msg': 'User not found'
                 }, 401)
