import json
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
import youtube_dl

# from exceptions import ResponseException
from secrets import *
class music_dir:
    def __init__(self):
        self.yt_client = self.yt_client()
        self.all_song_info = {}

    #to log into youtube
    def yt_client(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

    def liked_vids(self):
        request = self.youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like"
        )
        response = request.execute()

        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(
                item["id"])

            video = youtube_dl.YoutubeDL({}).extract_info(
                youtube_url, download=False)
            song_name = video["track"]
            artist = video["artist"]

            if artist is not None and song_name is not None:
                # save all important info and skip any missing song and artist
                self.all_song_info[video_title] = {
                    "youtube_url": youtube_url,
                    "song_name": song_name,
                    "artist": artist,

                    # add the uri, easy to get song to put into playlist
                    "spotify_uri": self.get_spotify_uri(song_name, artist)

                }

    def create_music_dir(self):
        request_body = json.dumps({
            "name": "Youtube Playlist",
            "description": "All Youtube Videos",
            "public": True
        })

        endpoint = "https://api.spotify.com/v1/users/{user_id}/playlists".format(self.id)
        response = requests.post(
            endpoint,
            data = request_body,
            headers={
                "Content-Type":"application/json",
                "Authorization":"Bearer {}".format(token)
            }
        )
        response_json = response.json()
        return response_json["id"]



    def spotify_uri(self,song_name,artist_name):
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(song_name,artist_name)
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(token)
            }
        )
        response_json = response.json()
        songs = response_json["tracks"]["items"]

        uri = songs[0]["uri"]
        return uri


    def new_song(self):
        self.liked_vids()
        uris = [info["spotify_uri"]
                for song, info in self.all_song_info.items()]

        playlist_id = self.create_music_dir()
        request_data = json.dumps(uris)
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        response = requests.post(
            query,
            data = request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(token)
            }
        )
        response_json = response.json()
        # if response.status_code != 200:
        #     raise ResponseException(response.status_code)
        #
        # response_json = response.json()
        return response_json



