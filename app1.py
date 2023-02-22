from flask import Flask, g,redirect,render_template
app = Flask(__name__)
import os

app.secret_key = '301a641e20f979308c4141a69dff0ec6exit'
app.config['OIDC_CLIENT_SECRETS'] = 'client_secrets.json'
app.config['OIDC_COOKIE_SECURE'] = False
from flask_oidc import OpenIDConnect
oidc = OpenIDConnect(app)

photos = os.path.join('static','photos')
app.config['UPLOAD_FOLDER'] = photos

@app.route('/')
def welcome():
    print(oidc.user_loggedin)
    # logo = os.path.join(app.config['UPLOAD_FOLDER'],'linkedin-signin.png')
    return "<p>Hello, World!</p>"

@app.route('/login')
@oidc.require_login
def loginwithlinkdin():
    print(oidc.user_loggedin) #this will print true if the user is logged in
    name = oidc.user_getfield('name') #getting name from linkedin
    email = oidc.user_getfield('email') #getting email from linkedin
    msg= "welcome "+name+" your email is "+ email + '<a href="/logout">Logout</a>'
    return (msg)
    
@app.route('/logout')
def logout():
    """Performs local logout by removing the session cookie."""
    oidc.logout() 
    return 'Hi, you have been logged out! <a href="/">Return</a>'


if __name__ == "__main__":
     app.run(debug=True)