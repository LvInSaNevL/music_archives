# File imports
import utils
import youtube
import datatypes
import lastfm
# Dep imports
import time
import json
import dateutil.parser as dp

# The playlists to archive
playlists = [#"PLRDuNIkwpnsd-BKflUccPeix9WfiKP8uQ",    # The Collection
            # "PL95haX7i8VmjHe0xeTx6t6Qf-D1gGUjKP",    # The OG Grand Collab
            # "PLRDuNIkwpnsdsAaytTIOtkaQGcsdy_fJH",    # The Grand Collab 2 
             #"PLRDuNIkwpnscDITObEK5bxWzc2qxbppjn",    # Karaoke Playlist
             #"LRYRTgzdv6NxbhrrYHZ2TOPlPNz94e0D5FZ11", # 2022 Recap
             #"LRYR1j6Kis480O0A9sU3oEnYWtbMrr_tPocTq"  # 2023 Recap
             "PLRDuNIkwpnsejsEmrc12a5K8mXmF9i5vX"
            ]

currentDB = []
systemDB = []

def main():    
    # The "database"
    with open("database.json") as dbj:
        currentDB = json.load(dbj)
    
    for pL in playlists:
        rawData = youtube.get_playlist_items(pL)
        for rS in rawData:
            # The song structure
            fmtArtist = datatypes.ArtistCleaner(rS['snippet']['videoOwnerChannelTitle'])
            fmtSong = {
                "yt_id": rS['contentDetails']['videoId'],
                "published": dp.parse(rS['contentDetails']['videoPublishedAt']).strftime('%s'),
                "title": datatypes.TitleCleaner(rS['snippet']['title'], fmtArtist),
                "artist": {
                    "name": fmtArtist,
                    "yt_id": rS['snippet']['videoOwnerChannelId'],
                }
            }
            print(fmtSong)
            if (next((song for song in currentDB if song['yt_id'] == fmtSong['yt_id']), False)):
                print("song is already in the database")
            else:
                print("adding song to database")
                lfmID = lastfm.findTrack(fmtSong['artist']['name'], fmtSong['title'])
                lfmData = lastfm.getSongInfo(lfmID)
                # Updating the song info with the data from Last.FM
                fmtSong.update({
                    "mbid": lfmData['mbid'],
                    # "artist": {
                    #     "name": lfmData['artist']['name'],
                    #     "mbid": lfmData['artist']['mbid']
                    # },
                    "album": {
                        "title": lfmData['albumInfo']['title'],
                        "mbid": lfmData['albumInfo']['mbid'],
                        "art": lfmData['albumInfo']['art']
                    },
                    "genre": lfmData['genre']
                })
                print(fmtSong)
                currentDB.append(fmtSong)
    
    # # write the DB to the file
    # sortedDB = sorted(currentDB, key=lambda d: d['title'])
    # with open("database.json", "w") as dbOut:
    #     json.dump(currentDB, dbOut)
        


# Actual start
if __name__ == "__main__":
    start_time = time.time()
    main()
    utils.logPrint("Matt.FM execution took {} seconds".format(int((time.time() - start_time))), 0)