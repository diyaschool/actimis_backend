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

def read_user_db(username):
    with open('data/auth.db') as f:
        data = json.loads(f.read())
    try:
        user_data = data[username]
        return user_data
    except KeyError:
        return False

def verify_creds(username, password):
    user_data = read_user_db(username)
    if user_data == False:
        return (False, "ACCOUNT_NOT_FOUND")
    if user_data['password'] == base64.b64encode(hashlib.sha256(hashlib.sha256(password.encode()).digest()).digest()).decode():
        return (True, "AUTH_SUCCESS")
    return (False, "PASSWORD_INCORRECT")

def authorize_jwt(jwt_token):
    idinfo = id_token.verify_oauth2_token(jwt_token, requests.Request(), CLIENT_ID)
    email = idinfo['email']
    if re.search("@[\w.]+", email).group() not in authorized_email_domains:
        return False, "EXTERNAL_ACCOUNT", None, None
    user_data = user_db_indexer.get_by_email(email)
    if user_data == False:
        return False, "ACCOUNT_NOT_FOUND", None, None
    return True, None, user_data['username'], email

def write(username, data):
    with open('data/auth.db') as f:
        all_data = json.loads(f.read())
    all_data[username] = data
    with open('data/auth.db', 'w') as f:
        f.write(json.dumps(all_data))

def modify_user(username, password):
    data = read_user_db(username)
    if data == False:
        return False
    if password != None:
        password = base64.b64encode(hashlib.sha256(hashlib.sha256(password.encode()).digest()).digest()).decode()
        data['password'] = password
    write(username, data)

def new_user(username, password):
    if session_db_manager.get_by_username(username) != False:
        return (False, "Username already exists")
    password = base64.b64encode(hashlib.sha256(hashlib.sha256(password.encode()).digest()).digest()).decode()
    user_data = {'password': password}
    write(username, user_data)
    return (True, "Written successfully")

def del_user(username):
    if read_user_db(username) == False:
        return False
    with open('data/auth.db') as f:
        data = json.loads(f.read())
    data.pop(username)
    with open('data/auth.db', 'w') as f:
        f.write(json.dumps(data))

if __name__ == '__main__':
    print(read_user_db())
