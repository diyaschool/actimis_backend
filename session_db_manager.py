"""
Session database manager, handles token storage.
Tokens are unique identifiers of sessions.
"""

import plyvel
import json
import user_db_indexer

def list_tokens():
    """
    list all sessions from all users along with details
    """
    db = plyvel.DB('data/token_db', create_if_missing=True)
    output_data = []
    for token, data in db:
        output_data.append((token.decode(), json.loads(data.decode())))
    db.close()
    return output_data

def read(token):
    """
    reads data associated with a session with the token.
    """
    db = plyvel.DB('data/token_db', create_if_missing=True)
    raw_data = db.get(token.encode())
    if raw_data == None:
        return False
    data = json.loads(raw_data.decode())
    db.close()
    return data

def write(token, data):
    """
    creates/modifies data session data and
    associates it with a unique token
    """
    db = plyvel.DB('data/token_db', create_if_missing=True)
    db.put(token.encode(), json.dumps(data).encode())
    db.close()

def delete(token):
    """
    delete a session, thus revoking access.
    """
    db = plyvel.DB('data/token_db', create_if_missing=True)
    db.delete(token.encode())
    db.close()

def deactivate(token):
    """
    marks a token as revoked, does not delete.
    """
    data = read(token)
    if data == False:
        return False
    data['active'] = False
    db = plyvel.DB('data/token_db', create_if_missing=True)
    db.put(token.encode(), json.dumps(data).encode())
    db.close()
    tokens = user_db_indexer.get_by_username(data['username'])['tokens']
    tokens.remove(token)
    user_db_indexer.write_by_username(data['username'], {"tokens": tokens})

def activate(token):
    """
    marks an existing revoked token as active and allows access.
    """
    data = read(token)
    if data == False:
        return False
    data['active'] = True
    db = plyvel.DB('data/token_db', create_if_missing=True)
    db.put(token.encode(), json.dumps(data).encode())
    db.close()

if __name__ == '__main__':
    for token, data in list_tokens():
        print(token, data)
        # delete(token)
    print()
