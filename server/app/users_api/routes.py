import uuid
from flask import request, make_response
from flask_restx import Api, Resource, fields
from . import bcrypt
from .models import User

users_api = Api(version="1.0", title="Users API")

signup_model = users_api.model('SignupModel', {"username": fields.String(required=True, min_length=5, max_length=50),
                                               "email": fields.String(required=True, min_length=5, max_length=100),
                                               "password": fields.String(required=True, min_length=8, max_length=50),
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
                password=bcrypt.generate_password_hash(_password),
                jwt_auth=False
            )

            new_user.save_user()

            return ({'user': new_user.email,
                     'msg': 'Successfully registered.'}, 201)
        else:
            # returns 202 if user already exists
            return make_response('User already exists. Please Log in.', 202)
