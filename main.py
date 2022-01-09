"""
This is spaghetti code.
Read/write it at your own risk.
"""

import flask
import random
import plyvel
import json
import time
import secrets
import session_db_manager
import auth_manager
import user_db_indexer
import user_db_manager

app = flask.Flask(__name__)

############################## Base Functions ##############################
def response(success, data, message=None, additional_data=None):
    """
    generate standardized response for success or failure.
    """
    if success == True:
        return_data = {"success": True}
        if data: return_data['data'] = data
        if message: return_data['message'] = message
        if additional_data: return_data['additional_data'] = additional_data
        return return_data
    elif success == False:
        return_data = {"success": False}
        if data: return_data['error'] = data
        if message: return_data['message'] = message
        if additional_data: return_data['additional_data'] = additional_data
        return return_data

def get_user_data(token):
    """
    get full user metadata from user_db_manager
    """
    user_index = user_db_indexer.get_by_token(token)
    if user_index == False:
        return False
    username = user_index['username']
    user_data = user_db_manager.user_db_get(username)
    user_data['username'] = username
    user_data['email'] = user_index['email']
    user_data['tags'] = user_index['tags']
    if user_data == False:
        return False
    return user_data

# def get_que(test_id, difficulty):
#     with open(f'data/test_db/prod_data/{test_id}.json') as f:
#         data = json.loads(f.read())
#     processed_data = {}
#     for que in data:
#         try:
#             data[que]['difficulty']
#             processed_data[data[que]['difficulty']]
#         except KeyError:
#             processed_data[data[que]['difficulty']] = []
#         data[que]['id'] = que
#         processed_data[data[que]['difficulty']].append(data[que])
#     if processed_data[difficulty] == []:
#         return False
#     selected_que = random.choice(processed_data[difficulty])
#     return selected_que
#
# def get_new_que(test_id, difficulty, finished_ids):
#     with open(f'data/test_db/prod_data/{test_id}.json') as f:
#         data = json.loads(f.read())
#     processed_data = {}
#     for que in data:
#         try:
#             processed_data[data[que]['difficulty']]
#         except KeyError:
#             processed_data[data[que]['difficulty']] = []
#         data[que]['id'] = que
#         processed_data[data[que]['difficulty']].append(data[que])
#     if processed_data[difficulty] == []:
#         return False
#     from_ids = [que['id'] for que in processed_data[difficulty]]
#     for que in finished_ids:
#         try:
#             from_ids.remove(que)
#         except ValueError:
#             pass
#     if from_ids == []:
#         return False
#     while True:
#         selected_que = random.choice(processed_data[difficulty])
#         if selected_que['id'] not in finished_ids:
#             break
#     return selected_que

def authorize_request(req_data):
    """
    check if token in req_data is valid and authorized.
    """
    try:
        token = req_data['token']
    except KeyError:
        return False, "TOKEN_MISSING", "Token missing", 400
    except TypeError:
        return False, "BAD_REQUEST", "Bad request, use application/json", 400
    token_data = session_db_manager.read(token)
    if token_data == False:
        return False, "UNAUTHORIZED", "API token invalid", 401
    elif token_data.get('active') == None:
        pass
    elif token_data.get('active') != True:
        return False, "UNAUTHORIZED", "API token deactivated", 401
    return True, "AUTHORIZED"

############################## API Endpoints ##############################
######## AUTH ########
@app.route('/auth/authorize/', methods=['POST'])
def auth_authorize():
    """
    auth endpoint for creating a new session with JWT token
    from Google OAuth Sign In button
    """
    data = flask.request.json # get JSON data from frontend
    if data == None:
        return response(False, "BAD_REQUEST", "Use application/json"), 400
    try:
        jwt_token = data['jwt_token'] # receive JWT token
    except KeyError:
        # return error if jwt_token is missing
        return response(False, "JWT_TOKEN_MISSING", "JWT token missing"), 400
    # authorize jwt_token, check if valid, extract email and lookup username
    res_bool, res_code, username, email_address = auth_manager.authorize_jwt(jwt_token)
    if res_bool == False:
        res_msg = None
        if res_code == "AUTH_ERROR": # unkown error, not implemented yet
            res_msg = "Authentication error, try again"
        elif res_code == "EXTERNAL_ACCOUNT": # if email doesnt belong to org
            res_msg = "This is an external account, make sure the email ends in @diyaschool.com"
        elif res_code == "ACCOUNT_NOT_FOUND": # if no account is linked to email
            res_msg = "This account does not exist, please use another one"
        return response(False, res_code, res_msg, {"email": email_address}), 403
    while True:
        token = secrets.token_urlsafe(32) # generate new token
        if user_db_indexer.get_by_token(token) == False:
            break # make sure token is not repeated (highly unlikely will ever occur)
    user_ip = flask.request.headers.get('X-Forwarded-For') # get IP from Cloudflare
    if user_ip == None:
        user_ip = flask.request.remote_addr # get connecting IP directly ip
    index_user_data = user_db_indexer.get_by_username(username)
    index_user_data['tokens'].append(token) # add token to user indexer
    user_db_indexer.write_by_username(username, index_user_data)
    session_db_manager.write(token, {"username": username, # add token to session manager
        "login_timestamp": time.time(), "ip_addr": user_ip,
        "user_agent": flask.request.headers.get('user-agent')})
    user_data = get_user_data(token)
    return response(True, {'token': token, 'user_data': user_data}) # return success with user_data

