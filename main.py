import flask
import random
import plyvel
import json
import time
import token_db_manager
import secrets
import auth_db_manager
import index_db_manager

app = flask.Flask(__name__)

############################## Base Functions ##############################
def response(success, data):
    if success == True:
        return {"success": True, "data": data}
    elif success == False:
        return {"success": False, "error": data}

def get_user_data(token):
    username = index_db_manager.get_by_token(token)
    if username == False:
        return False
    username = username['username']
    user_data = auth_db_manager.read_user_db(username)
    user_data['username'] = username
    if user_data == False:
        return False
    return user_data

def get_test_metadata(test_id):
    with open('data/test_db/test_metadata.json') as f:
        data = json.loads(f.read())
    return data[test_id]

def load_test_data(test_id):
    with open(f'data/test_db/prod_data/{test_id}.json') as f:
        data = json.loads(f.read())
    for que in data:
        for i, opt in enumerate(data[que]['options']):
            opt['id'] = i
    return data

def ctestdb_update(token, data):
    db = plyvel.DB('data/ctestdb', create_if_missing=True)
    db.put(token.encode(), json.dumps(data).encode())
    db.close()

def ctestdb_get(token):
    db = plyvel.DB('data/ctestdb', create_if_missing=True)
    data = db.get(token.encode())
    if data == None:
        return False
    data = json.loads(data.decode())
    db.close()
    return data

def ctestdb_exit(token):
    db = plyvel.DB('data/ctestdb', create_if_missing=True)
    db.delete(token.encode())
    db.close()

def get_que(test_id, difficulty):
    with open(f'data/test_db/prod_data/{test_id}.json') as f:
        data = json.loads(f.read())
    processed_data = {}
    for que in data:
        try:
            data[que]['difficulty']
            processed_data[data[que]['difficulty']]
        except KeyError:
            processed_data[data[que]['difficulty']] = []
        data[que]['id'] = que
        processed_data[data[que]['difficulty']].append(data[que])
    if processed_data[difficulty] == []:
        return False
    selected_que = random.choice(processed_data[difficulty])
    return selected_que

def get_new_que(test_id, difficulty, finished_ids):
    with open(f'data/test_db/prod_data/{test_id}.json') as f:
        data = json.loads(f.read())
    processed_data = {}
    for que in data:
        try:
            processed_data[data[que]['difficulty']]
        except KeyError:
            processed_data[data[que]['difficulty']] = []
        data[que]['id'] = que
        processed_data[data[que]['difficulty']].append(data[que])
    if processed_data[difficulty] == []:
        return False
    from_ids = [que['id'] for que in processed_data[difficulty]]
    for que in finished_ids:
        try:
            from_ids.remove(que)
        except ValueError:
            pass
    if from_ids == []:
        return False
    while True:
        selected_que = random.choice(processed_data[difficulty])
        if selected_que['id'] not in finished_ids:
            break
    return selected_que

############################## API Endpoints ##############################
######## AUTH ########
@app.route('/auth/authorize', methods=['POST'])
def auth_authorize():
    data = flask.request.json
    try:
        username = data['username']
    except KeyError:
        return response(False, "Username value missing"), 400
    try:
        password = data['password']
    except KeyError:
        return response(False, "Plaintext password value missing"), 400
    res_bool, res_text = auth_db_manager.verify_creds(username, password)
    if res_bool == False:
        return response(False, res_text)
    while True:
        token = secrets.token_urlsafe()
        if index_db_manager.get_by_token(token) == False:
            break
    user_ip = flask.request.headers.get('X-Forwarded-For')
    if user_ip == None:
        user_ip = flask.request.remote_addr
    index_user_data = index_db_manager.get_by_username(username)
    old_token = index_user_data['token']
    index_user_data['token'] = token
    index_db_manager.write_by_username(username, index_user_data)
    token_db_manager.write(token, {"username": username, "login_timestamp": time.time(), "ip_addr": user_ip, "user_agent": flask.request.headers.get('user-agent')})
    token_db_manager.delete(old_token)
    user_data = get_user_data(token)
    user_data.pop('password')
    return response(True, {'token': token, 'user_data': user_data})

