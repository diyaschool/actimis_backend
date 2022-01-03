"""
# Authentication Database manager.
# Holds only double-hashed passwords of users.

Authentication Manager.
Passwordless login with Google.
Handles JWT tokens.
"""

import json
import session_db_manager
import hashlib
import base64
from google.oauth2 import id_token
from google.auth.transport import requests
import user_db_indexer
import re

CLIENT_ID = "18178721920-v27esm525ddg2pdmemu7i37olq9bglkq.apps.googleusercontent.com"
authorized_email_domains = ["@gmail.com", "@diyaschool.com"]

def authorize_jwt(jwt_token):
    idinfo = id_token.verify_oauth2_token(jwt_token, requests.Request(), CLIENT_ID)
    email = idinfo['email']
    if re.search("@[\w.]+", email).group() not in authorized_email_domains:
        return False, "EXTERNAL_ACCOUNT", None, None
    user_data = user_db_indexer.get_by_email(email)
    if user_data == False:
        return False, "ACCOUNT_NOT_FOUND", None, None
    return True, None, user_data['username'], email

if __name__ == '__main__':
    print(read_user_db())
