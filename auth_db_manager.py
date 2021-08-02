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
    user_data = read_user_db(username)
    if user_data == False:
        return (False, "Username not found")
    if user_data['password'] == base64.b64encode(hashlib.sha256(hashlib.sha256(password.encode()).digest()).digest()).decode():
        return (True, "Authentication successful")
    return (False, "Password incorrect")

def write(username, data):
    with open('data/auth.db') as f:
        all_data = json.loads(f.read())
    all_data[username] = data
    with open('data/auth.db', 'w') as f:
        f.write(json.dumps(all_data))

def modify_user(username, password, name, email, tags):
    data = read_user_db(username)
    if data == False:
        return False
    if password != None:
        password = base64.b64encode(hashlib.sha256(hashlib.sha256(password.encode()).digest()).digest()).decode()
        data['password'] = password
    if email != None:
        data['email'] = email
    if tags != None:
        data['tags'] = tags
    if name != None:
        data['name'] = name
    write(username, data)

def new_user(username, password, name, email, tags):
    if index_db_manager.get_by_username(username) != False:
        return (False, "Username already exists")
    if index_db_manager.get_by_email(email) != False:
        return (False, "Email already exists")
    password = base64.b64encode(hashlib.sha256(hashlib.sha256(password.encode()).digest()).digest()).decode()
    user_data = {'password': password, 'name': name, 'email': email, 'tags': tags}
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
    del_user('test')