@app.route('/auth/user_data')
def auth_user_data():
    req_data = flask.request.json
    try:
        token = req_data['token']
    except KeyError:
        return response(False, "Token missing"), 400
    user_data = get_user_data(token)
    if user_data == False:
        return response(False, "Token missing"), 401
    user_data.pop('password')
    return response(True, user_data)

@app.route('/auth/test', methods=['GET', 'POST'])
def auth_test():
    req_data = flask.request.json
    try:
        token = req_data['token']
    except KeyError:
        return response(False, "Token missing"), 400
    user_data = get_user_data(token)
    if user_data == False:
        return response(False, "Token missing"), 401
    return response(True, "Token verified")

@app.route('/auth/logout', methods=['POST'])
def auth_logout():
    req_data = flask.request.json
    try:
        token = req_data['token']
    except KeyError:
        return response(False, "Token missing"), 400
    user_data = get_user_data(token)
    if user_data == False:
        return response(False, "Token missing"), 401
    index_data = index_db_manager.get_by_token(token)
    index_data['token'] = "LOGGED_OUT"
    index_db_manager.write_by_token(token, index_data)
    token_db_manager.delete(token)
    return response(True, "Logged out")

######## Test Endpoints ########
@app.route('/test/new', methods=['POST'])
def test_new():
    req_data = flask.request.json
    try:
        token = req_data['token']
    except KeyError:
        return response(False, "Token missing"), 400
    user_data = get_user_data(token)
    if user_data == False:
        return response(False, "Token missing"), 401
    if 'teacher' in user_data['tags'] or 'team' in user_data['tags']:
        pass
    else:
        return response(False, "Forbidden"), 403

@app.route('/test/init', methods=['POST'])
def test_init():
    req_data = flask.request.json
    try:
        token = req_data['token']
    except KeyError:
        return response(False, "Token missing"), 400
    user_data = get_user_data(token)
    if user_data == False:
        return response(False, "Token missing"), 401
    ctest_data = ctestdb_get(token)
    try:
        test_id = req_data['test_id']
    except KeyError:
        return response(False, "test_id missing"), 401
    ctest_data = {"test_id": test_id, "que_stream": []}
    ctestdb_update(token, ctest_data)
    return response(True, get_new_que(test_id, 1, ['a51s9', 'a51s8', 'a51s6']))

@app.route('/test/status', methods=['POST'])
def test_status():
    req_data = flask.request.json
    try:
        token = req_data['token']
    except KeyError:
        return response(False, "Token missing"), 400
    user_data = get_user_data(token)
    if user_data == False:
        return response(False, "Token missing"), 401
    ctest_data = ctestdb_get(token)
    if ctest_data == False:
        return response(True, False)
    else:
        return response(True, ctest_data)

######## Other Endpoints ########
@app.route('/ping/', methods=['GET', 'POST'])
def ping():
    user_ip = flask.request.headers.get('X-Forwarded-For')
    if user_ip == None:
        user_ip = flask.request.remote_addr
        output = {"result": f"PONG!", "details": {"ip_addr": user_ip, "time": time.time(), "user_agent": flask.request.headers.get('user-agent')}}
        return response(True, output)

############################## Error Handlers ##############################
@app.errorhandler(400)
def e_400(e):
    return response(False, "Bad Request"), 400

@app.errorhandler(404)
def e_404(e):
    return response(False, "Endpoint not found"), 404

@app.errorhandler(405)
def e_405(e):
    return response(False, "Method not allowed"), 405

@app.errorhandler(500)
def e_500(e):
    return response(False, "Encountered an error while processing your request"), 500

@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = "*"
    response.headers['Access-Control-Allow-Methods'] = "POST, GET"
    response.headers['Access-Control-Allow-Headers'] = "Content-Type"
    return response

if __name__ == '__main__':
    app.run(debug=True, port=8443, host='0.0.0.0', ssl_context="adhoc")
