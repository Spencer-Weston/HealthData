import json
import logging
import os

import pandas as pd
import requests
from flask import Flask, session, redirect, request, url_for
from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from requests_oauthlib import OAuth2Session

# import src.oura.tables as tables

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
    """Directs the user to login to the oura cloud for authorization.

    A successful login sends the app to the callback URL which updates the token.json.
    """
    oura_session = OAuth2Session(OURA_CLIENT_ID)

    # URL for oura's authorization page for specific client
    authorization_url, state = oura_session.authorization_url(OURA_AUTH_URL)

    session['oauth_state'] = state

    return redirect(authorization_url)


@app.route('/callback')
def callback():
    """Gets the access token from oura's response url and redirects to the sleep data page."""
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


@app.route('/readiness')
def readiness():
    """Sleep data page
    Get sleep data from the OURA API
    transform sleep data to a pandas DataFrame
    store sleep data as a csv
    return description of the DataFrame
    """
    oauth_token = session['oauth']['access_token']

    readiness_data = requests.get('https://api.ouraring.com/v1/readiness?'
                                 'start={}&end={}&access_token={}'
                                 .format(START_DATE, END_DATE, oauth_token))
    json_readiness = readiness_data.json()
    df = pd.DataFrame(json_readiness['readiness'])
    df.to_csv(LOCAL_READINESS_PATH)
    return '<p>Successfully stored readiness data</p><p>{}</p>'\
        .format(df.describe())


@app.route('/', methods=['GET', 'POST'])
def home():
    """Welcome page of the sleep data app.
    """
    # TODO create handling for when no json exists (Don't want to keep information on github)
    try:
        load_token_json('token.json')
    except FileNotFoundError:
        create_token_json('token.json')
        load_token_json('token.json')
    access_token = os.getenv("access_token")
    refresh_token = os.getenv("refresh_token")
    if not (access_token or refresh_token):
        return redirect(url_for('.oura_login'))
    else:
        token = {'access_token': access_token, 'refresh_token': refresh_token}

    oura_session = OAuth2Session(os.getenv('OURA_CLIENT_ID'), token=token, auto_refresh_url=OURA_TOKEN_URL)

    oauth_token = oura_session.access_token

    info_test = requests.get('https://api.ouraring.com/v1/userinfo?'
                             'access_token={}'.format(oauth_token))

    if info_test.status_code == 401:
        # Refresh Token
        extra = {
            'client_id': os.getenv('OURA_CLIENT_ID'),
            'client_secret': os.getenv('OURA_CLIENT_SECRET'),
        }

        # If the refresh token is bad (manually modified; not sure about expired), refresh_token() will return a missing
        # token error. So, I'm implementing error handling here.
        try:
            session['oauth'] = oura_session.refresh_token(OURA_TOKEN_URL, **extra)
        except MissingTokenError:
            return redirect(url_for('.oura_login'))

        update_json_token()
        oauth_token = oura_session.access_token
        info_test = requests.get('https://api.ouraring.com/v1/userinfo?'
                                 'access_token={}'.format(oauth_token))

        # If refresh token does not work, redirect to login
        if info_test.status_code == 401:
            # Access token
            return redirect(url_for('.oura_login'))

    # Configuration should be done by this point, so request data
    sleep_data = requests.get('https://api.ouraring.com/v1/sleep?'
                              'start={}&end={}&access_token={}'
                              .format(START_DATE, END_DATE, oauth_token))
    tables.sleep.process(sleep_data)

    activity_data = requests.get('https://api.ouraring.com/v1/activity?'
                                 'start={}&end={}&access_token={}'
                                 .format(START_DATE, END_DATE, oauth_token))
    tables.activity.process(activity_data)

    readiness_data = requests.get('https://api.ouraring.com/v1/readiness?'
                                  'start={}&end={}&access_token={}'
                                  .format(START_DATE, END_DATE, oauth_token))
    tables.readiness.process(readiness_data)

    return redirect(url_for('.shutdown'))


@app.route('/shutdown', methods=['GET'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


def create_token_json(path):
    """Create the token.json file used for API access.

    todo: is this safe? """
    oura_client_id = input('Input your oura client id')
    oura_client_secret = input('Input your oura client secret')
    data = {"OURA_CLIENT_ID": oura_client_id, "OURA_CLIENT_SECRET": oura_client_secret}
    with open(path, 'w') as f:
        json.dump(data, f)


def load_token_json(path):
    with open(path, 'r+') as file:
        env = json.load(file)
        for i in env.keys():
            if type(env[i]) is str:
                os.environ[i] = env[i]


def update_json_token():
    # Use session['oauth'] to update JSON
    with open('token.json', 'r+') as file:
        data = json.load(file)

    data.update(session['oauth'])

    with open('token.json', 'w+') as file:
        file.seek(0)
        json.dump(data, file, indent=4)


def process_data():
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    # logging.basicConfig(filename='example.log', level=logging.DEBUG)
    app.secret_key = os.urandom(24)
    app.run(debug=False, host='127.0.0.1', port=8080)


if __name__ == "__main__":
    import os
    from oura.v2 import OuraClientV2


    # my_token = os.getenv('MY_TOKEN')
    # import requests
    #
    # url = 'https://api.ouraring.com/v2/usercollection/daily_sleep'
    # params = {
    #     'start_date': '2024-10-10',
    #     'end_date': '2024-10-15'
    # }
    # headers = {
    #     'Authorization': 'Bearer QEG7CEKQQDAOA4QICOUSREGOHEP7G3WU'
    # }
    # response = requests.request('GET', url, headers=headers, params=params)
    # print(response.text)
    # response_json = response.json()
    # df = pd.DataFrame(response_json['data'])
    client = OuraClientV2(personal_access_token="QEG7CEKQQDAOA4QICOUSREGOHEP7G3WU")
    # who_am_i = client.user_info()
    test = client.sleep()
    t=2
    # os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    # # logging.basicConfig(filename='example.log', level=logging.DEBUG)
    # app.secret_key = os.urandom(24)
    # test = app.run(debug=False, host='127.0.0.1', port=8080)
    # print('finito')
