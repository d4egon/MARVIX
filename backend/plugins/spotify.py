# backend/plugins/spotify.py
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json

# Load config
with open('../config.json', 'r') as f:
    config = json.load(f)
SPOTIFY_CLIENT_ID = config.get('spotify_client_id')
SPOTIFY_CLIENT_SECRET = config.get('spotify_client_secret')
SPOTIFY_REDIRECT_URI = 'http://localhost:5000/callback'

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                                              client_secret=SPOTIFY_CLIENT_SECRET,
                                              redirect_uri=SPOTIFY_REDIRECT_URI,
                                              scope="user-read-playback-state user-modify-playback-state"))

def play_track(track_name):
    results = sp.search(q=track_name, limit=1)
    if results['tracks']['items']:
        track_uri = results['tracks']['items'][0]['uri']
        sp.start_playback(uris=[track_uri])
        return f"Playing {track_name} on Spotify."
    return "No track found."

# Add more: pause, next, etc.