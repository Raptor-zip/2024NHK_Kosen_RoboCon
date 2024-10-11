import math
import os
import sys
import time
import ctypes  # timer
import datetime

from sympy import Li
import UDPProtocol
from concurrent.futures import ThreadPoolExecutor
import Robots
import GamePad
import WebServer
# import global_value as g
from typing import Literal, Optional, Dict, Union, TypedDict, Final
from logger_setup import logger

class RoboDict(TypedDict):
    R1: Robots.Robot_1
    R21: Robots.Robot_2_1
    R22: Robots.Robot_2_2
    R23: Robots.Robot_2_3
    
robo: RoboDict = {
    "R1": Robots.Robot_1("R1"),
    "R21": Robots.Robot_2_1("R21"),
    "R22": Robots.Robot_2_2("R22"),
    "R23": Robots.Robot_2_3("R23")
}

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

def UDP_ReceiveTask():
    global gamePad
    while True:
        try:
            # logger.info("start")
            ip, command_id, bytes_command_content = UDPProtocol.receive()
            # logger.debug(f"rec {ip} {hex(command_id)} {UDPProtocol.decode(bytes_command_content, 'i32')}")
            for robot in robo.values():
                if isinstance(robot, (Robots.Robot_1, Robots.Robot_2_1, Robots.Robot_2_2, Robots.Robot_2_3)):
                    if robot.ip == ip:
                        logger.debug(f"rec {ip} {hex(command_id)} {UDPProtocol.decode(bytes_command_content, 'i32')}")
                        robot.setFeedback(command_id,  bytes_command_content)
            for gamePad_ in gamePad.values():
                if isinstance(gamePad_, (GamePad.ELECOM)):
                    if gamePad_.ip == ip:
                        gamePad_.setStatus(command_id, bytes_command_content)
            # logger.info("end")
        except Exception as e:
            logger.critical(f"error: {e}")
        usleep(1 * 1000)  # TODO もっと小さくできる？今どのくらいか実験


