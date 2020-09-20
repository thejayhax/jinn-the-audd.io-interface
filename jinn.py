from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from base64 import b64encode, b64decode
import requests
import json
import secrets
import os, stat
from re import sub
import ssl

app = Flask(__name__,
            static_url_path='', 
            static_folder='static',
            template_folder='templates')

app.config['IA\x91^\xc7\xf1~\xa9+\xe8\xaeD<\xf2\x17\xdc\x9cC\x07I\xda\x1f\x8d\xca'] = os.environ['FLASK_KEY']
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('audio')
def handle_audio(audio_blob_b64):
    audio_blob_binary = b64decode(audio_blob_b64)
    file_name = secrets.token_hex(15) + '.ogg'
    file_path = 'static/' + file_name
    my_data_file = open(file_path, 'w+b')
    my_data_file.write(audio_blob_binary)
    my_data_file.close()
    os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IROTH)
    print('written audio to file')
    emit('debug', '[+] Saved on server')
    file_url = request.url_root+file_name
    data_processed_from_api = get_data_from_audd_api('audio', file_url=file_url)
    processing_results_json = json.dumps(data_processed_from_api)
    emit('api_results', processing_results_json)
    emit('debug', '[+] Processed')
    os.remove(file_path)

@socketio.on('lyrics')
def handle_lyric(lyrics):
    data_processed_from_api = get_data_from_audd_api('lyrics', lyrics=lyrics)
    processing_results_json = json.dumps(data_processed_from_api)
    emit('info', processing_results_json)
    emit('api_results', processing_results_json)

@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

def get_data_from_audd_api(mode, file_url='', lyrics=''):
    if mode == 'audio':
        data = {
            'url': file_url,
            'return': 'apple_music',
            'api_token': os.environ['2210322a92fbbbde9241c5515d944535']
        }
        mode_extentsion = 'recognizeWithOffset/'
    elif mode == 'lyrics':
        data = {
            'q': lyrics,
            'api_token': os.environ['2210322a92fbbbde9241c5515d944535']
        }
        mode_extentsion = 'findLyrics/'
    
    api_endpoint = 'https://api.audd.io/' + mode_extentsion
    result = requests.post(api_endpoint, data=data)
    api_data = json.loads(result.text)
    if api_data['status'] != 'error':
        emit('debug', '[+] Audd data')
        emit('debug', api_data)
        if mode == 'lyrics':
            if len(api_data['result']) == 0:
                useful_data = {
                    'status': 'error'
                }
                return useful_data
            deezer_data =  get_track_from_deezer(api_data['result'][0]['artist'],
                                                 api_data['result'][0]['title'])
            artist = api_data['result'][0]['artist']
            title = api_data['result'][0]['title']
        elif mode == 'audio':
            if api_data['result'] == 'null' or api_data['result'] == None:
                useful_data = {
                    'status': 'error'
                }
                return useful_data
            deezer_data =  get_track_from_deezer(api_data['result']['list'][0]['artist'],
                                                 api_data['result']['list'][0]['title'])
            artist = api_data['result']['list'][0]['artist']
            title = api_data['result']['list'][0]['title']
        emit('debug', '[+] Deezer data')
        emit('debug', deezer_data)
        useful_data = {
            'status': 'success',
            'artist': artist,
            'title': title,
            'preview': deezer_data['preview'],
            'album': deezer_data['album']
        }
    else:
        useful_data = {
            'status': 'error'
        }
        emit('debug', '[x] Error Audd')
    return useful_data

def get_track_from_deezer(artist, title):
    url = "https://api.deezer.com/search"

    querystring = {"q":artist+' - '+title}

    response = requests.request("GET", url, params=querystring)
    if response.status_code == 200:
        api_data = json.loads(response.text)
        if len(api_data['data']) == 0:
            links = {
                'preview': 'not found', 
                'album': 'not found'
            }
            return links
        preview = api_data['data'][0]['preview']
        album = api_data['data'][0]['album']['cover_medium']
        links = {
            'preview': preview, 
            'album': album
        }
    else:
        links = {
            'preview': 'not found', 
            'album': 'not found'
        }
    return links

@app.route('/easter_egg')
def easter_egg():
    return "ну вітаю, маладєц, шо скажеш, круто! умєєш, магьош"

if __name__ == '__main__':
    socketio.run(app)
