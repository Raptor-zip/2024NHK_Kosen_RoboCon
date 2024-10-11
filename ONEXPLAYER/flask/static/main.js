let inputElem;
let currentValueElement;

var socket = io();
namespace = '/demo'; //main.pyで指定したnamespace
// var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);

var ping_pong_times = [];
let start_time_ping_pong;
let start_timer

const alarm = new Audio("static/battery_alert.mp3");
alarm.loop = true;

// const button_sound = new Audio("static/button.mp3");
// button_sound.loop = false;

function button_sound() {
    const sound = new Audio("static/button.mp3");
    sound.loop = false;
    sound.play();
}

let json_received = {};
namespace = '/test';

// 接続者数の更新
socket.on('count_update', function (msg) {
    // document.getElementById('user_count').innerText = msg.user_count;
    console.log(msg.user_count + " users connected");
    document.getElementById('user_count_value').innerText = msg.user_count;
});

socket.on('connect', function () {
    socket.emit('my event', { data: 'I\'m connected!' });
    socket.emit('start_emit');
});

window.setInterval(function () {
    // socket.emit('json_request');
}, 33);

socket.on('json_receive', function (json) {
    console.log(json);
});

// サーバーからメッセージを受信したとき
socket.on('dict', function (data) {
    console.log(data);
    let keys = Object.keys(data);
    keys.forEach(function (key) {
        if (document.getElementById(key)) {
            document.getElementById(key).innerText = data[key];
        } else if (key == "logger") {
            if (document.getElementById("logger_content").getElementsByTagName('*').length > 20) {
                document.getElementById("logger_content").firstElementChild.remove();
            }

            // 新しいHTML要素を作成
            let new_element = document.createElement('p');
            new_element.textContent = data[key];
            document.getElementById("logger_content").appendChild(new_element);
        }

    });
});

window.setInterval(function () {
    // Ping計測
    start_time_ping_pong = (new Date).getTime();
    socket.emit('my ping');
}, 1000);


document.addEventListener('DOMContentLoaded', () => {
    // すべてのボタンを取得
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        // ボタンが押された時 (マウス用: mousedown, タッチ用: touchstart)
        button.addEventListener('mousedown', (event) => {
            button_sound();
            if (event.target.id == "python_exit") {
                let result = window.confirm("本当にPythonを終了しますか?");
                if(result){
                    socket.emit('button', { down: event.target.id });
                    location.reload()
                }
            } else {
                // console.log(`Button Pressed: ${event.target.id}`);
                socket.emit('button', { down: event.target.id });
            }
        });
        button.addEventListener('touchstart', (event) => {
            button_sound();
            event.preventDefault(); // タッチスクロールを無効化
            if (event.target.id == "python_exit") {
                let result = window.confirm("本当にPythonを終了しますか?");
                if(result){
                    socket.emit('button', { down: event.target.id });
                    location.reload()
                }
            } else {
                // console.log(`Button Pressed: ${event.target.id}`);
                socket.emit('button', { down: event.target.id });
            }
        });

        // ボタンが離された時 (マウス用: mouseup, タッチ用: touchend)
        button.addEventListener('mouseup', (event) => {
            // console.log(`Button Released: ${event.target.id}`);
            socket.emit('button', { up: event.target.id });
        });
        button.addEventListener('touchend', (event) => {
            event.preventDefault(); // タッチ操作終了後のデフォルト動作を無効化
            // console.log(`Button Released (Touch): ${event.target.id}`);
            socket.emit('button', { up: event.target.id });
        });
    });
});


socket.on('my pong', function () {
    var latency = (new Date).getTime() - start_time_ping_pong;
    document.getElementById('ping').innerText = Math.round(10 * latency) / 10;
    ping_pong_times.push(latency);
    ping_pong_times = ping_pong_times.slice(-10); // keep last 30 samples
    var sum = 0;
    for (var i = 0; i < ping_pong_times.length; i++)
        sum += ping_pong_times[i];
    console.debug("ping: " + Math.round(10 * sum / ping_pong_times.length) / 10 + "ms");
});