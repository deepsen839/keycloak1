import json
import logging

from flask import Flask, g
from flask_oidc import OpenIDConnect
import requests
from graphene_file_upload.flask import FileUploadGraphQLView
logging.basicConfig(level=logging.DEBUG)
from schema import schema
from models import Todo, session
app = Flask(__name__)
app.config.update({
    'SECRET_KEY': '0497cdafb931478456983f4dd82ce46a',
    'TESTING': True,
    'DEBUG': True,
    'OIDC_CLIENT_SECRETS': 'client_secrets.json',
    'OIDC_ID_TOKEN_COOKIE_SECURE': False,
    'OIDC_REQUIRE_VERIFIED_EMAIL': False,
    'OIDC_USER_INFO_ENABLED': True,
    'OIDC_OPENID_REALM': 'flask-demo',
    'OIDC_SCOPES': ['openid', 'email', 'profile'],
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post'
})

oidc = OpenIDConnect(app)


@app.route('/')
def hello_world():
    if oidc.user_loggedin:
        return ('Hello, %s, <a href="/private">See private</a> '
                '<a href="/logout">Log out</a>') % \
            oidc.user_getfield('preferred_username')
    else:
        return 'Welcome anonymous, <a href="/private">Log in</a>'


@app.route('/private')
@oidc.require_login
def hello_me():
    greeting = ''
    headers =''
    """Example for protected endpoint that extracts private information from the OpenID Connect id_token.
       Uses the accompanied access_token to access a backend service.
    """

    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

    username = info.get('preferred_username')
    email = info.get('email')
    user_id = info.get('sub')

    if user_id in oidc.credentials_store:
        try:
            from oauth2client.client import OAuth2Credentials
            access_token = OAuth2Credentials.from_json(oidc.credentials_store[user_id]).access_token
            print( 'access_token=<%s>' % access_token)
            headers = {'Authorization': 'Bearer %s' % (access_token)}
            # YOLO
            greeting = requests.get('http://localhost:8080/greeting', headers=headers).text
        except:
            print ("Could not access greeting-service")
            greeting = "Hello %s" % username
    

    return ("""%s your email is %s and your user_id is %s accesstoeken is %s!
               <ul>
                 <li><a href="/">Home</a></li>
                 <li><a href="//localhost:8080/realms/myrealm/account?referrer=flask-app&referrer_uri=http://localhost:5000/private&">Account</a></li>
                </ul>""" %
            (greeting, email, user_id,headers))


@app.route('/api', methods=['POST'])
@oidc.accept_token(require_token=True, scopes_required=['openid'])
def hello_api():
    """OAuth 2.0 protected API endpoint accessible via AccessToken"""

    return json.dumps({'hello': 'Welcome %s' % g.oidc_token_info['sub']})


@app.route('/logout',methods=['GET'])
def logout():
    """Performs local logout by removing the session cookie."""

    oidc.logout()
    return 'Hi, you have been logged out! <a href="/">Return</a>'

app.add_url_rule(
    '/graphq','index',
    view_func=FileUploadGraphQLView.as_view(
        'graphq',
        schema=schema,
        graphiql=True,
    )
)
if __name__ == '__main__':
    app.run()