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
import os

# The playlists to archive
playlists = ["PLRDuNIkwpnsd-BKflUccPeix9WfiKP8uQ",    # The Collection
             "PL95haX7i8VmjHe0xeTx6t6Qf-D1gGUjKP",    # The OG Grand Collab
             "PLRDuNIkwpnsdsAaytTIOtkaQGcsdy_fJH",    # The Grand Collab 2 
             "PLRDuNIkwpnscDITObEK5bxWzc2qxbppjn",    # Karaoke Playlist
             "LRYRTgzdv6NxbhrrYHZ2TOPlPNz94e0D5FZ11", # 2022 Recap
             "LRYR1j6Kis480O0A9sU3oEnYWtbMrr_tPocTq", # 2023 Recap
             "PLTYtECRlkGVW5f6ZCQ44PnJWWbZ6g51L8",     # TikTok Tour
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
                mp3Path = f'{systemPath}/{fmtSong['artist']['name']} - {fmtSong['title']}'
                ydl_opts = {
                    'format': 'bestaudio',       
                    'extractaudio': True,          
                    'audioformat': 'mp3',          
                    'outtmpl': mp3Path,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3'
                    }],
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download(fmtSong["yt_id"])
                # Sets the id3 tags
                targetFile = eyed3.load(f'{mp3Path}.mp3')
                if targetFile is None:
                    print(f"Failed to load MP3 file: mp3Path")
                    return
                if targetFile.tag is None:
                    targetFile.initTag()
                targetFile.tag.artist = fmtSong['artist']['name']
                targetFile.tag.album = fmtSong['album']['title']
                targetFile.tag.title = fmtSong['title']    
                # Download the thumbnail (if available)
                if fmtSong["album"]['art'] != "null":
                    artPath = f"{systemPath}/art/{fmtSong['artist']['name']} - {fmtSong['album']['title']}.png"
                    if not os.path.exists(artPath):
                        img_data = requests.get(fmtSong["album"]['art']).content
                        with open(artPath, 'wb') as handler:
                            handler.write(img_data)
                    with open(artPath, 'rb') as img_file:
                        targetFile.tag.images.set(3, img_file.read(), "image/png")
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
