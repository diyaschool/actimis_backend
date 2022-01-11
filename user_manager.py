import plyvel
import json

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
    data.update(new_data)
    put(user, data)

if __name__ == '__main__':
    print(put("admin1", {"test_data": {"classic_mcq": {"user_sessions": {}}}}))
    # print(modify("admin0", {"test": "hi"}))
    print(get("admin1"))
