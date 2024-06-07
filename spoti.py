import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, redirect, session, url_for, render_template

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'

# Configurar las credenciales de Spotify
SPOTIPY_CLIENT_ID = 'your_client_id'
SPOTIPY_CLIENT_SECRET = 'your_client_secret'
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:5000/callback'

# Configurar el objeto de autenticación de Spotipy
sp_oauth = SpotifyOAuth(
    SPOTIPY_CLIENT_ID,
    SPOTIPY_CLIENT_SECRET,
    SPOTIPY_REDIRECT_URI,
    scope="user-library-read playlist-read-private"
)

@app.route('/')
def index():
    if not session.get('token_info'):
        return redirect(url_for('login'))
    
    token_info = session.get('token_info')
    sp = spotipy.Spotify(auth=token_info['access_token'])
    playlists = sp.current_user_playlists()
    
    return render_template('spoti.html', playlists=playlists['items'])

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
