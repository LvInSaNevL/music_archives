# File Imports
import utils
# Dep Imports
import requests
from thefuzz import fuzz
import json

BASE_URL = 'http://ws.audioscrobbler.com/2.0/'

def getSongID(artist, title):
    query = f'artist:"{artist}" AND recording:"{title}"'
    url = f'https://musicbrainz.org/ws/2/recording/?query={query}&fmt=json&limit=25'
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        recordings = data.get('recordings', [])
        
        maxMatch = {
            "match": 0,
            "data": []
        }

        for t in range(len(recordings)):
            fmtArtist = recordings[t]['artist-credit'][0]['name']
            fmtTitle = recordings[t]['title']
                        
            songRatio = fuzz.ratio(str(title), str(fmtTitle))
            artistRatio = fuzz.ratio(str(artist), str(fmtArtist))
            totalRatio = (((songRatio * 0.4) + (artistRatio * 0.6)))
                        
            if (totalRatio > maxMatch['match']):
                maxMatch['data'] = recordings[t]
                maxMatch['match'] = totalRatio
            
            if (maxMatch['match'] > 90):
                # print(f"{maxMatch['data']['name']} - {maxMatch}['data']['artist'] == {maxMatch['match']}")
                return maxMatch['data']['id']
    else:
        print(f"Error: {response.status_code}")
        return None

def getMBIDInfo(mbid):
    URL = f"https://musicbrainz.org/ws/2/recording/{mbid}?inc=artist-credits+isrcs+releases+genres&fmt=json"
    response = requests.get(URL)
    print(response.json())
    return response.json()

def getSongInfo(mbid):
    print(mbid)
    creds = utils.readAuth("lastfm")
    URL = f"{BASE_URL}?method=track.getInfo&mbid={mbid}&api_key={creds['key']}&format=json"
    print(URL)
    
    response = requests.get(URL)
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        if "error" in data:
            return None

        artIndex = utils.last_index(data['track']['album']['image'])
        fmtData = {
            "mbid": mbid,
            "artist": {
                "name": data['track']['artist']['name'],
                "mbid": data['track']['artist']['mbid']
            },
            "title": data['track']['name'],
            "albumInfo": {
                "title": data['track']['album']['title'],
                "mbid": data['track']['album']['mbid'],
                "art": data['track']['album']['image'][artIndex]['#text']
            }
        }
        # Gets the genre
        with open("genre_codes.json") as gcs:
            genre_codes = json.load(gcs)
            returnTags = data['track']['toptags']['tag']
            for tags in returnTags:
                for codes in genre_codes:
                    if tags['name'].lower() == codes['name'].lower():
                        fmtData.update({"genre": codes['name']})
                        return fmtData
            fmtData.update({"genre": "Unknown"})
            return fmtData
    else:
        print(f"Error: {response.status_code}")
        return None