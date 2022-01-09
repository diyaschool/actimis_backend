"""
old: Authentication Database manager.
old: Holds only double-hashed passwords of users.

Authentication Manager.
Passwordless login with Google.
Handles JWT tokens.
"""

from google.oauth2 import id_token
from google.auth.transport import requests
import user_db_indexer
import re

CLIENT_ID = "18178721920-v27esm525ddg2pdmemu7i37olq9bglkq.apps.googleusercontent.com"
authorized_email_domains = ["@gmail.com", "@diyaschool.com"] # allowed email domains

def authorize_jwt(jwt_token):
    """
    Verify and extract JWT token generated by Google OAuth and received from
    the frontend.
    Check if email is valid, if yes then return the username of the email holder.
    """
    idinfo = id_token.verify_oauth2_token(
        jwt_token, requests.Request(), CLIENT_ID) # verify JWT token
    email = idinfo['email'] # get email
    # check if email is part of organization
    if re.search("@[\w.]+", email).group() not in authorized_email_domains:
        return False, "EXTERNAL_ACCOUNT", None, email # return EXTERNAL_ACCOUNT error
    user_data = user_db_indexer.get_by_email(email) # get username of email owner
    if user_data == False:
        return False, "ACCOUNT_NOT_FOUND", None, None # return error if account invalid
    return True, None, user_data['username'], email

if __name__ == '__main__':
    print(read_user_db())
