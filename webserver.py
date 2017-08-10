from flask import Flask, redirect, request, abort
from os import environ
from evernote.api.client import EvernoteClient

# INSTRUCTIONS FROM EVERNOTE: http://dev.evernote.com/doc/articles/authentication.php

# ***STEP 1***: First we need our client (i.e. app) tokens:
try:
    api_key = environ["EVERNOTEKEY"]
    api_secret = environ["EVERNOTESECRET"]
except:
    raise Exception("You need an Evernote api key. Stick the key in an environment variable named EVERNOTEKEY and the secret in EVERNOTESECRET")

app = Flask(__name__)
app.config['DEBUG'] = True

# ***STEP 2***: we need to create an Evernote client instance to get the authentication information.

# Note that later we'll create a second client instance to actually interact with an authorized account:

auth_client = EvernoteClient(consumer_key=api_key,
                        consumer_secret=api_secret,
                        sandbox=True) # for production this will need to be False.

# Ok, from here I'm going to create a bunch of totally unnecessary functions that wrap the functions the evernote SDK already gives you.  The point is to make the flow a little bit more explicit by organizing it into a step 3 function, a step 4 function, etc.

# ***STEP 3***: request a temporary token when it's time to get authorization.

# At this step, you'll also set a callback url for the user. This example assumes you're running locally as a CLI, and so you'll do this on localhost.  The routes are below.

callback_url = "http://127.0.0.1:8080/oauth-callback"

def request_temporary_token(): # returns the token you need for step 2
    return auth_client.get_request_token(callback_url)

# ***STEP 4***: With that request token, you can get a webpage to send the users to in order to authorize your application.

def get_user_authorization_url(temporary_request_token):
    return auth_client.get_authorize_url(temporary_request_token)

# This is the machinery we need for our actual route---this will be where users go once the application starts, to get it all running.

# As should be clear from above, this route will ask the evernote server for a temporary token, then ask it for an authorization URL, then redirect the user to that URL to authorize our application.

# HERE I THINK THE DOCUMENTATION IS WRONG.  The authentication docs imply that there's
# only one thing returned from the request token call, viz., a token, http://dev.evernote.com/doc/articles/authentication.php and also implies that when you use the request token
# you don't need a secret.   
# however, the actual code for the SDK https://github.com/evernote/evernote-sdk-python/blob/master/lib/evernote/api/client.py seems to suggest that you need an oauth secret, acquired at this point.

# moreover, their sample application https://github.com/evernote/evernote-sdk-python/blob/master/sample/pyramid/evernote_oauth_sample/views.py#L39 takes a secret out of this and uses it later.

# I'm going to trust the sample code rather than the docs. 

# Probably the least bizarre way to handle this is to just store it all in a global.

temporary_request_token = None

oauth_secret = None

# I'm going to get my functional programmer card taken away for this nonsense.

@app.route('/authorize-evernote', methods=['GET'])
def authorize_user():
    global temporary_request_token
    tt = request_temporary_token()
    temporary_request_token = tt["oauth_token"]
    global oauth_secret
    oauth_secret = tt["oauth_token_secret"]
    authorization_url = get_user_authorization_url(tt) # you have to pass the whole dictionary (token and secret) in here.
    return redirect(authorization_url)

# ***STEP 5***: After the user decides whether or not to authorize your app (if it's something you're running on the command line, presumably you said yes), they get sent to the callback url with authorization information that you need to parse.

# Let's do it right in our callback route, since flask does a bunch of weird WTF/magic with a global request object rather than passing it in to anything ( http://flask.pocoo.org/docs/0.12/api/#flask.request ).


@app.route('/oauth-callback', methods=['GET'])
def get_api_key():
    oauth_verifier = request.args.get("oauth_verifier")
    if oauth_verifier: # if this shows up, then we've been authorized.
        #
        # therefore, now it's time for:
        #
        # ***STEP 6*** (still in our callback route):
        #
        # 6a. I think the temporary token you're sent back is the same you sent, but it's not completely clear from the docs, so let's parse it anyway.
        #
        temporary_token2 = request.args.get("oauth_token")
        # but just in case that doesn't really exist and it is the one we had before:
        if temporary_token2:
            oauth_token = temporary_token2
        else:
            oauth_token = temporary_request_token
        #
        # 6b. Send yet ANOTHER request, this time for the proper authorization token
        #
        access_token = auth_client.get_access_token(oauth_token, oauth_secret, oauth_verifier)
        #
        # And we should be authenticated!!!  Let's use our new token.
        #
        real_client = EvernoteClient(token=access_token)
        userStore = real_client.get_user_store()
        user = userStore.getUser()
        return "Hi! You're authenticated, and I can prove it, {}!".format(user.username)
    else:  # our request was not authorized.  throw an unfriendly error.
        abort(401)

if __name__ == '__main__':
    print "please go to http://127.0.0.1:8080/authorize-evernote"
    app.run(port=8080)
