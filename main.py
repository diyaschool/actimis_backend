import flask
import hashlib
import json
import db_manager

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
    return response(True, data)

############### Error Handlers ###############
@app.errorhandler(400)
def e_400(e):
    return response(False, "Bad Request"), 400

@app.errorhandler(404)
def e_404(e):
    return response(False, "Endpoint not found"), 404

@app.errorhandler(405)
def e_405(e):1
    return response(False, "Method not allowed"), 405

@app.errorhandler(500)
def e_500(e):
    return response(False, "Encountered an error while processing your request"), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
