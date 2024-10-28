import utils

import sys
from pydoc import cli
import datetime
from urllib.parse import urlparse
import os
import requests
import json

import google.auth.exceptions
import google_auth_oauthlib
import google.oauth2
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import googleapiclient.discovery
import googleapiclient.errors

# Variables and such
scopes = ["https://www.googleapis.com/auth/youtube.force-ssl",
          "https://www.googleapis.com/auth/youtube.readonly"]
lastAuth = datetime.datetime.min       

def get_authenticated_service(lastAuth):
    utils.logPrint("Authenticating service access and refresh token", 0)
    nowAuth = datetime.datetime.now()
    authDiff = nowAuth - lastAuth
    if (authDiff.total_seconds() * 1000 < 250):
        datetime.time.sleep(0.150)
    
    lastAuth = datetime.datetime.now()

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "youtubeauth.json"

    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)

    if os.path.exists("refresh.token"):
        with open("refresh.token", 'r') as t:
            rawToken = t.read()
            with open(client_secrets_file, 'r') as j:
                youtubeAuth = json.loads(j.read())
            params = {
                "grant_type": "refresh_token",
                "client_id": youtubeAuth['installed']['client_id'],
                "client_secret": youtubeAuth['installed']['client_secret'],
                "refresh_token": rawToken
            }
            authorization_url = "https://www.googleapis.com/oauth2/v4/token"
            r = requests.post(authorization_url, data=params)
            credToken = google.oauth2.credentials.Credentials(
                                                    rawToken,
                                                    refresh_token = rawToken,
                                                    token_uri = 'https://accounts.google.com/o/oauth2/token',
                                                    client_id = youtubeAuth['installed']['client_id'],
                                                    client_secret = youtubeAuth['installed']['client_secret']
                                                    )
    else: 
        credFlow = flow.run_console()
        with open('refresh.token', 'w+') as f:
            credToken = credFlow
            f.write(credFlow._refresh_token)
            utils.logPrint('Saved Refresh Token to file: refresh.token', 0)
    
    return googleapiclient.discovery.build(api_service_name, api_version, credentials=credToken)

### <summary>
# Recursively gets all playlist items
### </summary>
def get_playlist_items(playlistID):
    utils.logPrint("Getting the playlist data", 0)

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    youtube = get_authenticated_service(lastAuth)

    # Makes the first round of API calls
    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        maxResults=50,
        playlistId=playlistID
    )

    response = request.execute()

    currentLen = response["pageInfo"]["totalResults"]
    playlist_items = []    
    for p in response['items']:
        playlist_items.append(p)
        
    utils.logPrint("Getting the rest of the playlist datat", 0)
    try:
        while len(playlist_items) < response["pageInfo"]['totalResults']:
            request = youtube.playlistItems().list(
                part="snippet,contentDetails",
                maxResults=50,
                playlistId=playlistID,
                pageToken=response["nextPageToken"]
            )        
            response = request.execute()
            for p in response['items']:
                playlist_items.append(p)
    except googleapiclient.errors.HttpError as err:
        # This is intentional because I have too many songs to do in 1 day, so I just break it up
        if err.reason == "quotaExceeded":
            utils.logPrint("Quota limit exceded, terminating program.", 4)
            sys.exit()
        else:
            utils.logPrint("Unhandled exception while adding video: " + str(err), 4)
    return playlist_items