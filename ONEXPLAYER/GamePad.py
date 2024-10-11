# TODO pygameでgamepad取得してるけどpygame使い勝手よくないから、evdevとかのほうがいいかも

from lib2to3.pytree import convert
from math import e
from sqlite3 import connect
import struct
import copy
from typing import Callable, Literal, Optional, Union
import pygame
import time
from logger_setup import logger
import UDPProtocol
import WebServer

pygame.init()

class gamepad:
    def __init__(self, eventFunc:Callable[[str, Literal["down","up"]],None]) -> None:
        self.axes: dict[str, dict[str, Union[float, int]]] = {
            "L": {
                "x": 0,
                "y": 0
            },
            "R": {
                "x": 0,
                "y": 0
            }
        }

        self.buttons: dict[str, Union[float, int]] = {
            "A": 0,
            "B": 0,
            "X": 0,
            "Y": 0,
            "LB": 0,
            "RB": 0,
            "LT": 0,
            "RT": 0,
            "LS": 0,
            "RS": 0,
            "BACK": 0,
            "START": 0,
            "UP": 0,
            "DOWN": 0,
            "LEFT": 0,
            "RIGHT": 0,
        }

        self.device_name = ""
        self.ip: Optional[str] = None
        self.axes_last = copy.deepcopy(self.axes)
        self.buttons_last = copy.deepcopy(self.buttons)
        self.eventFunc = eventFunc
        self.update_time:float = 0
        # TODO add self.last_update_time

    def eventCaller(self):
        for button_key in self.buttons.keys():
            if (self.buttons[button_key] > 0.5) != (self.buttons_last[button_key] > 0.5):
                self.eventFunc(button_key, "down" if self.buttons[button_key] > 0.5 else "up")



class ELECOM(gamepad):
    def __init__(self, device_name:Literal["P2","P3"], eventFunc:Callable[[str, Literal["down","up"]],None]) -> None:
        super().__init__(eventFunc)
        self.device_name = device_name
        self.RSSI = 0
        self.ping = 0

        self.command_id = {
            "setStickData": 0x2000,
            "setButtonsData": 0x2001,
            "RSSI": 0xFFF0,
            "ping": 0xFFF2
        }

        self.voltage:float = 0

    def setStatus(self, command_id, bytes_command_content):
        self.buttons_last = copy.deepcopy(self.buttons)

        if command_id == self.command_id["setStickData"]:
            datas = struct.unpack("<BBBB", bytes_command_content)

            self.axes["L"]["x"] = (datas[0]/128)-1
            self.axes["L"]["y"] = -(datas[1]/128)+1
            self.axes["R"]["x"] = (datas[2]/128)-1
            self.axes["R"]["y"] = -(datas[3]/128)+1

        elif command_id == self.command_id["setButtonsData"]:
            datas = struct.unpack("<BBBB", bytes_command_content)

            self.buttons["A"] = (datas[0] >> 0) & 1
            self.buttons["B"] = (datas[0] >> 1) & 1
            self.buttons["X"] = (datas[0] >> 2) & 1
            self.buttons["Y"] = (datas[0] >> 3) & 1

            self.buttons["LB"] = (datas[0] >> 4) & 1
            self.buttons["RB"] = (datas[0] >> 5) & 1
            self.buttons["LT"] = (datas[0] >> 6) & 1
            self.buttons["RT"] = (datas[0] >> 7) & 1

            self.buttons["LS"] = (datas[1] >> 0) & 1
            self.buttons["RS"] = (datas[1] >> 1) & 1
            self.buttons["BACK"] = (datas[1] >> 2) & 1
            self.buttons["START"] = (datas[1] >> 3) & 1

            self.buttons["UP"] = (datas[2] >> 0) & 1
            self.buttons["DOWN"] = (datas[2] >> 1) & 1
            self.buttons["LEFT"] = (datas[2] >> 2) & 1
            self.buttons["RIGHT"] = (datas[2] >> 3) & 1

            self.voltage = round(datas[3]*3.3*14.7/10/255, 2)

            self.update_time = time.time()
            self.eventCaller()

        elif command_id == self.command_id["RSSI"]:
            # RSSI
            self.RSSI = UDPProtocol.decode(bytes_command_content, "i32")
            WebServer.send_message_to_clients({self.device_name+"_RSSI": self.RSSI})
            # logger.debug(f"RSSI {self.ip}: {self.RSSI}")

        elif command_id == self.command_id["ping"]:
            logger.info("bbbbbbbbbbbbb")





