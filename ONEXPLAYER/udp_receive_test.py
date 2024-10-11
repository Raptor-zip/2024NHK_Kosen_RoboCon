from socket import socket, AF_INET, SOCK_DGRAM
import UDPProtocol
import struct
# import logger_setup
from logger_setup import logger

HOST = ''

UDPProtocol.setup()

sock = socket(AF_INET, SOCK_DGRAM)
sock.bind((HOST, UDPProtocol.PORT_BW16))

while True:
    # 受信
    # ip, command_id, bytes_command_content = UDPProtocol.receive()

    # print(f"{ip}: {hex(command_id)}  {UDPProtocol.decode(bytes_command_content, 'ui32')}")

    # msg, address = s.recvfrom(8192)

    data, addr = sock.recvfrom(6)
    ip: str = addr[0]
    command_id: int = struct.unpack("<Hxxxx", data)[0]
    bytes_command_content: bytes = data[2:6]
    logger.info(f"from: {ip}: {hex(command_id)} {UDPProtocol.decode(bytes_command_content, 'ui32')}")

# ソケットを閉じておく
s.close()