def WebServer_EventCallback(button, event, robo:RoboDict, gamePad) -> None:
    logger.debug(f"Web {button} {event}")
    # velocity_limit = 10000
    if event == "down":
        if button == "python_exit":
            logger.warning("Python強制終了")
            os._exit(0)

        elif button == "add_delay":
            robo["R1"].UDP_delay += 1 * 1000
            robo["R21"].UDP_delay += 1 * 1000
            robo["R22"].UDP_delay += 1 * 1000
            robo["R23"].UDP_delay += 1 * 1000
            logger.debug(f"add_delay: {robo['R1'].UDP_delay}")
        elif button == "reduce_delay":
            robo["R1"].UDP_delay -= 1 * 1000
            robo["R21"].UDP_delay -= 1 * 1000
            robo["R22"].UDP_delay -= 1 * 1000
            robo["R23"].UDP_delay -= 1 * 1000
            logger.debug(f"reduce_delay: {robo['R1'].UDP_delay}")
            
        elif button == "R1_set_M3508_origin": # TODO GUIのやつ長押し用とすると事故って左クリック判定みたいになる ボタンでかくする？
            robo["R1"].RM_pull_state = 1

        elif button == "R1_set_M3508_default_position":
            robo["R1"].RM_pull_state = 2

        elif button == "R1_initialize":
            robo['R1'].initialize()
            logger.info("R1_initialize")

        elif button == "R1_Cyber_tension_ResetPosition":
            robo['R1'].Cyber_tension.ResetPosition()
            robo['R1'].Cyber_tension_position = 0

        elif button == "R1_servo_small_prepare":
            robo['R1'].servo_small.setPosition(0)
            logger.info("R1_servo_small_prepare 0")
            WebServer.send_message_to_clients({"R1.servo_small_position": robo['R1'].servo_small.target_value})
        elif button == "R1_servo_big_prepare":
            robo['R1'].servo_big.setPosition(0)
            logger.info("R1_servo_big_prepare 0")
            WebServer.send_message_to_clients({"R1.servo_big_position": robo['R1'].servo_big.target_value})

        elif button == "R2-1_collect_servo":
            robo["R21"].sendServoAngle(110)
            WebServer.send_message_to_clients({"R21.servo_position": 110})
            logger.info("R2-1 servo push 110")

        elif button == "R2-1_lock_servo":
            robo["R21"].sendServoAngle(90)
            WebServer.send_message_to_clients({"R21.servo_position": 90})
            logger.info("R2-1 servo lock 90")

        elif button == "R2-2_initialize":
            robo['R22'].initialize()
            logger.info("R2-2 initialize")

        elif button == "R2-2_collect_fast":
            robo['R22'].collect_abjust += 500

        elif button == "R2-2_collect_slow":
            robo['R22'].collect_abjust -= 500

        elif button == "R2-3_initialize":
            robo['R23'].initialize()
            WebServer.send_message_to_clients({"R23.servo_position": 0})
            WebServer.send_message_to_clients({"R23.Cyber_position": int(math.degrees(robo['R23'].Cyber_position))})

        elif button == "R2-3_Cyber_free":
            robo['R23'].Cyber_SetFree()
            WebServer.send_message_to_clients({"R23.Cyber_position": int(math.degrees(robo['R23'].Cyber_position))})

        elif button == "R2-3_Cyber_up":
            robo['R23'].Cyber_SetPositionRelative(math.radians(5))
            WebServer.send_message_to_clients({"R23.Cyber_position": int(math.degrees(robo['R23'].Cyber_position))})

        elif button == "R2-3_Cyber_down":
            robo['R23'].Cyber_SetPositionRelative(math.radians(-5))
            WebServer.send_message_to_clients({"R23.Cyber_position": int(math.degrees(robo['R23'].Cyber_position))})

        elif button == "R2-3_Cyber_collect":
            position = 150
            robo['R23'].Cyber_right.SpeedLimit(2.0)
            robo['R23'].Cyber_left.SpeedLimit(2.0)
            robo['R23'].Cyber_right.ControlPosition(math.radians(position))
            robo['R23'].Cyber_left.ControlPosition(-1 * math.radians(position))
            WebServer.send_message_to_clients({"R23.Cyber_position": position})

        elif button == "R2-3_servo_lock":
            robo['R23'].servo.setPosition(-30)
            WebServer.send_message_to_clients({"R23.servo_position": robo['R23'].servo.target_value})
            logger.info(f"R2-3 servo release {robo['R23'].servo.target_value}")

        elif button == "R2-3_servo_release":
            robo['R23'].servo.setPosition(20)
            WebServer.send_message_to_clients({"R23.servo_position": robo['R23'].servo.target_value})
            logger.info(f"R2-3 servo release {robo['R23'].servo.target_value}")
            
        elif button == "GP2_change_wired":
            gamePad["P2"] = GamePad.GamePad_wired("Logicool", 1, GamePad_2_EventCallback)
        elif button == "GP2_change_wireless":
            gamePad["P2"] = GamePad.ELECOM("P2",GamePad_2_EventCallback)
        elif button == "GP3_change_wired":
            gamePad["P3"] = GamePad.GamePad_wired("Logicool", 1, GamePad_3_EventCallback)
        elif button == "GP3_change_wireless":
            gamePad["P3"] = GamePad.ELECOM("P3",GamePad_3_EventCallback)
            

    elif event == "up":
        if button == "R2-1_collect_servo":
            robo["R21"].sendServoAngle(65)
            WebServer.send_message_to_clients({"R21.servo_position": 65})
            logger.info("R2-1 servo pull 65")
            
        elif button == "R1_wheel_turn":
            # 旋回解除
            robo["R1"].wheel_FL.setVelocityLimit(18000)
            robo["R1"].wheel_FR.setVelocityLimit(18000)
            robo["R1"].wheel_RL.setVelocityLimit(18000)
            robo["R1"].wheel_RR.setVelocityLimit(18000)
            robo["R1"].wheel_state = "normal"
            
        elif button == "R1_wheel_diagonal":
            # 斜め移動解除
            robo["R1"].wheel_FL.setVelocityLimit(18000)
            robo["R1"].wheel_FR.setVelocityLimit(18000)
            robo["R1"].wheel_RL.setVelocityLimit(18000)
            robo["R1"].wheel_RR.setVelocityLimit(18000)
            robo["R1"].wheel_state = "normal"

        elif button == "R1_set_M3508_origin":
            robo["R1"].RM_pull_state = 0
            robo['R1'].RM_pull.resetZEROPosition()
            robo['R1'].RM_pull_position = 0

        elif button == "R1_set_M3508_default_position":
            robo["R1"].RM_pull_state = 0
            robo['R1'].RM_pull_position = int(-40200 * 0.7)

        elif button == "R2-3_Cyber_collect":
            position = 30
            robo['R23'].Cyber_right.SpeedLimit(1.0)
            robo['R23'].Cyber_left.SpeedLimit(1.0)
            robo['R23'].Cyber_right.ControlPosition(
                math.radians(position))
            robo['R23'].Cyber_left.ControlPosition(
                -1 * math.radians(position))
            WebServer.send_message_to_clients({"R23.Cyber_position": int(math.degrees(robo['R23'].Cyber_right.target_value))})


