from flask import current_app
from .. import jwt

'''
Utility functions for setting up custom JWT callbacks
'''


@jwt.token_in_blocklist_loader
def is_token_in_blocklist(jwt_header: dict, jwt_payload: dict):
    '''
    Custom callback for checking a @jwt_required route to make sure the token
    has not been revoked (added to redis blocklist)
    '''
    jti = jwt_payload['jti']
    token_in_redis = current_app.redis_blocklist.get(jti)

    return token_in_redis is not None