class GamePad_wired(gamepad):
    def __init__(self, kind:Literal["ONEX","Logicool","ELECOM_wired","DS4_Ubuntu","DS4_Windows"], id:int, eventFunc:Callable[[str, Literal["down","up"]],None]) -> None:
        super().__init__(eventFunc)
        self.kind: Literal['ONEX'] | Literal['Logicool'] | Literal['ELECOM_wired'] | Literal['DS4_Ubuntu'] | Literal['DS4_Windows'] = kind
        self.id = id
        self.connect()

    def connect(self):
        try:
            self.joy = pygame.joystick.Joystick(self.id)
            self.joy.init()
            self.device_name = self.joy.get_name()
            logger.info(f"{self.kind}:{self.device_name}:{self.id} found")
        except Exception as e:
            logger.critical(f"{self.kind}:{self.device_name}:{self.id} not found 接続台数:{pygame.joystick.get_count()}台 {e}")

    # 20msごとにloopさせる必要がある
    def setStatus(self):
        try:
            pygame.event.pump()
            self.buttons_last = copy.deepcopy(self.buttons)

            self.convert() # buttonsとaxesを更新する

            self.update_time = time.time()
            self.eventCaller()

        except AttributeError as e:
            logger.critical(f"{self.kind}:{self.device_name}:{self.id} not found 接続台数:{pygame.joystick.get_count()}台 {e}")
            self.connect()

        except Exception as e:
            logger.critical(f"{self.kind}:{self.id} error {e}")



    def convert(self):
        if self.kind == "ONEX":
            self.axes["L"]["x"] = self.joy.get_axis(0)
            self.axes["L"]["y"] = -self.joy.get_axis(1)
            self.axes["R"]["x"] = self.joy.get_axis(3)
            self.axes["R"]["y"] = -self.joy.get_axis(4)

            self.buttons["A"] = self.joy.get_button(0)
            self.buttons["B"] = self.joy.get_button(1)
            self.buttons["X"] = self.joy.get_button(2)
            self.buttons["Y"] = self.joy.get_button(3)

            self.buttons["LB"] = self.joy.get_button(4)
            self.buttons["RB"] = self.joy.get_button(5)

            self.buttons["LT"] = (self.joy.get_axis(2)+1)/2
            self.buttons["RT"] = (self.joy.get_axis(5)+1)/2

            self.buttons["LS"] = self.joy.get_button(9)
            self.buttons["RS"] = self.joy.get_button(10)

            self.buttons["BACK"] = self.joy.get_button(6)
            self.buttons["START"] = self.joy.get_button(7)

            hat = self.joy.get_hat(0)
            self.buttons["UP"] = 1 if hat[1] > 0 else 0
            self.buttons["DOWN"] = 1 if hat[1] < 0 else 0
            self.buttons["LEFT"] = 1 if hat[0] < 0 else 0
            self.buttons["RIGHT"] = 1 if hat[0] > 0 else 0

        elif self.kind == "Logicool":
            self.axes["L"]["x"] = self.joy.get_axis(0)
            self.axes["L"]["y"] = -self.joy.get_axis(1)
            self.axes["R"]["x"] = self.joy.get_axis(3)
            self.axes["R"]["y"] = -self.joy.get_axis(4)

            self.buttons["A"] = self.joy.get_button(0)
            self.buttons["B"] = self.joy.get_button(1)
            self.buttons["X"] = self.joy.get_button(2)
            self.buttons["Y"] = self.joy.get_button(3)

            self.buttons["LB"] = self.joy.get_button(4)
            self.buttons["RB"] = self.joy.get_button(5)

            self.buttons["LT"] = (self.joy.get_axis(2)+1)/2
            self.buttons["RT"] = (self.joy.get_axis(5)+1)/2

            self.buttons["LS"] = self.joy.get_button(9)
            self.buttons["RS"] = self.joy.get_button(10)

            self.buttons["BACK"] = self.joy.get_button(6)
            self.buttons["START"] = self.joy.get_button(7)

            hat = self.joy.get_hat(0)
            self.buttons["UP"] = 1 if hat[1] > 0 else 0
            self.buttons["DOWN"] = 1 if hat[1] < 0 else 0
            self.buttons["LEFT"] = 1 if hat[0] < 0 else 0
            self.buttons["RIGHT"] = 1 if hat[0] > 0 else 0

        elif self.kind == "DS4_Ubuntu":
            self.axes["L"]["x"] = self.joy.get_axis(0)
            self.axes["L"]["y"] = -self.joy.get_axis(1)
            self.axes["R"]["x"] = self.joy.get_axis(3)
            self.axes["R"]["y"] = -self.joy.get_axis(4)

            self.buttons["A"] = self.joy.get_button(0)
            self.buttons["B"] = self.joy.get_button(1)
            self.buttons["X"] = self.joy.get_button(3)
            self.buttons["Y"] = self.joy.get_button(2)

            self.buttons["LB"] = self.joy.get_button(4)
            self.buttons["RB"] = self.joy.get_button(5)

            self.buttons["LT"] = self.joy.get_button(6)
            self.buttons["RT"] = self.joy.get_button(7)

            # self.buttons["LS"] = self.joy.get_button(11)
            # self.buttons["RS"] = self.joy.get_button(12)

            self.buttons["BACK"] = self.joy.get_button(8)
            self.buttons["START"] = self.joy.get_button(9)

            hat = self.joy.get_hat(0)
            self.buttons["UP"] = 1 if hat[1] > 0 else 0
            self.buttons["DOWN"] = 1 if hat[1] < 0 else 0
            self.buttons["LEFT"] = 1 if hat[0] < 0 else 0
            self.buttons["RIGHT"] = 1 if hat[0] > 0 else 0

            # 8 is PS button

        elif self.kind == "ELECOM_wired":
            self.axes["L"]["x"] = self.joy.get_axis(0)
            self.axes["L"]["y"] = -self.joy.get_axis(1)
            self.axes["R"]["x"] = self.joy.get_axis(2)
            self.axes["R"]["y"] = -self.joy.get_axis(3)

            self.buttons["A"] = self.joy.get_button(0)
            self.buttons["B"] = self.joy.get_button(1)
            self.buttons["X"] = self.joy.get_button(2)
            self.buttons["Y"] = self.joy.get_button(3)

            self.buttons["LB"] = self.joy.get_button(4)
            self.buttons["RB"] = self.joy.get_button(5)

            self.buttons["LT"] = self.joy.get_button(6)
            self.buttons["RT"] = self.joy.get_button(7)

            self.buttons["LS"] = self.joy.get_button(8)
            self.buttons["RS"] = self.joy.get_button(9)

            self.buttons["BACK"] = self.joy.get_button(10)
            self.buttons["START"] = self.joy.get_button(11)

            hat = self.joy.get_hat(0)
            self.buttons["UP"] = 1 if hat[1] > 0 else 0
            self.buttons["DOWN"] = 1 if hat[1] < 0 else 0
            self.buttons["LEFT"] = 1 if hat[0] < 0 else 0
            self.buttons["RIGHT"] = 1 if hat[0] > 0 else 0

        elif self.kind == "DS4_Windows":
            self.axes["L"]["x"] = self.joy.get_axis(0)
            self.axes["L"]["y"] = -self.joy.get_axis(1)
            self.axes["R"]["x"] = self.joy.get_axis(2)
            self.axes["R"]["y"] = -self.joy.get_axis(3)

            self.buttons["A"] = self.joy.get_button(0)
            self.buttons["B"] = self.joy.get_button(1)
            self.buttons["X"] = self.joy.get_button(2)
            self.buttons["Y"] = self.joy.get_button(3)

            self.buttons["LB"] = self.joy.get_button(9)
            self.buttons["RB"] = self.joy.get_button(10)

            self.buttons["LT"] = (self.joy.get_axis(4)+1)/2
            self.buttons["RT"] = (self.joy.get_axis(5)+1)/2

            self.buttons["LS"] = self.joy.get_button(7)
            self.buttons["RS"] = self.joy.get_button(8)

            self.buttons["BACK"] = self.joy.get_button(4)
            self.buttons["START"] = self.joy.get_button(6)

            self.buttons["UP"] = self.joy.get_button(11)
            self.buttons["DOWN"] = self.joy.get_button(12)
            self.buttons["LEFT"] = self.joy.get_button(13)
            self.buttons["RIGHT"] = self.joy.get_button(14)

# print(self.joy.get_numaxes(),self.joy.get_numbuttons(),self.joy.get_numhats(),self.joy.get_numballs())
# print("4",self.joy.get_button(4),"5",self.joy.get_button(5),"6",self.joy.get_button(6),"7",self.joy.get_button(7),"8",self.joy.get_button(8),"9",self.joy.get_button(9),"10",self.joy.get_button(10),"11",self.joy.get_button(11),"12",self.joy.get_button(12),"13",self.joy.get_button(13),"14",self.joy.get_button(14),"15",self.joy.get_button(15))
# print(self.joy.get_hat(0))
# print(self.joy.get_axis(0),self.joy.get_axis(1),self.joy.get_axis(2),self.joy.get_axis(3),self.joy.get_axis(4),self.joy.get_axis(5))
