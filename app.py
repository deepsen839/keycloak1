import json
import logging
import os
from python_graphql_client import GraphqlClient
import requests
from flask import Flask, g,render_template,request,flash,jsonify,session
from flask_oidc import OpenIDConnect
import requests
from graphene_file_upload.flask import FileUploadGraphQLView
logging.basicConfig(level=logging.DEBUG)
from schema import schema
from models import Todo, session,User
from forms import TodoForm
from helpers import file_path
import stripe
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

from flask_session import Session
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'dev.db')
db = SQLAlchemy(app)


stripe_keys = {
    "secret_key": "sk_test_51Mf34CSGSzfJLk4L3mhigTAemWqxDhXQB8YbeGn1GfsvUGOjQM9AC2XAxNv1ssGHNT7q7zKxqELAvCleZdN7pIwy005iYhSmZk",
    "publishable_key": "pk_test_51Mf34CSGSzfJLk4LV47evTsHxcxQ1bHSHtoVQVi6jizXJjQ9skqLtdKnyFLRp1TFNku5pz32x8lDkF8xNgXBBxMy00kaz7Du6W",
}
stripe.api_key = stripe_keys["secret_key"]
userid=''
stripe_id=''
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
client = GraphqlClient(endpoint="http://localhost:5000/graphq", verify=True)

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

    check_credential()
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
        methods=['GET',"POST"],
    )
)
@app.route("/addtodo",methods=('GET', 'POST'))
@oidc.require_login
def addtodo():
    global stripe_id
    check_credential()
    variables=""
    form = TodoForm()
    if request.method == 'POST':
        if form.validate_on_submit():
 
            query = """mutation ($file:Upload,$title:String,$description:String){addTodo(title:$title,description:$description,file1:$file){
    ok,todo{
    id
    }
    }
    }"""
            if stripe_id:
                file2 = request.files['file1']
                filename = request.files['file1'].filename
                file2.save(os.path.join(file_path,filename))
            else:
                filename = ''
            variables = {'file':filename,'title':request.form.get('title'),'description':request.form.get('description')}
            result = client.execute(query=query,variables=variables)
          
            flash(result, 'success')
    return render_template("todo_create.html",form=form)

@app.route("/listtodo",methods=('GET', 'POST'))
@oidc.require_login
def listtodo():
    check_credential()
    query ="""query {userNotes{
  title,description,path,id
}
      }"""
    result = client.execute(query=query)
    # flash(result, 'success')
    return render_template("todo_list.html",result=result)

@app.route("/findbyid/<int:id>/",methods=('GET', 'POST'))
@oidc.require_login
def findbyid(id):
    global stripe_id
    check_credential()

    query ="""query($id:Int) {findTodo(id:$id){
  title,description,path,id
}
      }"""
    variables = {'id':id}

    result = client.execute(query=query,variables=variables)
    form = TodoForm(title=result["data"]["findTodo"]["title"],
                    description=result["data"]["findTodo"]["description"],
                    
                    )
    if request.method=='POST':
        if form.validate_on_submit():
            query_update = """mutation($file:Upload,$id:Int,$title:String,$description:String) {updateTodo(todoId:$id,title:$title,description:$description,file1:$file){
ok

}
      }"""

            if stripe_id:
                file2 = request.files['file1']
                filename = request.files['file1'].filename
                file2.save(os.path.join(file_path,filename))
            else:
                filename=''
            variables = {'file':filename,'title':request.form.get('title'),'description':request.form.get('description'),'id':id}
            result1 = client.execute(query=query_update,variables=variables)
            flash(result1, 'success')



    return render_template("todo_edit.html",form=form,result=result)



@app.route("/delete_record/<int:id>/",methods=('GET', 'POST'))
@oidc.require_login
def delete_record(id):
    check_credential()
    query ="""mutation($id:Int){deleteTodo(todoId:$id){
ok

}
      }"""

    variables = {'id':id}
    result = client.execute(query=query,variables=variables)
    flash("Record Deleted successfully", 'success')

def check_credential():
    global userid
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])

    username = info.get('preferred_username')
    email = info.get('email')
    user_id = info.get('sub')
    userid = user_id
    
    user = db.session.query(User).filter_by(user_id=user_id).first()
    if user is None:
        user_record = User(email=email,user_id=user_id,stripe_sessionid='')
        db.session.add(user_record)
        db.session.commit()


@app.route("/create-checkout-session")
def create_checkout_session():
    domain_url = "http://127.0.0.1:5000/"
    stripe.api_key = stripe_keys["secret_key"]

    try:
        # Create new Checkout Session for the order
        # Other optional params include:
        # [billing_address_collection] - to display billing address details on the page
        # [customer] - if you have an existing Stripe Customer ID
        # [payment_intent_data] - capture the payment later
        # [customer_email] - prefill the email input in the form
        # For full details see https://stripe.com/docs/api/checkout/sessions/create

        # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
        checkout_session = stripe.checkout.Session.create(
            success_url=domain_url + "success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=domain_url + "cancelled",
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
    'price_data': {
      'currency': 'usd',
      'unit_amount': 2000,
      'product_data': {
        'name': 'T-shirt',
        'description': 'Comfortable cotton t-shirt',
      },
    },
    'quantity': 1,
  }],
        )
        return jsonify({"sessionId": checkout_session["id"]})
    except Exception as e:
        return jsonify(error=str(e)), 403


@app.route("/success")
def success():
    global stripe_id
    session_id = request.args.get('session_id')
    
    user = db.session.query(User).filter_by(user_id=userid).first()
    if user:
        stripe_id = session_id
        user.stripe_sessionid = session_id
        db.session.add(user)
        db.session.commit()
    return render_template("success.html")


@app.route("/cancelled")
def cancelled():
    return render_template("cancelled.html")

@app.route("/config")
def get_publishable_key():
    stripe_config = {"publicKey": stripe_keys["publishable_key"]}
    return jsonify(stripe_config)


if __name__ == '__main__':
    app.run()