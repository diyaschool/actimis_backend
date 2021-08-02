import json

def read_db():
    try:
        with open('data/index.db') as f:
            data = f.read()
        return json.loads(data)
    except FileNotFoundError:
        return []

def get_by_username(username):
    data = read_db()
    for user in data:
        if user[0].lower() == username.lower():
            return {"username": user[0], "token": user[1], "email": user[2], 'tags': user[3]}
    return False

def get_by_token(token):
    data = read_db()
    for user in data:
        if user[1] == token:
            return {"username": user[0], "token": user[1], "email": user[2], 'tags': user[3]}
    return False

def get_by_email(email):
    data = read_db()
    for user in data:
        if user[2].lower() == email.lower():
            return {"username": user[0], "token": user[1], "email": user[2], 'tags': user[3]}
    return False

def get_by_tag(tag):
    data = read_db()
    output_data = []
    for user in data:
        if tag in user[3]:
            output_data.append({"username": user[0], "token": user[1], "email": user[2], 'tags': user[3]})
    if output_data == []:
        return False
    return output_data

def write_by_username(username, data):
    old_data = get_by_username(username)
    for key in data:
        old_data[key] = data[key]
    all_data = read_db()
    for user in all_data:
        if user[0].lower() == username.lower():
            user[0] = old_data['username']
            user[1] = old_data['token']
            user[2] = old_data['email']
            user[3] = old_data['tags']
    with open('data/index.db', 'w') as f:
        f.write(json.dumps(all_data))

def write_by_token(token, data):
    old_data = get_by_token(token)
    for key in data:
        old_data[key] = data[key]
    all_data = read_db()
    for user in all_data:
        if user[1] == token:
            user[0] = old_data['username']
            user[1] = old_data['token']
            user[2] = old_data['email']
            user[3] = old_data['tags']
    with open('data/index.db', 'w') as f:
        f.write(json.dumps(all_data))

def write_by_email(email, data):
    old_data = get_by_email(email)
    for key in data:
        old_data[key] = data[key]
    all_data = read_db()
    for user in all_data:
        if user[2].lower() == email.lower():
            user[0] = old_data['username']
            user[1] = old_data['token']
            user[2] = old_data['email']
            user[3] = old_data['tags']
    with open('data/index.db', 'w') as f:
        f.write(json.dumps(all_data))

def list_data():
    output_data = []
    data = read_db()
    for user in data:
        output_data.append({'username': user[0], 'token': user[1], 'email': user[2], 'tags': user[3]})
    return output_data

def new_user(username, token, email, tags):
    if get_by_username(username) != False:
        return (False, "Username already exists")
    if get_by_email(email) != False:
        return (False, "Email already exists")
    all_data = read_db()
    all_data.append([username, token, email, tags])
    with open('data/index.db', 'w') as f:
        f.write(json.dumps(all_data))
    return (True, all_data)

def del_user(username):
    if get_by_username(username) == False:
        return False
    all_data = read_db()
    for i, user in enumerate(all_data):
        if user[0].lower() == username:
            all_data.pop(i)
            break
    with open('data/index.db', 'w') as f:
        f.write(json.dumps(all_data))

if __name__ == '__main__':
    del_user('test')
