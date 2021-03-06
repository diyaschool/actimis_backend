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
import user_manager
import test_manager
import os
import shutil

app = flask.Flask(__name__)

############################## Base Functions ##############################
def response(success, data=None, message=None, additional_data=None):
    """
    generate standardized response for success or failure.
    """
    if success == True:
        return_data = {"success": True}
        if data!=None: return_data['data'] = data
        if message!=None: return_data['message'] = message
        if additional_data!=None: return_data['additional_data'] = additional_data
        return return_data
    elif success == False:
        return_data = {"success": False}
        if data!=None: return_data['error'] = data
        if message!=None: return_data['message'] = message
        if additional_data!=None: return_data['additional_data'] = additional_data
        return return_data

def get_user_data(identifier, use_username=False):
    """
    get full user metadata from user_manager
    """
    if use_username != True:
        token = identifier
        user_index = user_db_indexer.get_by_token(token)
    else:
        username = identifier
        user_index = user_db_indexer.get_by_username(username)
    if user_index == False:
        return False
    username = user_index['username']
    user_data = user_manager.get(username)
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
## Attendee ##
@app.route('/test/classic_mcq/user_session/new/', methods=["POST"])
def classic_mcq_new_session():
    """
    Creates a new "session" for a test (by attendee).
    The test will be conducted with reference to this new session and NOT the live config by the teacher.
    This is to prevent conflicts between the configurations, question sequence, answers, etc.

    This function makes a copy of the live test data along with its metadata into a config file with a session name.
    Then it adds the session name to the user data of the attendee.
    """
    req_data = flask.request.json
    auth_resp = authorize_request(req_data)
    if auth_resp[0] == False:
        return response(False, auth_resp[1], auth_resp[2]), auth_resp[3]
    if req_data.get('test_id') == None:
        return response(False, "TEST_ID_MISSING", "test_id missing"), 400
    user_data = get_user_data(req_data['token'])
    username = user_data['username']
    test_id = req_data['test_id']
    if user_data['test_data']['classic_mcq']['user_sessions'].get(test_id) != None:
        return response(False, "USER_SESSION_EXISTS", "A session for this test already exists"), 409
    test_metadata = test_manager.classic_mcq.get_test_metadata(test_id)
    if [i for i in user_data['tags'] if i in test_metadata['tags']] == []:
        return response(False, "UNAUTHORIZED", "This test is not for you")
    user_session_id = secrets.token_hex(10)
    user_manager.modify(username, {"test_data": {"classic_mcq": {"user_sessions": {test_id: {"session_id": user_session_id}}}}})
    try:
        with open(f"data/test_db/classic_mcq/test_data/{test_id}/data.json") as f:
            test_data = json.loads(f.read())
    except FileNotFoundError:
        return response(False, "TEST_NOT_FOUND", "No test exists with the test_id specified")
    test_metadata.pop("sharing")
    test_flow = list(test_data['questions'].keys())
    if test_metadata["control_type"] == "random":
        random.shuffle(test_flow)
    with open(f"data/test_db/classic_mcq/user_sessions/{user_session_id}.json", "w") as f:
        f.write(json.dumps({
            "test_data": test_data,
            "test_metadata": test_metadata,
            "test_id": test_id,
            "username": username,
            "journal": {},
            "test_flow": test_flow
            }))
    return response(True, {"user_session_id": user_session_id})

@app.route('/test/classic_mcq/user_session/delete/', methods=['POST'])
def classic_mcq_delete_session():
    """
    Deletes the user session created by the attendee for a test.
    The user session ID is present in the user data of the attendee.
    """
    req_data = flask.request.json
    auth_resp = authorize_request(req_data)
    if auth_resp[0] == False:
        return response(False, auth_resp[1], auth_resp[2]), auth_resp[3]
    test_id = req_data.get('test_id')
    if test_id == None:
        return response(False, "TEST_ID_MISSING", "test_id missing"), 400
    user_data = get_user_data(req_data['token'])
    username = user_data['username']
    user_session = user_data['test_data']['classic_mcq']['user_sessions'].get(test_id)
    if user_session == None:
        return response(False, "SESSION_NOT_FOUND", "No session was found for this test"), 404
    user_session_id = user_session['session_id']
    user_data['test_data']['classic_mcq']['user_sessions'].pop(test_id)
    os.remove(f"data/test_db/classic_mcq/user_sessions/{user_session_id}.json")
    user_manager.put(username, user_data)
    return response(True, "SESSION_REMOVED")

