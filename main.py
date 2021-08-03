import flask
import time
import token_db_manager
import secrets
import auth_db_manager
import index_db_manager

app = flask.Flask(__name__)

############### Base Functions ###############
def response(success, data):
    if success == True:
        return {"success": True, "data": data}
    elif success == False:
        return {"success": False, "error": data}

############### API Endpoints ###############
######## AUTH ########
@app.route('/auth/authorize', methods=['POST'])
def auth_authorize():
    data = flask.request.json
    try:
        username = data['username']
    except KeyError:
        return response(False, "Username value missing")
    try:
        password = data['password']
    except KeyError:
        return response(False, "Plaintext password value missing")
    res_bool, res_text = auth_db_manager.verify_creds(username, password)
    if res_bool == False:
        return res_text
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
    return response(True, data)

######## API Endpoints ########
@app.route('/ping/', methods=['GET', 'POST'])
def ping():
    user_ip = flask.request.headers.get('X-Forwarded-For')
    if user_ip == None:
        user_ip = flask.request.remote_addr
    output = f'''
    PONG!<br><br>

    {flask.request.method} {flask.request.path}<br>
    IP: {user_ip}<br>
    Time: {time.time()}<br>
    User_Agent: {flask.request.headers.get('user-agent')}
    '''
    return output

############### Error Handlers ###############
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
