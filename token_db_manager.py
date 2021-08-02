import plyvel
import json

def list_tokens():
    db = plyvel.DB('data/token_db', create_if_missing=True)
    output_data = []
    for token, data in db:
        output_data.append(token.decode())
    db.close()
    return output_data

def read(token):
    db = plyvel.DB('data/token_db', create_if_missing=True)
    data = json.loads(db.get(token.encode()).decode())
    db.close()
    return data

def write(token, data):
    db = plyvel.DB('data/token_db', create_if_missing=True)
    db.put(token.encode(), json.dumps(data).encode())
    db.close()

def delete(token):
    db = plyvel.DB('data/token_db', create_if_missing=True)
    db.delete(token.encode())
    db.close()

if __name__ == '__main__':
    for token in list_tokens():
        print(token, read(token))
