# File Imports
import utils
# Dep Imports
import requests
from thefuzz import fuzz

BASE_URL = 'http://ws.audioscrobbler.com/2.0/'

def findTrack(artist, title):
    creds = utils.readAuth("lastfm")
    print(f"{title} - {artist}")
    URL = f"{BASE_URL}?method=track.search&track={title}&api_key={creds['key']}&format=json"
    
    response = requests.get(URL)
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        fmtData = data['results']['trackmatches']['track']
        
        maxMatch = {
            "match": 0,
            "data": []
        }
        
        for t in range(len(fmtData)):
            fmtArtist = fmtData[t]['artist']
            fmtTitle = fmtData[t]['name']
                        
            songRatio = fuzz.ratio(str(title), str(fmtTitle))
            artistRatio = fuzz.ratio(str(artist), str(fmtArtist))
            totalRatio = (((songRatio * 0.4) + (artistRatio * 0.6)))
                        
            if (totalRatio > maxMatch['match']):
                maxMatch['data'] = fmtData[t]
                maxMatch['match'] = totalRatio
            
            if (maxMatch['match'] > 90):
                # print(f"{maxMatch['data']['name']} - {maxMatch}['data']['artist'] == {maxMatch['match']}")
                return maxMatch['data']['mbid']
    else:
        print(f"Error: {response.status_code}")
        return None

def getSongInfo(mbid):
    print(mbid)
    creds = utils.readAuth("lastfm")
    URL = f"{BASE_URL}?method=track.getInfo&mbid={mbid}&api_key={creds['key']}&format=json"
    print(URL)
    
    response = requests.get(URL)
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        
        artIndex = utils.last_index(data['track']['album']['image'])
        fmtData = {
            "mbid": mbid,
            "artist": {
                data['track']['artist']['name'],
                data['track']['artist']['mbid']
            },
            "title": data['track']['name'],
            "albumInfo": {
                "title": data['track']['album']['title'],
                "mbid": data['track']['album']['mbid'],
                "art": data['track']['album']['image'][artIndex]['#text']
            },
            "genre": [
                data['track']['toptags']['tag'][0]['name'],
                data['track']['toptags']['tag'][1]['name']
                ] 
        }
        return fmtData
    else:
        print(f"Error: {response.status_code}")
        return None