@app.route('/auth/test/', methods=['GET', 'POST'])
def auth_test():
    """
    test endpoint to check if token is valid and authorized
    """
    req_data = flask.request.json
    auth_resp = authorize_request(req_data)
    if auth_resp[0] == False:
        return response(False, auth_resp[1], auth_resp[2]), auth_resp[3]
    return response(True, None, "Token verified")

@app.route('/auth/user_data/')
def auth_user_data():
    """
    user_data of authorized token holder.
    """
    req_data = flask.request.json
    auth_resp = authorize_request(req_data)
    if auth_resp[0] == False:
        return response(auth_resp[0], auth_resp[1], auth_resp[2]), auth_resp[3]
    user_data = get_user_data(req_data['token'])
    return response(True, user_data)

@app.route('/auth/logout/', methods=['POST'])
def auth_logout():
    """
    DEACTIVATES token. Can be re-activated later, without appearing on indexer.
    (could be exploited by admins for personal data, if any exists)
    """
    req_data = flask.request.json
    auth_resp = authorize_request(req_data)
    if auth_resp[0] == False:
        return response(auth_resp[0], auth_resp[1], auth_resp[2]), auth_resp[3]
    token = req_data['token']
    index_data = user_db_indexer.get_by_token(token)
    index_data['token'].remove(token) # removes token from indexer (used for frontend sessions page)
    user_db_indexer.write_by_token(token, index_data)
    session_db_manager.deactivate(token) # deactivates token in session db (only backend)
    return response(True, "LOGGED_OUT", "Logged out")

######## Test (Assessment) Endpoints ########
##### Classic MCQ #####
@app.route('/test/classic_mcq/user_instance/new/', methods=["POST"])
def classic_mcq_new_instance():
    req_data = flask.request.json
    auth_resp = authorize_request(req_data)
    if auth_resp[0] == False:
        return response(auth_resp[0], auth_resp[1], auth_resp[2]), auth_resp[3]
    user_data = get_user_data(req_data['token'])

    with open("data/test_db/classic_mcq/user_instances/") as f:
        pass

# @app.route('/test/new/', methods=['POST'])
# def test_new():
#     req_data = flask.request.json
#     auth_resp = authorize_request(req_data)
#     if auth_resp[0] == False:
#         return response(auth_resp[0], auth_resp[1], auth_resp[2]), auth_resp[3]
#     user_data = get_user_data(req_data['token'])
#     if user_data == False:
#         return response(False, "TOKEN_MISSING", "Token missing"), 401
#     if 'teacher' in user_data['tags'] or 'team' in user_data['tags']:
#         pass
#     else:
#         return response(False, "FORBIDDEN", "Forbidden"), 403
#
# @app.route('/test/init/', methods=['POST'])
# def test_init():
#     req_data = flask.request.json
#     auth_resp = authorize_request(req_data)
#     if auth_resp[0] == False:
#         return response(auth_resp[0], auth_resp[1], auth_resp[2]), auth_resp[3]
#     token = req_data['token']
#     ctest_data = ctestdb_get(token)
#     try:
#         test_id = req_data['test_id']
#     except KeyError:
#         return response(False, "TEST_ID_MISSING", "test_id missing"), 401
#     ctest_data = {"test_id": test_id, "que_stream": []}
#     ctestdb_update(token, ctest_data)
#     return response(True, get_new_que(test_id, 1, ['a51s9', 'a51s8', 'a51s6']))

######## Other Endpoints ########
@app.route('/ping/', methods=['GET', 'POST'])
def ping():
    """
    Does nothing but respond to a ping.
    Returns PONG with IP ad user agent string.
    """
    user_ip = flask.request.headers.get('X-Forwarded-For')
    if user_ip == None:
        user_ip = flask.request.remote_addr
    output = {
        "result": f"PONG!",
        "client_info":
            {"ip_addr": user_ip, "time": time.time(),
            "user_agent": flask.request.headers.get('user-agent')}}
    return response(True, output)

############################## Error Handlers ##############################
@app.errorhandler(400)
def e_400(e):
    return response(False, "BAD_REQUEST", "Bad Request"), 400

@app.errorhandler(404)
def e_404(e):
    return response(False, "NOT_FOUND", "Endpoint not found"), 404

@app.errorhandler(405)
def e_405(e):
    return response(False, "INVALID_METHOD", "Method not allowed"), 405

@app.errorhandler(500)
def e_500(e):
    return response(False, "SERVER_ERROR", "Encountered an error while processing your request"), 500

@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = "https://test.actimis.ml"
    response.headers['Access-Control-Allow-Methods'] = "POST, GET"
    response.headers['Access-Control-Allow-Headers'] = "Content-Type"
    return response

if __name__ == '__main__':
    # run in development mode
    app.run(debug=True, port=8441, host='0.0.0.0', ssl_context="adhoc")
