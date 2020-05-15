import os, json
import requests
from flask import Flask, session, redirect, request, url_for
from requests_oauthlib import OAuth2Session
import pandas as pd

app = Flask(__name__)


OURA_CLIENT_ID = 'JMCE2VESOI2AKLEK'
OURA_CLIENT_SECRET = '4QU3GL5KPC5QTW3F5GSY7CP6Y4IJ5TKC'

START_DATE = '2020-01-01'
END_DATE = '2020-02-01'
LOCAL_STORAGE_PATH = 'sleep_data_from{}_to{}.csv'.format(START_DATE, END_DATE)
LOCAL_ACTIVITY_PATH = 'activity_data_from{}_to{}.csv'.format(START_DATE, END_DATE)
LOCAL_READINESS_PATH = 'readiness_data_from{}_to{}.csv'.format(START_DATE, END_DATE)

OURA_AUTH_URL = 'https://cloud.ouraring.com/oauth/authorize'
OURA_TOKEN_URL = 'https://api.ouraring.com/oauth/token'


@app.route('/login')
def oura_login():
    """Login to the Oura cloud.
    This will redirect to the login page
    of the OAuth provider in our case the
    Oura cloud's login page
    """
    oura_session = OAuth2Session(OURA_CLIENT_ID)

    # URL for Oura's authorization page for specific client
    authorization_url, state = oura_session.authorization_url(OURA_AUTH_URL)

    session['oauth_state'] = state

    return redirect(authorization_url)


@app.route('/callback')
def callback():
    """Callback page
    Get the acces_token from response url from Oura.
    Redirect to the sleep data page.
    """
    oura_session = OAuth2Session(OURA_CLIENT_ID, state=session['oauth_state'])
    session['oauth'] = oura_session.fetch_token(
                        OURA_TOKEN_URL,
                        client_secret=OURA_CLIENT_SECRET,
                        authorization_response=request.url)

    update_json_token()

    return redirect(url_for('.sleep'))


@app.route('/sleep')
def sleep():
    """Sleep data page
    Get sleep data from the OURA API
    transform sleep data to a pandas DataFrame
    store sleep data as a csv
    return description of the DataFrame
    """
    oauth_token = session['oauth']['access_token']

    sleep_data = requests.get('https://api.ouraring.com/v1/sleep?'
                              'start={}&end={}&access_token={}'
                              .format(START_DATE, END_DATE, oauth_token))
    json_sleep = sleep_data.json()
    df = pd.DataFrame(json_sleep['sleep'])
    df.to_csv(LOCAL_STORAGE_PATH)
    return redirect(url_for('.activity'))



@app.route('/activity')
def activity():
    """Sleep data page
    Get sleep data from the OURA API
    transform sleep data to a pandas DataFrame
    store sleep data as a csv
    return description of the DataFrame
    """
    oauth_token = session['oauth']['access_token']

    activity_data = requests.get('https://api.ouraring.com/v1/activity?'
                                 'start={}&end={}&access_token={}'
                                 .format(START_DATE, END_DATE, oauth_token))
    json_activity = activity_data.json()
    df = pd.DataFrame(json_activity['activity'])
    df.to_csv(LOCAL_ACTIVITY_PATH)
    return redirect(url_for('.readiness'))
    #return '<p>Successfully stored activity data</p><p>{}</p>'\
    #    .format(df.describe())


@app.route('/readiness')
def readiness():
    """Sleep data page
    Get sleep data from the OURA API
    transform sleep data to a pandas DataFrame
    store sleep data as a csv
    return description of the DataFrame
    """
    oauth_token = session['oauth']['access_token']

    activity_data = requests.get('https://api.ouraring.com/v1/readiness?'
                                 'start={}&end={}&access_token={}'
                                 .format(START_DATE, END_DATE, oauth_token))
    json_readiness = activity_data.json()
    df = pd.DataFrame(json_readiness['readiness'])
    df.to_csv(LOCAL_READINESS_PATH)
    return '<p>Successfully stored readiness data</p><p>{}</p>'\
        .format(df.describe())


@app.route('/')
def home():
    """Welcome page of the sleep data app.
    """
    load_token_json('token.json')
    return redirect(url_for('.oura_login'))
    # return "<h1>Welcome to your Oura app</h1>"


def load_token_json(path):
    with open(path, 'r+') as file:
        env = json.load(file)
        os.environ['OURA_CLIENT_ID'] = env['client_id']
        os.environ['OURA_CLIENT_SECRET'] = env['client_secret']
        os.environ['OURA_ACCESS_TOKEN'] = env['access_token']
        os.environ['OURA_REFRESH_TOKEN'] = env['refresh_token']


def update_json_token():
    # Use session['oauth'] to update JSON
    with open('token.json', 'r+') as file:
        test = json.load(file)
        test['ACCESS_TOKEN'] = 'cows'
        file.seek(0)
        json.dump(test, file, indent=4)




def test_run():
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.secret_key = os.urandom(24)
    app.run(debug=False, host='127.0.0.1', port=8080)


if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.secret_key = os.urandom(24)
    app.run(debug=False, host='127.0.0.1', port=8080)
    input("Press any key to close")