def GamePad_1_EventCallback(button:str, event:Literal["down","up"]) -> None:
    logger.debug(f"GamePad1 {button} {event}")
    
    velocity_limit = 10000
    
    if event == "down":
        if button == "LS":
            robo['R1'].initialize()
            logger.info("R1 initlialie 174")

        elif button == "BACK":
            # inject R22
            robo['R1'].servo_big.setPosition(40)
            # robo['R1'].servo_big.setPosition(25)
            logger.info("inject R2-2")
            WebServer.send_message_to_clients({"R1.servo_big_position": robo['R1'].servo_big.target_value})

        elif button == "UP":
            robo['R1'].Cyber_pull.ControlPositionRelative(math.radians(-60))
            logger.info(f"push Cyber_push {robo['R1'].Cyber_pull.position_relatice_sum}")
            WebServer.send_message_to_clients({"R1_Cyber_position": int(math.degrees(robo['R1'].Cyber_pull.position_relatice_sum))})
        elif button == "DOWN":            
            robo['R1'].Cyber_pull.ControlPositionRelative(math.radians(60))
            logger.info(f"push Cyber_push {robo['R1'].Cyber_pull.position_relatice_sum}")
            WebServer.send_message_to_clients({"R1_Cyber_position": int(math.degrees(robo['R1'].Cyber_pull.position_relatice_sum))})

        elif button == "RIGHT":
            robo["R1"].wheelAssist_direction = "right"
            robo["R1"].wheel_FL.resetZEROPosition()
            robo["R1"].wheel_FL.setVelocityLimit(velocity_limit)
            robo["R1"].wheel_FR.resetZEROPosition()
            robo["R1"].wheel_FR.setVelocityLimit(velocity_limit)
            robo["R1"].wheel_RL.resetZEROPosition()
            robo["R1"].wheel_RL.setVelocityLimit(velocity_limit)
            robo["R1"].wheel_RR.resetZEROPosition()
            robo["R1"].wheel_RR.setVelocityLimit(velocity_limit)
            robo["R1"].wheel_state = "diagonal"
            
        elif button == "LEFT":
            robo["R1"].wheelAssist_direction = "left"
            robo["R1"].wheel_FL.resetZEROPosition()
            robo["R1"].wheel_FL.setVelocityLimit(velocity_limit)
            robo["R1"].wheel_FR.resetZEROPosition()
            robo["R1"].wheel_FR.setVelocityLimit(velocity_limit)
            robo["R1"].wheel_RL.resetZEROPosition()
            robo["R1"].wheel_RL.setVelocityLimit(velocity_limit)
            robo["R1"].wheel_RR.resetZEROPosition()
            robo["R1"].wheel_RR.setVelocityLimit(velocity_limit)
            robo["R1"].wheel_state = "diagonal"

        elif button == "Y":
            robo['R1'].Cyber_pull.ControlPositionRelative(-4*math.pi)
            logger.info(f"push Cyber_push {robo['R1'].Cyber_pull.position_relatice_sum}")
            WebServer.send_message_to_clients({"R1_Cyber_position": int(math.degrees(robo['R1'].Cyber_pull.position_relatice_sum))})        
            # robo["R1"].Cyber_pull.ControlSpeed_SetMode(5)
        elif button == "A":
            robo['R1'].Cyber_pull.ControlPositionRelative(4*math.pi)
            logger.info(f"push Cyber_push {robo['R1'].Cyber_pull.position_relatice_sum}")
            WebServer.send_message_to_clients({"R1_Cyber_position": int(math.degrees(robo['R1'].Cyber_pull.position_relatice_sum))})
            # robo["R1"].Cyber_pull.ControlSpeed_SetMode(-5)

        elif button == "LB":
            robo['R1'].is_wheel_slow = not robo['R1'].is_wheel_slow
            logger.info(f"R1 wheel slow: {robo['R1'].is_wheel_slow}")

    if event == "up":
        if button == "BACK":
            robo['R1'].servo_big.setPosition(0)

            # robo['R1'].servo_big.setPosition(5)
            logger.info("inject R22 release")
            WebServer.send_message_to_clients({"R1.servo_big_position": robo['R1'].servo_big.target_value})

        elif button == "RIGHT" or button == "LEFT":
            # 斜め移動解除
            robo["R1"].wheel_FL.setVelocityLimit(18000)
            robo["R1"].wheel_FR.setVelocityLimit(18000)
            robo["R1"].wheel_RL.setVelocityLimit(18000)
            robo["R1"].wheel_RR.setVelocityLimit(18000)
            robo["R1"].wheel_state = "normal"


