import logging  # Flaskのログを削除する
from engineio.payload import Payload
from threading import Lock  # これ消していいよね？
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from concurrent.futures import ThreadPoolExecutor  # threadPoolExecutor
import json
from flask import Flask, render_template, request  # Flaskを使うため
# from UDP_main import WebServer_EventCallback  # WebServer_EventCallbackをインポート
import time
import threading
import webbrowser
# import global_value as g
from logger_setup import logger

# url = 'https://google.com'
# webbrowser.open(url, new=2, autoraise=True)


# def WebServer_EventCallback():
#     pass


Payload.max_decode_packets = 10000

thread_lock = Lock()  # これ消していいよね？

# うけとったデータ
received_json = {"test": -1}

# ユーザー数
user_count = 0

reception_json = {
    "state": 0
}

# l = logging.getLogger()
# l.addHandler(logging.FileHandler("/dev/null"))
app = Flask(__name__,
            template_folder="flask/templates",
            static_folder="flask/static")
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*')  # , async_mode='eventlet'

l = logging.getLogger()
l.addHandler(logging.FileHandler("/dev/null")) # ubuntu
# l.addHandler( logging.FileHandler( "/nul" )) # Windows

robo = ""
gamePad = ""

def flask_socketio_run(robots, gamePads):
    global robo, gamePad
    robo = robots
    gamePad = gamePads
    socketio.run(app, host='0.0.0.0', port=5000,
                 debug=True, use_reloader=False)
    logger.debug(f"run flask_socketio")
    
    # allow_unsafe_werkzeug=True
    # async_mode="threading" 非同期処理に使用するライブラリの指定`threading`, `eventlet`, `gevent`から選択可能
    # threaded=Trueやると起動しない
    # ssl_context=(cert_path, key_path)


def send_message_to_clients(message: dict):
    socketio.emit('dict', message)


@app.route("/")
def index():
    return render_template('main.html')  # インスタンスをテンプレートに渡す

# ユーザーが新しく接続すると実行


@socketio.on('connect')
def connect(auth):
    global user_count
    logger.info(f"新規デバイスがWebServerに接続された")
    user_count += 1
    # 接続者数の更新（全員向け）
    emit('count_update', {'user_count': user_count}, broadcast=True)


# ユーザーの接続が切断すると実行
@socketio.on('disconnect')
def disconnect():
    global user_count
    user_count -= 1
    # 接続者数の更新（全員向け）
    emit('count_update', {'user_count': user_count}, broadcast=True)

# サーバー側から自発的にemitする関数


def emit_messages():
    while True:
        # socketio.emit('message', {'data': 'Hello from the server!'})
        time.sleep(5)  # 5秒ごとに送信

# サーバー側からのemitを別スレッドで動かす


@socketio.on('start_emit')
def start_emit():
    threading.Thread(target=emit_messages).start()


@socketio.on('json_request')
def json_request():
    global reception_json  # しなくていいの?
    emit('json_receive', reception_json)


@socketio.on("send_web_data")
def send_web_data(json):
    global received_json
    received_json = json


@socketio.on("button")
def button(json):
    global robo, gamePad
    from main import WebServer_EventCallback
    if list(json) == ["up"]:
        WebServer_EventCallback(json["up"], "up", robo, gamePad)
    elif list(json) == ["down"]:
        WebServer_EventCallback(json["down"], "down", robo, gamePad)


@socketio.on("my ping")
def ping():
    emit('my pong', {})


if __name__ == '__main__':
    # main()
    # flask_socketio_run()
    pass
