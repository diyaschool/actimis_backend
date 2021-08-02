import json
import index_db_manager
import hashlib
import base64
import os
import shutil

def read_user_db(username):
    with open('data/auth.db') as f:
        data = json.loads(f.read())
    try:
        user_data = data[username]
        return user_data
    except KeyError:
        return False

def verify_creds(username, password):
    pass

def write(username, data):
    with open('data/auth.db') as f:
        all_data = json.loads(f.read())
    all_data[username] = data
    with open('data/auth.db', 'w') as f:
        f.write(all_data)

def modify_user(username, password, email, tags):
    data = read_user_db(username)
    if data == False:
        return False
    if password != None:
        password = base64.b64encode(hashlib.sha256(hashlib.sha256(password.encode()).digest()).digest())
        data['password'] = password
    if email != None:
        data['email'] = email
    if tags != None:
        data['tags'] = tags
    write(username, data)

def new_user(username, password, email, tags):
    if index_db_manager.get_by_username(username) == False:
        return (False, "Username already exists")
    if index_db_manager.get_by_email(email) == False:
        return (False, "Email already exists")
    password = base64.b64encode(hashlib.sha256(hashlib.sha256(password.encode()).digest()).digest())
    user_data = {'password': password, 'email': email, 'tags': tags}
    write(username, user_data)