@app.route('/test/classic_mcq/user_session/get/')
def classic_mcq_get_session():
    """
    Get the user session ID and details of a test created by the attendee.
    """
    req_data = flask.request.json
    auth_resp = authorize_request(req_data)
    if auth_resp[0] == False:
        return response(False, auth_resp[1], auth_resp[2]), auth_resp[3]
    test_id = req_data.get('test_id')
    if test_id == None:
        return response(False, "TEST_ID_MISSING", "test_id missing"), 400
    user_data = get_user_data(req_data['token'])
    username = user_data['username']
    user_session = user_data['test_data']['classic_mcq']['user_sessions'].get(test_id)
    if user_session == None:
        return response(False, "SESSION_NOT_FOUND", "No session was found for this test"), 404
    user_session_id = user_session['session_id']
    user_session = test_manager.classic_mcq.get_user_session(user_session_id)
    test_metadata = user_session['test_metadata']
    return_data = {
        "test_id": test_id,
        "session_id": user_session_id,
        "title": test_metadata['title'],
        "subject": test_metadata['subject'],
        "creator": {
            "username": test_metadata['creator'],
            "name": get_user_data(test_metadata['creator'], True)['name']
            },
        "control_type": test_metadata['control_type'],
        }
    return response(True, return_data)

@app.route('/test/classic_mcq/user_session/list/')
def classic_mcq_session_list():
    """
    List user sessions created for the user accross all tests
    """
    req_data = flask.request.json
    auth_resp = authorize_request(req_data)
    if auth_resp[0] == False:
        return response(False, auth_resp[1], auth_resp[2]), auth_resp[3]
    user_data = get_user_data(req_data['token'])
    username = user_data['username']
    user_session_list = []
    for test_id in user_data['test_data']['classic_mcq']['user_sessions']:
        session_id = user_data['test_data']['classic_mcq']['user_sessions'][test_id]['session_id']
        user_session = test_manager.classic_mcq.get_user_session(session_id)
        test_metadata = user_session['test_metadata']
        user_session_list.append({
            "test_id": test_id,
            "session_id": session_id,
            "title": test_metadata['title'],
            "subject": test_metadata['subject'],
            "creator": {
                "username": test_metadata['creator'],
                "name": get_user_data(test_metadata['creator'], True)['name']
                },
            "control_type": test_metadata['control_type'],
            })
    return response(True, {"user_session_list": user_session_list})

@app.route('/test/classic_mcq/attempt/get/')
def classic_mcq_attempt_get():
    """
    Get details of a specific test's user session
    """
    req_data = flask.request.json
    auth_resp = authorize_request(req_data)
    if auth_resp[0] == False:
        return response(False, auth_resp[1], auth_resp[2]), auth_resp[3]
    test_id = req_data.get('test_id')
    if test_id == None:
        return response(False, "TEST_ID_MISSING", "test_id missing"), 400
    user_data = get_user_data(req_data['token'])
    username = user_data['username']
    _user_session = user_data['test_data']['classic_mcq']['user_sessions'].get(test_id)
    if _user_session == None:
        return response(False, "SESSION_NOT_FOUND", "No session was found for this test"), 404
    session_id = _user_session['session_id']
    session_data = test_manager.classic_mcq.get_user_session(session_id)
    return_data = {}
    return_data['id'] = session_data['test_flow'][0]
    question_id = req_data.get('question_id')
    if session_data['test_metadata']['control_type'] != "user" and question_id != None:
        return response(False, "UNAUTHORIZED", "This test does not allow choosing questions"), 401
    question = session_data['test_data']['questions'][session_data['test_flow'][0]]
    if question_id != None and session_data['test_metadata']['control_type'] == "user":
        if question_id in list(session_data['test_data']['questions'].keys()):
            question = session_data['test_data']['questions'][question_id]
        else:
            return response(False, "QUESTION_NOT_FOUND", "Question not found"), 400
    return_data['question'] = question
    if question.get('parent_context') != None:
        return_data['context'] = session_data['test_data']['contexts'][question.get('parent_context')]
    return response(True, return_data)

@app.route('/test/classic_mcq/attempt/que_submit/', methods=['POST'])
def classic_mcq_attempt_que_submit():
    """
    Submit answer to A QUESTION for an mcq only test.
    Reacts according to control_type.
    """
    req_data = flask.request.json
    auth_resp = authorize_request(req_data)
    if auth_resp[0] == False:
        return response(False, auth_resp[1], auth_resp[2]), auth_resp[3]
    test_id = req_data.get('test_id')
    if test_id == None:
        return response(False, "TEST_ID_MISSING", "test_id missing"), 400
    answer_id = req_data.get('answer_id')
    if answer_id == None:
        return response(False, "ANSWER_ID_MISSING", "answer_id missing"), 400
    user_data = get_user_data(req_data['token'])
    username = user_data['username']
    _user_session = user_data['test_data']['classic_mcq']['user_sessions'].get(test_id)
    if _user_session == None:
        return response(False, "SESSION_NOT_FOUND", "No session was found for this test"), 404
    session_id = _user_session['session_id']
    session_data = test_manager.classic_mcq.get_user_session(session_id)
    question_id = req_data.get('question_id')
    if len(session_data['test_flow']) == 0:
        # TODO: ADD SUBMIT FEATURE HERE
        return response(True, "TEST_COMPLETED")
    if session_data['test_metadata']['control_type'] == "user" and question_id == None:
        return response(False, "QUESTION_ID_MISSING", "question_id missing"), 400
    elif session_data['test_metadata']['control_type'] != "user" and question_id != None:
        return response(False, "UNAUTHORIZED", "This test does not allow choosing questions"), 401
    elif session_data['test_metadata']['control_type'] != "user" and question_id == None:
        question_id = session_data['test_flow'][0]
    if question_id in range(len(session_data['test_data']['questions'])):
        question_data = {"question": session_data['test_data']['questions'][question_id]}
    else:
        return response(False, "QUESTION_NOT_FOUND", "Question out of range"), 400
    if answer_id not in range(len(question_data['question']['o'])):
        return response(False, "ANSWER_INVALID", "Answer out of range"), 400
    question_data['answer_id'] = answer_id
    session_data['journal'][str(question_id)] = question_data
    session_data['test_flow'].pop(0)
    test_manager.classic_mcq.write_user_session(session_id, session_data)
    return response(True, "SUBMITTED_ANSWER")

