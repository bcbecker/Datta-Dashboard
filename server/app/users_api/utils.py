from flask import request
from .. import jwt
from ..models import JWTBlocklist

'''
Utility functions for setting up custom JWT callbacks
'''


@jwt.token_in_blocklist_loader
def is_token_in_blocklist(jwt_header: dict, jwt_payload: dict):
    '''
    Custom callback for checking a @jwt_required route to make sure the token
    has not been revoked (added to JWTBlocklist)
    '''
    _jwt_token = request.headers["Authorization"]
    blocked_jwt_token = JWTBlocklist.query.filter_by(jwt_token=_jwt_token).one_or_none()

    return blocked_jwt_token is not None