def GamePad_2_EventCallback(button, event):
    logger.debug(f"GamePad2 {button} {event}")
    if event == "down":
        if button == "LS":
            robo['R22'].initialize()
            
        elif button == "LB":
            if robo["R22"].collect_state != "Reversing":
                robo['R22'].collect_state = "Reversing"
            else:
                robo['R22'].collect_state = "stop"
                
            logger.info(f"R22 collect {robo['R22'].collect_state}")

        elif button == "RB":
            if robo["R22"].collect_state != "forward":
                robo['R22'].collect_state = "forward"
            else:
                robo['R22'].collect_state = "stop"
                
            logger.info(f"R22 collect {robo['R22'].collect_state}")

        elif button == "B":
            robo['R22'].is_wheel_slow = not robo['R22'].is_wheel_slow
            logger.info(f"R22 wheel slow: {robo['R22'].is_wheel_slow}")

        elif button == "DOWN":
            robo['R22'].is_collect_fast = not robo['R22'].is_collect_fast
            logger.info(f"R2 collect fast: {robo['R22'].is_collect_fast}")

        elif button == "RIGHT":
            robo['R22'].collect_abjust += 500
        elif button == "LEFT":
            robo['R22'].collect_abjust -= 500


def GamePad_3_EventCallback(button, event):
    logger.debug(f"GamePad3 {button} {event}")
    if event == "down":
        if button == "A":
            robo['R23'].Cyber_SetFree()
            logger.info(f"Cyber set free")

        elif button == "B":
            robo['R23'].Cyber_left.SpeedLimit(30)
            robo['R23'].Cyber_right.SpeedLimit(30)
        
        elif button == "X":
            # Cyberを垂直から水平に倒す
            robo['R23'].Cyber_left.SpeedLimit(10)
            robo['R23'].Cyber_right.SpeedLimit(10)
            robo['R23'].Cyber_left.ControlPosition(math.radians(0))
            robo['R23'].Cyber_right.ControlPosition(math.radians(0))

        elif button == "LS":
            robo['R23'].initialize()
            WebServer.send_message_to_clients({"R23.servo_position": 0})            
            WebServer.send_message_to_clients({"R23.Cyber_position": int(math.degrees(robo['R23'].Cyber_position))})


        elif button == "LB":
            robo['R23'].is_wheel_slow = not robo['R23'].is_wheel_slow
            logger.info(f"R23 wheel slow: {robo['R23'].is_wheel_slow}")

        elif button == "RB":
            # robo['R22'].collect_L.
            # robo['R22'].collect_R.
            logger.info(f"R22パタパタ 位置調整")

        elif button == "UP":
            robo['R23'].Cyber_SetPositionRelative(math.radians(2))
            WebServer.send_message_to_clients({"R23.Cyber_position": int(math.degrees(robo['R23'].Cyber_position))})
        elif button == "DOWN":
            robo['R23'].Cyber_SetPositionRelative(math.radians(-2))
            WebServer.send_message_to_clients({"R23.Cyber_position": int(math.degrees(robo['R23'].Cyber_position))})
        
        elif button == "BACK":
            robo["R23"].servo_position = 105
            # robo['R23'].servo.setPosition(105)
            # WebServer.send_message_to_clients({"R23.servo_position": robo['R23'].servo.target_value})
            # logger.info(f"R2-3 servo release {robo['R23'].servo.target_value}")

        elif button == "START":
            robo["R23"].servo_position = 35
            # robo['R23'].servo.setPosition(35)
            # robo['R23'].servo.setPosition(-30)
            # WebServer.send_message_to_clients({"R23.servo_position": robo['R23'].servo.target_value})
            # logger.info(f"R2-3 servo release {robo['R23'].servo.target_value}")


