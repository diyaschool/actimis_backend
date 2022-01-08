"""
Relational database. Contains user metadata, along with auth tokens.
Stored in JSON-like arrays in the form of a table.
"""

import json

def read_db():
    """
    raw-reads the whole database (may be problematic in future with more data)
    """
    try:
        with open('data/index.db') as f:
            data = f.read()
        return json.loads(data)
    except FileNotFoundError:
        return []

def get_by_username(username):
    """
    fetches user metadata by username
    """
    data = read_db()
    for user in data:
        if user[0].lower() == username.lower():
            return {"username": user[0], "tokens": user[1], "email": user[2], 'tags': user[3]}
    return False

def get_by_token(token):
    """
    fetches user metadata by token
    """
    data = read_db()
    for user in data:
        if token in user[1]:
            return {"username": user[0], "tokens": user[1], "email": user[2], 'tags': user[3]}
    return False

def get_by_email(email):
    """
    fetches user metadata by email address
    """
    data = read_db()
    for user in data:
        if user[2].lower() == email.lower():
            return {"username": user[0], "tokens": user[1], "email": user[2], 'tags': user[3]}
    return False

def get_by_tag(tag):
    """
    fetches and returns a list of users that belong to a tag-group
    """
    data = read_db()
    output_data = []
    for user in data:
        if tag in user[3]:
            output_data.append({"username": user[0], "tokens": user[1], "email": user[2], 'tags': user[3]})
    if output_data == []:
        return False
    return output_data

def write_by_username(username, new_data):
    """
    writes data to a row, using the username as index
    """
    data = get_by_username(username)
    data.update(new_data)
    all_data = read_db()
    for user in all_data:
        if user[0].lower() == username.lower():
            user[0] = data['username']
            user[1] = data['tokens']
            user[2] = data['email']
            user[3] = data['tags']
    with open('data/index.db', 'w') as f:
        f.write(json.dumps(all_data))

def write_by_token(token, new_data):
    """
    writes data to a row, using the token as index
    """
    data = get_by_token(token)
    data.update(new_data)
    all_data = read_db()
    for user in all_data:
        if token in user[1]:
            user[0] = data['username']
            user[1] = data['tokens']
            user[2] = data['email']
            user[3] = data['tags']
    with open('data/index.db', 'w') as f:
        f.write(json.dumps(all_data))

def write_by_email(email, data):
    """
    writes data to a row, using the email address as index
    """
    old_data = get_by_email(email)
    data.update(new_data)
    all_data = read_db()
    for user in all_data:
        if user[2].lower() == email.lower():
            user[0] = old_data['username']
            user[1] = old_data['tokens']
            user[2] = old_data['email']
            user[3] = old_data['tags']
    with open('data/index.db', 'w') as f:
        f.write(json.dumps(all_data))

def list_data():
    """
    list all entries in database
    """
    output_data = []
    data = read_db()
    for user in data:
        output_data.append({'username': user[0], 'tokens': user[1], 'email': user[2], 'tags': user[3]})
    return output_data

def new_entry(username, tokens, email, tags):
    """
    create a new entry with the following data:
    username, tokens (list), email address, tags (list)
    """
    if get_by_username(username) != False:
        return (False, "Username already exists")
    if get_by_email(email) != False:
        return (False, "Email already exists")
    all_data = read_db()
    all_data.append([username, tokens, email, tags])
    with open('data/index.db', 'w') as f:
        f.write(json.dumps(all_data))
    return (True, all_data)

def del_entry(username):
    """
    delete a new entry.
    """
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
    print(list_data())
