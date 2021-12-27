import unittest
import uuid
import json
from flask import current_app
from flask_jwt_extended import create_access_token
from app import create_app, db
from app.models import User, JWTBlocklist
from config import TestingConfig


class TestFlaskApp(unittest.TestCase):

    def setUp(self):
        '''
        Sets up the app environment for testing: creates db, test_client, and app context.
        '''
        self.app = create_app(TestingConfig)
        self.appctx = self.app.app_context()
        self.appctx.push()
        db.create_all()
        self._populate_db()
        self.client = self.app.test_client()


    def tearDown(self):
        '''
        Tears down the set up test_client, db, and app context.
        '''
        db.drop_all()
        self.appctx.pop()
        self.app = None
        self.appctx = None
        self.client = None


    def _populate_db(self):
        '''
        Helper function to populate the db with a user for testing.
        '''
        user = User(
                public_id=str(uuid.uuid4()),
                username='Admin',
                email='admin@gmail.com',
                jwt_auth=False
            )
        user.set_password('adminisabadpassword')
        user.save()


    def test_app(self):
        '''
       Verify that the current app is the app set up in the setUp method.
        '''
        assert self.app is not None
        assert current_app == self.app


    def test_user_signup(self):
        '''
        Given a test client, create a user with the necessary JSON data.
        Verify status codes and user attributes for a successful creation,
        and make sure 202 if user already exists.
        '''

        data = {'username': 'Testing',
                'email': 'testing@gmail.com',
                'password': 'badpassword'
                }

        response_201 = self.client.post('/api/users/signup',
                                        headers={'Content-Type': 'application/json'},
                                        data=json.dumps(data),
                                        follow_redirects=True
                                        )
                    
        response_202 = self.client.post('/api/users/signup',
                                        headers={'Content-Type': 'application/json'},
                                        data=json.dumps(data),
                                        follow_redirects=True
                                        )
        
        user = User.query.filter_by(email='testing@gmail.com').first()

        assert response_201.status_code == 201
        assert response_201.request.path == '/api/users/signup'
        assert response_202.status_code == 202
        assert response_202.request.path == '/api/users/signup'
        assert user.username == 'Testing'
        assert user.jwt_auth == False
        assert user is not None
        assert isinstance(user.to_json(), dict)
        
    
    def test_user_login(self):
        '''
        Given a test client, attempt to log in with proper JSON credentials. Verify status
        codes and user attributes for a successful creation. Verify token exists.
        '''
                 
        response_200 = self.client.post('/api/users/login',
                                        headers={'Content-Type': 'application/json'},
                                        data=json.dumps(
                                                    {'email': 'admin@gmail.com',
                                                    'password': 'adminisabadpassword'
                                                    }),
                                        follow_redirects=True
                                        )

        response_401 = self.client.post('/api/users/login',
                                        headers={'Content-Type': 'application/json'},
                                        data=json.dumps(
                                                    {'email': 'testing@gmail.com',
                                                    'password': 'badpassword'
                                                    }),
                                        follow_redirects=True 
                                        )
        
        response_403 = self.client.post('/api/users/login',
                                        headers={'Content-Type': 'application/json'},
                                        data=json.dumps(
                                                    {'email': 'admin@gmail.com',
                                                    'password': 'WRONGPASSWORD'
                                                    }),
                                        follow_redirects=True 
                                        )

        user = User.query.filter_by(email='admin@gmail.com').first()

        assert response_200.status_code == 200
        assert response_200.request.path == '/api/users/login'
        assert response_200.json.get('token') is not None
        assert response_401.status_code == 401
        assert response_401.request.path == '/api/users/login'
        assert response_401.json.get('token') is None
        assert response_403.status_code == 403
        assert response_403.request.path == '/api/users/login'
        assert response_403.json.get('token') is None
        assert user.jwt_auth == True


    def test_user_update(self):
        '''
        Given a test client, attempt to change their attributes with proper
        JSON credentials and JWT token. Verify status codes and user attributes
        for a successful creation.
        '''

        token_200 = create_access_token(identity='admin@gmail.com')

        response_200 = self.client.post('/api/users/update',
                                        headers={'Content-Type': 'application/json',
                                                'Authorization': f'Bearer {token_200}'
                                                },
                                        data=json.dumps({'username': 'Changed'}),
                                        follow_redirects=True
                                        )

        token_401 = create_access_token(identity='testing@gmail.com')

        response_401 = self.client.post('/api/users/update',
                                        headers={'Content-Type': 'application/json',
                                                'Authorization': f'Bearer {token_401}'
                                                },
                                        data=json.dumps({'username': 'Notgonnawork'}),
                                        follow_redirects=True
                                        )

        user = User.query.filter_by(email='admin@gmail.com').first()

        assert response_200.status_code == 200
        assert response_200.request.path == '/api/users/update'
        assert response_401.status_code == 401
        assert response_401.request.path == '/api/users/update'
        assert user.username == 'Changed'


    def test_user_logout(self):
        '''
        Given a test client, attempt to log user out with JWT token. Verify
        status codes and blocklisted JWT for successful creation.
        '''

        token_200 = create_access_token(identity='admin@gmail.com')

        response_200 = self.client.post('/api/users/logout',
                                        headers={'Content-Type': 'application/json',
                                                'Authorization': f'Bearer {token_200}'
                                                },
                                        follow_redirects=True
                                        )

        token_401 = create_access_token(identity='testing@gmail.com')

        response_401 = self.client.post('/api/users/logout',
                                        headers={'Content-Type': 'application/json',
                                                'Authorization': f'Bearer {token_401}'
                                                },
                                        follow_redirects=True
                                        )

        user = User.query.filter_by(email='admin@gmail.com').first()
        blocked_token = JWTBlocklist.query.filter_by(jwt_token=token_200).first()

        assert response_200.status_code == 200
        assert response_200.request.path == '/api/users/logout'
        assert response_401.status_code == 401
        assert response_401.request.path == '/api/users/logout'
        assert user.jwt_auth == False
        assert blocked_token is not None
        assert isinstance(blocked_token.jwt_token, str)