def R1_ControlLoop():
    global gamePad
    while True:
        try:
            if robo["R1"].wheel_state == "normal":
                R1Wheels = robo['R1'].wheels.calc(
                    (gamePad["P1"].axes["R"]["x"],
                    gamePad["P1"].axes["R"]["y"]),
                    gamePad["P1"].axes["L"]["x"] * -0.5)
                if robo['R1'].is_wheel_slow:
                    R1Wheels = [int(speed * 100 * 36) for speed in R1Wheels]
                else:
                    R1Wheels = [int(speed * 500 * 36) for speed in R1Wheels]
                robo['R1'].wheel_FL.setVelocity(R1Wheels[0])
                robo['R1'].wheel_FR.setVelocity(R1Wheels[1])
                robo['R1'].wheel_RL.setVelocity(R1Wheels[2])
                robo['R1'].wheel_RR.setVelocity(R1Wheels[3])
                
            elif robo["R1"].wheel_state == "turn":
                _sign = 1
                if robo["R1"].wheelAssist_direction == "left": # 赤チームならマイナスに旋回させる
                    _sign = -1
                    
                variation = 8000
                robo["R1"].wheel_FL.setPosition(variation * _sign)
                robo["R1"].wheel_FR.setPosition(variation * _sign)
                robo["R1"].wheel_RL.setPosition(variation * _sign)
                robo["R1"].wheel_RR.setPosition(variation * _sign)
                
            elif robo["R1"].wheel_state == "diagonal":
                _sign = 1
                if robo["R1"].wheelAssist_direction == "left": # 赤チームならマイナスに旋回させる
                    _sign = -1
                    
                R1Wheels = robo['R1'].wheels.calc((1,1),0)
                variation = 20000
                robo["R1"].wheel_FL.setPosition(R1Wheels[0] * variation * _sign)
                robo["R1"].wheel_FR.setPosition(R1Wheels[1] * variation * _sign)
                robo["R1"].wheel_RL.setPosition(R1Wheels[2] * variation * _sign)
                robo["R1"].wheel_RR.setPosition(R1Wheels[3] * variation * _sign)

            byte_combined = bytes()
            while not robo['R1'].udp_send_queue.empty():
                # bytes
                byte_combined += robo['R1'].udp_send_queue.get()
                # UDPProtocol.send_byte(robo['R1'].ip, robo['R1'].udp_send_queue.get())
                # usleep(robo['R1'].UDP_delay)

            if byte_combined != b"":
                UDPProtocol.send_byte(robo['R1'].ip, byte_combined)

            robo['R1'].command_send_number += 1
        except Exception as e:
            logger.critical(f"error: {e}")
        # usleep(3 * 1000)

        usleep(robo['R1'].UDP_delay)

