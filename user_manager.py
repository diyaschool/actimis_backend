import plyvel
import json
import collections.abc

def update_dict(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def get(user):
    db = plyvel.DB('data/user_db', create_if_missing=True)
    data = db.get(user.encode())
    if data == None:
        return False
    data = json.loads(data.decode())
    db.close()
    return data

def put(user, data):
    db = plyvel.DB('data/user_db', create_if_missing=True)
    db.put(user.encode(), json.dumps(data).encode())
    db.close()

def delete(user):
    db = plyvel.DB('data/user_db', create_if_missing=True)
    db.delete(user.encode())
    db.close()

def ls():
    db = plyvel.DB('data/user_db', create_if_missing=True)
    data = []
    for user, _ in db:
        data.append(user.decode())
    db.close()
    return data

def modify(user, new_data):
    data = get(user)
    if data == False:
        return False
    data = update_dict(data, new_data)
    put(user, data)
