# File imports
import utils
import youtube
import datatypes
import lastfm
# Dep imports
import time
import datetime
import json
import yt_dlp
import eyed3
import requests

# The playlists to archive
playlists = [#"PLRDuNIkwpnsd-BKflUccPeix9WfiKP8uQ",    # The Collection
             #"PL95haX7i8VmjHe0xeTx6t6Qf-D1gGUjKP",    # The OG Grand Collab
             #"PLRDuNIkwpnsdsAaytTIOtkaQGcsdy_fJH",    # The Grand Collab 2 
             #"PLRDuNIkwpnscDITObEK5bxWzc2qxbppjn",    # Karaoke Playlist
             #"LRYRTgzdv6NxbhrrYHZ2TOPlPNz94e0D5FZ11", # 2022 Recap
             #"LRYR1j6Kis480O0A9sU3oEnYWtbMrr_tPocTq", # 2023 Recap
             #"PLTYtECRlkGVW5f6ZCQ44PnJWWbZ6g51L8",     # TikTok Tour
             #"PLRDuNIkwpnsc1Gvmt90PO3zV7XVQhu-sr",
             "PLRDuNIkwpnsejsEmrc12a5K8mXmF9i5vX"
            ]

currentDB = []
systemDB = []
systemPath = "/bulk/users/mwollam/share/music/music"

def main():    
    # The "database"
    with open("database.json") as dbj:
        currentDB = json.load(dbj)
    
    for pL in playlists:
        rawData = youtube.get_playlist_items(pL)
        for rS in rawData:
            # The song structure, with some empty fields
            fmtArtist = datatypes.ArtistCleaner(rS['snippet']['videoOwnerChannelTitle'])
            fmtSong = {
                "yt_id": rS['contentDetails']['videoId'],
                "published": rS['contentDetails']['videoPublishedAt'],
                "archived": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "title": datatypes.TitleCleaner(rS['snippet']['title'], fmtArtist),
                "mbid": "Unknown",
                "artist": {
                    "name": fmtArtist,
                    "yt_id": rS['snippet']['videoOwnerChannelId'],
                    "mbid": "Unknown"
                },
                "album": {
                    "title": "Unknown",
                    "mbid": "Unknown",
                    "art": "null"
                },
                "genre": "Unknown"
            }
            if (next((song for song in currentDB if song['yt_id'] == fmtSong['yt_id']), False)):
                print("song is already in the database")
            else:
                print("adding song to database")
                mbid = lastfm.getSongID(fmtSong['artist']['name'], fmtSong['title'])
                # Updating the song info with the data from Last.FM
                if (mbid is not None) and (len(mbid) > 0):
                    lfmData = lastfm.getSongInfo(mbid)
                    if lfmData is None:
                        print(f"Unable to find song {fmtSong['title']} on Last.FM")
                        continue
                    fmtSong.update({
                        "title": lfmData['title'],
                        "mbid": lfmData['mbid'],
                        "artist": {
                            "name": lfmData['artist']['name'],
                            "mbid": lfmData['artist']['mbid']
                        },
                        "album": {
                            "title": lfmData['albumInfo']['title'],
                            "mbid": lfmData['albumInfo']['mbid'],
                            "art": lfmData['albumInfo']['art']
                        },
                        "genre": lfmData['genre']
                    })
                # Download the actual song
                ydl_opts = {
                    'format': 'bestaudio',       
                    'extractaudio': True,          
                    'audioformat': 'mp3',          
                    'outtmpl': f'{systemPath}/{fmtSong['artist']['name']} - {fmtSong['title']}.mp3'
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download(fmtSong["yt_id"])
                # Sets the id3 tags
                targetFile = eyed3.load(f'{systemPath}/{fmtSong['artist']['name']} - {fmtSong['title']}.mp3')
                targetFile.tag.artist = fmtSong['artist']['name']
                targetFile.tag.album = fmtSong['album']['name']
                targetFile.tag.title = fmtSong['title']
                targetFile.tag.track_num = 3
                targetFile.tag.save()                
                # Download the thumbnail (if available)
                if fmtSong["album"]['art'] is not "null":
                    img_data = requests.get(fmtSong["album"]['art']).content
                    with open(f"{systemPath}/{fmtSong['artist']['name']} - {fmtSong['album']['art']}.png", 'wb') as handler:
                        handler.write(img_data)
                    targetFile.tag.images.set(3, handler.read(), "image/jpeg")
                    targetFile.tag.save()
                # Adds the song to the database
                currentDB.append(fmtSong)
    
    # write the DB to the file
    sortedDB = sorted(currentDB, key=lambda d: d['title'])
    with open("database.json", "w") as dbOut:
        json.dump(sortedDB, dbOut)
        


# Actual start
if __name__ == "__main__":
    start_time = time.time()
    main()
    utils.logPrint("Matt.FM execution took {} seconds".format(int((time.time() - start_time))), 0)