import time
import socket  # UDP通信用
from concurrent.futures import ThreadPoolExecutor  # threadPoolExecutor


def UDP_send() -> None:
    # ホスト名を取得、表示
    host = socket.gethostname()
    ip: str = "192.168.179.255"

    count = 0

    while True:
        print(count)
        count += 1

        msg: str = "from_" + host + f"_{count}"

        # ipv4を使うので、AF_INET。udp通信を使いたいので、SOCK_DGRAM
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,
                        1)  # ブロードキャストのための設定
        sock.sendto(msg.encode('utf-8'), (ip, 8000))

        time.sleep(0.001)


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=6) as executor:
        executor.submit(UDP_send)
        # executor.submit(UDP_receive)