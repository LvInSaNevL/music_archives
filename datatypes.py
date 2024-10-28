# import deps
import utils
# file import
   
# The basic song structure
# This is mostly here for documentation
Song = {
    "yt_id": "", # yt - ['contentDetails]['videoId]
    "published": "", # yt - ['contentDetails']['published']
    "title": "", # yt - ['snippet']['title']
    "artist": {
        "name": "", # yt - ['snippet']['contentOwnerName']
        "yt_id": "" # yt - ['snippet]['contentOwnerId']
    },
    "duration": "" # yt - ['snippet']
}

# Cleans up the title to get rid of junk
def TitleCleaner(title, artist):
    # The things to remove
    filters = ["(Official Music Video)",
               "(Lyric Video)",
               "(Official Video)"]
    for sF in filters:
        title = title.replace(sF, "")
    title = title.replace(artist, "")
    return title.strip()

# Cleans up the artists name to get rid of junk
def ArtistCleaner(artist):
    filters = [" - Topic",
               "(Official)",
               "VEVO"]
    for aF in filters:
        artist = artist.replace(aF, "")    
    return artist.strip()