## Teacher ##
@app.route('/test/classic_mcq/directory/create/', methods=['POST'])
def directory_classic_mcq_create():
    """
    Create a new and empty test with no configurations.
    """
    req_data = flask.request.json
    auth_resp = authorize_request(req_data)
    if auth_resp[0] == False:
        return response(auth_resp[0], auth_resp[1], auth_resp[2]), auth_resp[3]
    user_data = get_user_data(req_data['token'])
    while True:
        test_id = secrets.token_hex(3)
        if test_manager.classic_mcq.get_test_metadata(test_id) == False:
            break
    test_title = req_data.get('test_title')
    if test_title == None:
        return response(False, "TEST_TITLE_MISSING", "test_title missing"), 400
    test_subject = req_data.get('test_subject')
    if test_subject == None:
        return response(False, "TEST_SUBJECT_MISSING", "test_subject missing"), 400
    test_tags = req_data.get('test_tags')
    if test_tags == None:
        return response(False, "TEST_TAGS_MISSING", "test_tags missing"), 400
    test_control_type = req_data.get('test_control_type')
    if test_control_type == None:
        return response(False, "TEST_CONTROL_TYPE_MISSING", "test_control_type missing"), 400
    user_data['created_tests']['classic_mcq'][test_id] = {
        "title": test_title,
        "subject": test_subject,
        "tags": test_tags,
        "control_type": test_control_type
        }
    os.mkdir(f'data/test_db/classic_mcq/test_data/{test_id}/')
    with open(f'data/test_db/classic_mcq/test_data/{test_id}/data.json', 'w') as f:
        f.write("{}")
    user_manager.modify(user_data['username'], user_data)
    test_metadata = {
        "test_id": test_id,
        "title": test_title,
        "subject": test_subject,
        "tags": test_tags,
        "creator": user_data['username'],
        "sharing": {},
        "control_type": test_control_type
        }
    test_manager.classic_mcq.write_test_metadata(test_id, test_metadata)
    return response(True, test_metadata)

@app.route('/test/classic_mcq/directory/list/')
def directory_classic_mcq_list():
    """
    Lists all the tests created by the user
    """
    req_data = flask.request.json
    auth_resp = authorize_request(req_data)
    if auth_resp[0] == False:
        return response(auth_resp[0], auth_resp[1], auth_resp[2]), auth_resp[3]
    user_data = get_user_data(req_data['token'])
    return_data = []
    for test_id in list(user_data['created_tests']['classic_mcq'].keys()):
        test_metadata = user_data['created_tests']['classic_mcq'][test_id]
        test_metadata['test_id'] = test_id
        return_data.append(test_metadata)
    return response(True, return_data)

@app.route('/test/classic_mcq/directory/delete/', methods=['POST'])
def directory_classic_mcq_delete():
    """
    Deletes the specified test created by the user.
    """
    req_data = flask.request.json
    auth_resp = authorize_request(req_data)
    if auth_resp[0] == False:
        return response(auth_resp[0], auth_resp[1], auth_resp[2]), auth_resp[3]
    user_data = get_user_data(req_data['token'])
    test_id = req_data.get('test_id')
    if test_id == None:
        return response(False, "TEST_ID_MISSING", "test_id missing"), 400
    if user_data['created_tests']['classic_mcq'].get(test_id) == None:
        return response(False, "UNAUTHORIZED", "Only the creator of a test can delete it."), 401
    shutil.rmtree(f'data/test_db/classic_mcq/test_data/{test_id}/')
    test_manager.classic_mcq.delete_test_metadata(test_id)
    user_data['created_tests']['classic_mcq'].pop(test_id)
    user_manager.put(user_data['username'], user_data)
    return response(True)

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

############################## Worker Handlers ##############################
@app.before_request
def before_request():
    flask.g.process_init_time = time.time()

@app.after_request
def after_request(response):
    process_time = time.time()-flask.g.process_init_time
    data = response.get_json()
    data['pt_ms'] = round(process_time*1000, 1)
    response.set_data(json.dumps(data))
    response.headers['Access-Control-Allow-Origin'] = "https://test.actimis.ml"
    response.headers['Access-Control-Allow-Methods'] = "POST, GET"
    response.headers['Access-Control-Allow-Headers'] = "Content-Type"
    return response

if __name__ == '__main__':
    # run in development mode
    app.run(debug=True, port=8441, host='0.0.0.0', ssl_context="adhoc")
