import socket
import struct
import time
from typing import Optional
import os
import socket
import ctypes  # 1ms timer
import queue

# from networkx import common_neighbor_centrality

from Robots import Robot
from main import RoboDict
from Robots import Robot_1, Robot_2_1, Robot_2_2, Robot_2_3
from logger_setup import logger

DEBUG_IP:str = "192.168.110.101" # WindowsPCのip
# DEBUG_IP:str = "192.168.110.103" # WindowsPCのip

# OSを判定して適切なスリープ関数を呼び出す
if os.name == "nt":
    # Windowsの場合はkernel32のSleepを使う（ミリ秒単位）
    kernel32 = ctypes.windll.kernel32

    def usleep(microseconds):
        milliseconds = microseconds / 1000  # マイクロ秒からミリ秒に変換
        kernel32.Sleep(int(milliseconds))
elif os.name == "posix":
    # LinuxまたはUnixの場合はlibcのusleepを使う（マイクロ秒単位）
    libc = ctypes.cdll.LoadLibrary('libc.so.6')

    def usleep(microseconds):
        libc.usleep(microseconds)

PORT_BW16 = 8000
PORT_PC = 8001 # BW16 to ONEX
PORT_PC_CONNECTION = 8002

broadcast_address = ""
my_ip_address = ""

def setup():
    global sock, sock_broadcast, broadcast_address, my_ip_address

    # get broadcast ip address
    my_ip_address, broadcast_address = get_ip_and_broadcast()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((my_ip_address, PORT_PC))

    sock_broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock_broadcast.bind(('', PORT_PC_CONNECTION))  # 開けなかった場合の処理が必要
    # sock.setblocking(False)  # ソケットを非同期に設定 これならsettimeoutしなくてもいいかも
    # sock.settimeout(0.1) # TODO 動作を確認


# ID: 0-255, command: 0-255, command_content: int32, uint32, float32
def encode(command_id, command_content, fmt):
    header = struct.pack("<H", command_id)
    if fmt == "i32":
        return header + struct.pack("<l", int(command_content))  # int32
    elif fmt == "ui32":
        return header + struct.pack("<L", int(command_content))  # uint32
    elif fmt == "f32":
        return header + struct.pack("<f", command_content)  # float32
    else:
        return header + struct.pack("<L", int(command_content))  # uint32


def decode(bytes_command_content, fmt):
    if fmt == "i32":
        command_content = struct.unpack("<l", bytes_command_content)[0]
    elif fmt == "ui32":
        command_content = struct.unpack("<L", bytes_command_content)[0]
    elif fmt == "f32":
        command_content = struct.unpack("<f", bytes_command_content)[0]
    else:
        command_content = struct.unpack("<L", bytes_command_content)[0]
    return command_content


def put_queue(ip, command_id, command_content, fmt, queue):
    if ip is not None:
        if command_id is not None:
            try:
                queue.put(encode(command_id, command_content, fmt))
            except Exception as e:
                logger.critical(f"error {e}")


def send_byte(ip, byte):
    if ip is not None:
        try:
            # logger.debug(decode(byte, "ui32"))
            # command_id: int = struct.unpack("<Hxxxx", byte)[0]
            # bytes_command_content: bytes = byte[2:6]
            # logger.debug(f"{ip}:{PORT_BW16} {hex(command_id)} {bytes_command_content}")
            # logger.debug(f"{ip}:{PORT_BW16} {hex(command_id)} {decode(bytes_command_content, 'i32')}")
            # logger.debug(f"send {ip}:{PORT_BW16} {byte.hex()}")
            sock.sendto(byte, (ip, PORT_BW16))
            # sock.sendto(byte, (DEBUG_IP, PORT_BW16))
        except Exception as e:
            logger.critical(f"error {e}")


def send(ip, command_id, command_content, fmt):
    if ip is not None:
        if command_id is not None:
            try:
                sock.sendto(
                    encode(command_id, command_content, fmt), (ip, PORT_BW16))
            except Exception as e:
                logger.critical(f"error {e}")

def receive():
    data, addr = sock.recvfrom(6)
    ip: str = addr[0]
    command_id: int = struct.unpack("<Hxxxx", data)[0]
    bytes_command_content: bytes = data[2:6]
    return ip, command_id, bytes_command_content


def close():
    sock.close()
    sock_broadcast.close()


def get_ip_and_broadcast():
    my_ip_addr = ''
    broadcast_addr = ''
    if os.name == "nt":
        # Windowsの場合
        my_ip_addr = socket.gethostbyname(socket.gethostname())
        # Windowsではブロードキャストアドレスの取得が難しいため、ここでは省略します
        broadcast_addr: str = ".".join(my_ip_addr.split(".")[:3]) + ".255"
    elif os.name == "posix":
        # Linuxの場合
        import netifaces
        if_nameindex_list = socket.if_nameindex()
        for if_nameindex in if_nameindex_list:
            try:
                addrs = netifaces.ifaddresses(if_nameindex[1])
                my_ip_addr = addrs[netifaces.AF_INET][0]['addr']
                broadcast_addr = addrs[netifaces.AF_INET][0]['broadcast']
            except KeyError:
                continue
    return my_ip_addr, broadcast_addr


def connection_send():
    iplist: list = my_ip_address.split('.')
    for i in range(len(iplist)):
        iplist[i] = int(iplist[i])
    sock_broadcast.sendto(b'\xFF\xFF'+bytes(iplist),
                          (broadcast_address, PORT_BW16))
    # logger.info(f"connection_send run {broadcast_address}:{PORT_BW16}")


def connection_receive():
    try:
        data, addr = sock_broadcast.recvfrom(1024)
    except Exception as e:
        logger.critical(f"error {e}")
        return None, None
    else:
        device_name = data.decode()
        return device_name, addr[0]


def send_ping(robo: RoboDict):
    for robot in robo.values():
        if isinstance(robot, (Robot_1, Robot_2_1, Robot_2_2, Robot_2_3)):
            send(robot.ip, 0xFFF1, str(int(time.time_ns()/100))[-9:], "ui32")
            time.sleep(0.2)


if (__name__ == "__main__"):
    logger.debug(f"ip,broadcast: {get_ip_and_broadcast()}")
    setup()