def R2_2_ControlLoop():
    global gamePad
    while True:
        try:
            # collect motor
            collect_velocity:int = 0
            if robo['R22'].collect_state != "stop":
                if robo['R22'].is_collect_fast:
                    collect_velocity = 8000 + robo['R22'].collect_abjust
                else:
                    collect_velocity = 11000 + robo['R22'].collect_abjust
            
            if robo["R22"].collect_state == "Reversing":
                collect_velocity *= -1
                
            robo['R22'].collect_L.setVelocity(-1 * collect_velocity)
            robo['R22'].collect_R.setVelocity(collect_velocity)
            # logger.debug(f"R22 collect_velocity {collect_velocity}")
            # WebServer.send_message_to_clients({"R22.collect_setting": collect_velocity})

            # wheel motor
            R22Wheels = robo['R22'].wheels.calc(
                (gamePad["P2"].axes["R"]["x"], gamePad["P2"].axes["R"]["y"]), gamePad["P2"].axes["L"]["x"] * -0.3)
            if robo['R22'].is_wheel_slow:
                R22Wheels = [int(speed * 100 * 36) for speed in R22Wheels]
            else:
                R22Wheels = [int(speed * 500 * 36) for speed in R22Wheels]
            
            if R22Wheels[1] > 0 and R22Wheels[2] < 0: # TODO 動作確認
                R22Wheels[1] = int(R22Wheels[1] * 0.3)
                R22Wheels[2] = int(R22Wheels[2] * 0.3)
                    
            robo['R22'].wheel_F.setVelocity(R22Wheels[0])
            robo['R22'].wheel_RL.setVelocity(R22Wheels[1])
            robo['R22'].wheel_RR.setVelocity(R22Wheels[2])
            # WebServer.send_message_to_clients({"R22.wheel_F_setting": robo['R22'].wheel_F.target_value})
            # WebServer.send_message_to_clients({"R22.wheel_RL_setting": robo['R22'].wheel_RL.target_value})
            # WebServer.send_message_to_clients({"R22.wheel_RR_setting": robo['R22'].wheel_RR.target_value})
            # logger.info(f"R22Wheels:{R22Wheels}")


            byte_combined = bytes()
            while not robo['R22'].udp_send_queue.empty():
                # bytes
                byte_combined += robo['R22'].udp_send_queue.get()
                # UDPProtocol.send_byte(robo['R22'].ip, robo['R22'].udp_send_queue.get())
                # usleep(robo['R22'].UDP_delay)

            if byte_combined != b"":
                UDPProtocol.send_byte(robo['R22'].ip, byte_combined)

            robo['R22'].command_send_number += 1
        except Exception as e:
            logger.critical(f"error: {e}")
        # usleep(3 * 1000)

        usleep(robo['R22'].UDP_delay)


