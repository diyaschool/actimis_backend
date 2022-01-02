import plyvel
import json

def user_db_get(key):
    db = plyvel.DB('data/user_db', create_if_missing=True)
    data = db.get(key.encode())
    if data == None:
        return {}
    data = json.loads(data.decode())
    db.close()
    return data

def user_db_put(key, value):
    db = plyvel.DB('data/user_db', create_if_missing=True)
    db.put(key.encode(), json.dumps(value).encode())
    db.close()

def user_db_del(key):
    db = plyvel.DB('data/user_db', create_if_missing=True)
    db.delete(key.encode())
    db.close()

def user_db_list():
    db = plyvel.DB('data/user_db', create_if_missing=True)
    data = []
    for key, _ in db:
        data.append(key.decode())
    db.close()
    return data

if __name__ == '__main__':
    print(user_db_list())