def R2_3_ControlLoop():
    global gamePad
    while True:
        current_time_ms = int(time.time() * 1000)
        # print(f"現在の時刻 (ms): {current_time_ms}")
        try:
            # logger.info(f"{gamePad['P3'].status['JoyStick']['L']['y']}")
            if robo['R23'].is_wheel_slow:
                robo['R23'].wheel_left.setVelocity(int(
                    gamePad["P3"].axes["L"]["y"] * 20 * 36))
                robo['R23'].wheel_right.setVelocity(int(
                    gamePad["P3"].axes["R"]["y"] * 20 * 36 * -1))
            else:
                robo['R23'].wheel_left.setVelocity(int(
                    gamePad["P3"].axes["L"]["y"] * 50 * 36))
                robo['R23'].wheel_right.setVelocity(int(
                    gamePad["P3"].axes["R"]["y"] * 50 * 36 * -1))
            # WebServer.send_message_to_clients({"R22.wheel_left_setting": robo['R23'].wheel_left.target_value})
            # WebServer.send_message_to_clients({"R22.wheel_right_setting": robo['R23'].wheel_right.target_value})

            robo['R23'].servo.setPosition(robo["R23"].servo_position)

            if gamePad["P3"].buttons["B"]:
                time_now = datetime.datetime.now()
                time_difference = time_now - robo['R23'].last_set_time
                time_difference_ms = int(
                    time_difference.total_seconds() * 1000)  # 秒をミリ秒に変換してintに変換
                # print(time_difference_ms)
                if time_difference_ms > 20:
                    robo['R23'].last_set_time = time_now
                    Cyber_position_summed:float = 0
                    if math.degrees(robo['R23'].Cyber_position) < -90:
                        Cyber_position_summed = robo['R23'].Cyber_position + math.radians(-0.2)
                    else:
                        Cyber_position_summed = robo['R23'].Cyber_position + math.radians(-0.6)
                    print(Cyber_position_summed)
                    if math.radians(-190) < Cyber_position_summed < 0:
                        robo['R23'].Cyber_position = Cyber_position_summed
                        robo['R23'].Cyber_left.ControlPosition(
                            robo['R23'].Cyber_position)
                        robo['R23'].Cyber_right.ControlPosition(
                            -1 * robo['R23'].Cyber_position)
                        logger.info("R2-3 Cyber up %f",
                                    robo['R23'].Cyber_position)
                        WebServer.send_message_to_clients({"R23.Cyber_position": int(math.degrees(robo['R23'].Cyber_position))})
                    else:
                        logger.error("R2-3 Cyber over 0 ~ -190deg limit")

            byte_combined = bytes()
            while not robo['R23'].udp_send_queue.empty():
                # bytes
                byte_combined += robo['R23'].udp_send_queue.get()
                # UDPProtocol.send_byte(robo['R23'].ip, robo['R23'].udp_send_queue.get())
                # usleep(robo['R23'].UDP_delay)

            if byte_combined != b"":
                UDPProtocol.send_byte(robo['R23'].ip, byte_combined)

            robo['R23'].command_send_number += 1
        except Exception as e:
            logger.critical(f"error: {e}")
        # usleep(3 * 1000)

        usleep(robo['R23'].UDP_delay)


def GamePad_update():
    global gamePad
    while (True):
        try:
            for key, gamePad_ in gamePad.items():
                if isinstance(gamePad_, (GamePad.GamePad_wired)):
                    gamePad_.setStatus()
                if isinstance(gamePad_, GamePad.ELECOM) and (time.time() - gamePad_.update_time) > 0.5: # タイムアウト 本当は有線のもタイムアウト処理したかったけど、pygameがゴミで無理
                    logger.critical(f"ELECOM timed out key:{key} device_name:{gamePad_.device_name}")
        except Exception as e:
            logger.critical(f"error: {e}")
        usleep(20 * 1000)


def UDP_Connection_SendTask():
    while True:
        try:
            UDPProtocol.connection_send()
        except Exception as e:
            logger.critical(f"error: {e}")
        time.sleep(0.5)


def UDP_Connection_ReceiveTask():
    global gamePad
    # robo["R1"].ip= "192.168.110.101"
    while True:
        try:
            device_name, ip = UDPProtocol.connection_receive()
            if device_name is not None:
                # logger.debug(f"receive_connection device_name: {device_name}, ip: {ip}")
                if device_name in robo:
                    if robo[device_name].ip is not None and robo[device_name].ip != ip:
                        logger.critical(
                            f"device_name: {device_name}, new_ip: {ip}, registered_ip: {robo[device_name].ip} is already registered")
                        # logger.debug(f"robo: {robo[device_name]} ip: {ip}")
                    robo[device_name].ip = ip
                for key, value in gamePad.items():
                    if isinstance(value, GamePad.gamepad):
                        if value.device_name == device_name:
                            if gamePad[key].ip is not None and gamePad[key].ip != ip:
                                logger.critical(
                                    f"device_name: {key}, new_ip: {ip}, registered_ip: {gamePad[key].ip} is already registered")
                            gamePad[key].ip = ip
                            # logger.debug(f"gamePad: {gamePad[device_name]} ip: {ip}")
        except Exception as e:
            logger.critical(f"error: {e}")
        usleep(1 * 1000)


def UDP_SendPing():
    while True:
        try:
            UDPProtocol.send_ping(robo)
            # logger.info(f"{robo['R1'].wheel_FL.feedback}")
        except Exception as e:
            logger.critical(f"error: {e}")
        time.sleep(0.2)


def WebServer_update():
    global gamePad,robo
    while True:
        try:
            send_list:dict = {
                # "R1.wheel_FL_feedback" : robo['R1'].wheel_FL.feedback["current"],
                # "R1.wheel_FL_feedback" : robo['R1'].wheel_FL.feedback["velocity"],
                # "R1.wheel_FR_feedback" : robo['R1'].wheel_FR.feedback["velocity"],
                # "R1.wheel_RL_feedback" : robo['R1'].wheel_RL.feedback["velocity"],
                # "R1.wheel_RR_feedback" : robo['R1'].wheel_RR.feedback["velocity"],
                "UDP_delay": robo['R1'].UDP_delay/1000,
                "R1.is_wheel_slow": robo["R1"].is_wheel_slow,
                "R22.is_wheel_slow": robo["R22"].is_wheel_slow,
            }

            for key, gamePad_ in gamePad.items():
                if isinstance(gamePad_, (GamePad.ELECOM)):
                    send_list[key+"_battery"] = gamePad_.voltage
                if isinstance(gamePad_, (GamePad.gamepad)):
                    send_list[key+"_name"] = gamePad_.device_name

            my_ip_address, _ = UDPProtocol.get_ip_and_broadcast()
            send_list["my_ip_address"] = my_ip_address

            # logger.debug(f"R23 left {robo['R23'].wheel_left.feedback['velocity']}")
            WebServer.send_message_to_clients(send_list)

            for key,robo_ in robo.items():
                if isinstance(robo_, (Robots.Robot_1,Robots.Robot_2_2,Robots.Robot_2_3)):
                    if robo_.ip is None:
                        logger.critical(f"{key} not found")
                    

        except Exception as e:
            logger.critical(f"error: {e}")
        time.sleep(1)


# class GamePadDict(TypedDict):
#     P1: GamePad.GamePad_wired
#     # P1: GamePad.ELECOM

#     P2: GamePad.GamePad_wired
#     # P2: GamePad.ELECOM

#     # P3: GamePad.GamePad_wired
#     P3: GamePad.ELECOM

gamePad: dict[str,GamePad.gamepad] = {
    "P1": GamePad.GamePad_wired("ONEX", 0, GamePad_1_EventCallback),

    "P2": GamePad.ELECOM("P2", GamePad_2_EventCallback),
    # "P2": GamePad.ELECOM("P3", GamePad_2_EventCallback), # TODO ちゃんとP3判定か確かめる
    # "P2": GamePad.GamePad_wired("Logicool", 1, GamePad_2_EventCallback),
    # "P2": GamePad.GamePad_wired("ONEX", 0, GamePad_2_EventCallback),

    "P3": GamePad.ELECOM("P3", GamePad_3_EventCallback), # TODO ちゃんとP3判定か確かめる
    # "P3": GamePad.ELECOM("P2", GamePad_3_EventCallback), # TODO ちゃんとP3判定か確かめる
    # "P3": GamePad.GamePad_wired("ONEX", 0, GamePad_3_EventCallback),
}

if __name__ == "__main__":
    try:
        UDPProtocol.setup()
    except Exception as e:
        logger.critical(f"error {e}")
    with ThreadPoolExecutor(max_workers=10) as executor:
        feature1 = executor.submit(R1_ControlLoop)
        feature2 = executor.submit(R2_2_ControlLoop)
        feature3 = executor.submit(R2_3_ControlLoop)
        feature4 = executor.submit(UDP_ReceiveTask)
        feature5 = executor.submit(GamePad_update)
        feature6 = executor.submit(UDP_Connection_SendTask)
        feature7 = executor.submit(UDP_Connection_ReceiveTask)
        feature8 = executor.submit(UDP_SendPing)
        feature9 = executor.submit(WebServer_update)
        feature10 = executor.submit(WebServer.flask_socketio_run, robo, gamePad)
