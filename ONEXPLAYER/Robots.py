from datetime import datetime
import queue
from typing import Literal
import UDPProtocol
from WebServer import send_message_to_clients
# import WebServer
# import global_value as g
import Wheel
import math
import time
from logger_setup import logger


class RoboMaster:
    def __init__(self, robot, motor_id) -> None:
        self.robot = robot
        self.motor_id = motor_id
        self.feedback = {
            "current": 0,
            "velocity": 0,
            "position": 0,
            "output_current": 0,
        }
        self.command_feedback = {
            "current": (0x0200 | self.motor_id, "f32"),
            "velocity": (0x0210 | self.motor_id, "i32"),
            "position": (0x0220 | self.motor_id, "i32"),
            "output_current": (0x0230 | self.motor_id, "i32"),
        }
        self.target_value:float = 0 # 制御量(制御値)

    def send_command(self, command, value, value_type):
        if self.robot.ip is not None:
            # print("32")
            # UDPProtocol.send(self.robot.ip,
            #                  command, value, value_type)
            UDPProtocol.put_queue(self.robot.ip, command, value, value_type, self.robot.udp_send_queue)

    def setCurrent(self, current):
        self.target_value = current
        command = 0x0100 | self.motor_id
        self.send_command(command, current, "f32")

    def setVelocity(self, velocity):
        self.target_value = velocity
        command = 0x0110 | self.motor_id
        self.send_command(command, velocity, "i32")

    def setPosition(self, position):
        self.target_value = position
        command = 0x0120 | self.motor_id
        self.send_command(command, position, "i32")

    def setPositionOffset(self, position):
        command = 0x0130 | self.motor_id
        self.send_command(command, position, "i32")

    def setMotorModel(self, model):
        command = 0x0140 | self.motor_id
        self.send_command(command, model, 'ui32')

    def resetZEROPosition(self):
        command = 0x0150 | self.motor_id
        self.send_command(command, 0, "i32")

    def setCurrentLimit(self, current):
        command = 0x0160 | self.motor_id
        self.send_command(command, current, "f32")

    def setVelocityLimit(self, velocity):
        command = 0x0170 | self.motor_id
        self.send_command(command, velocity, "i32")

    def setPositionLimit(self, position):
        command = 0x0180 | self.motor_id
        self.send_command(command, position, "i32")

    def setVelocityKP(self, kp):
        command = 0x0190 | self.motor_id
        self.send_command(command, kp, "f32")

    def setVelocityKI(self, ki):
        command = 0x01A0 | self.motor_id
        self.send_command(command, ki, "f32")

    def setVelocityKD(self, kd):
        command = 0x01B0 | self.motor_id
        self.send_command(command, kd, "f32")

    def setPositionKP(self, kp):
        command = 0x01C0 | self.motor_id
        self.send_command(command, kp, "f32")

    def setPositionKI(self, ki):
        command = 0x01D0 | self.motor_id
        self.send_command(command, ki, "f32")

    def setPositionKD(self, kd):
        command = 0x01E0 | self.motor_id
        self.send_command(command, kd, "f32")

    def setFeedback(self, command_id, bytes_command_content):
        for command_feedback_key in self.command_feedback:
            if self.command_feedback[command_feedback_key][0] == command_id:
                fmt = self.command_feedback[command_feedback_key][1]
                command_content = UDPProtocol.decode(
                    bytes_command_content, fmt)
                self.feedback[command_feedback_key] = command_content


class CyberGear:
    def __init__(self, robot, motor_id) -> None:
        self.robot = robot
        self.motor_id = motor_id
        self.feedback = {
            "position": 0,
            "velocity": 0,
            "torque": 0
        }
        self.command_feedback = {
            "position": (0x0300 | self.motor_id, "f32"),
            "velocity": (0x0310 | self.motor_id, "f32"),
            "torque": (0x0320 | self.motor_id, "f32"),
        }
        self.target_value:float = 0 # 制御量(制御値)
        self.position_relatice_sum:float = 0

    def send_command(self, command, value, value_type):
        if self.robot.ip is not None:
            # UDPProtocol.send(self.robot.ip,
            #                  command, value, value_type)
            UDPProtocol.put_queue(self.robot.ip, command, value, value_type, self.robot.udp_send_queue)

    def Init(self, can_id:int):
        command = 0x0400 | self.motor_id
        self.send_command(command, can_id, 'ui32')

    def ResetMotor(self):
        command = 0x0410 | self.motor_id
        self.send_command(command, 0, 'ui32')

    def ResetZEROPos(self):
        command = 0x0420 | self.motor_id
        self.send_command(command, 0, 'ui32')

    def EnableMotor(self):
        command = 0x0430 | self.motor_id
        self.send_command(command, 0, 'ui32')

    def SetMode(self, mode:Literal[0,1,2,3]): # 0:drive 1:position 2:velocity 3:current
        command = 0x0440 | self.motor_id
        self.send_command(command, mode, 'ui32')

    def SpeedLimit(self, speed:float):
        command = 0x0450 | self.motor_id
        self.send_command(command, speed, "f32")

    def TorqueLimit(self, torque:float):
        command = 0x0460 | self.motor_id
        self.send_command(command, torque, "f32")

    def CurrentLimit(self, current:float):
        command = 0x0470 | self.motor_id
        self.send_command(command, current, "f32")

    def ControlSpeed(self, speed:float):
        self.target_value = speed
        command = 0x0480 | self.motor_id
        self.send_command(command, speed, "f32")

    def ControlPosition(self, position:float):
        self.target_value = position
        command = 0x0490 | self.motor_id
        if -4 * math.pi <= position <= 4 * math.pi:
            self.send_command(command, position, "f32")
        else:
            logger.critical(f"Cyber limit over -4pi ~ 4pi :{position}")

    # 相対位置制御 増加量を指定
    def ControlPositionRelative(self, position_relative):
        self.position_relatice_sum += position_relative
        command = 0x04A0 | self.motor_id
        if -4 * math.pi <= position_relative <= 4 * math.pi:
            self.send_command(command, position_relative, "f32")
        else:
            logger.critical(f"Cyber limit over -4pi ~ 4pi :{position_relative}")

    def ResetPosition(self):
        command = 0x04B0 | self.motor_id
        self.send_command(command, 0, 'ui32')

    def ControlSpeed_SetMode(self, speed:float):
        self.target_value = speed
        command = 0x04C0 | self.motor_id
        self.send_command(command, speed, "f32")

    def setFeedback(self, command_id, bytes_command_content):
        for command_feedback_key in self.command_feedback:
            if self.command_feedback[command_feedback_key][0] == command_id:
                logger.info(f"aaaaaaaaaaaa")
                fmt = self.command_feedback[command_feedback_key][1]
                command_content = UDPProtocol.decode(
                    bytes_command_content, fmt)
                self.feedback[command_feedback_key] = command_content


class KondoServo:
    def __init__(self, robot, motor_id) -> None:
        self.robot = robot
        self.motor_id = motor_id
        self.target_value:int = 0

    def send_command(self, command, value, value_type):
        if self.robot.ip is not None:
            # UDPProtocol.send(self.robot.ip,
            #                  command, value, value_type)
            UDPProtocol.put_queue(self.robot.ip, command, value, value_type, self.robot.udp_send_queue)

    def setPosition(self, position):  # unit: deg
        self.target_value = position
        command = 0x0600 | self.motor_id
        self.send_command(command, position, "f32")

    def digitalWrite(self, state):
        command = 0x0610 | self.motor_id
        self.send_command(command, state, 'ui32')


class Robot:
    UDP_delay: int = 30 * 1000 # unit:ns
    def __init__(self) -> None:
        pass
        # self.device_name = device_name
        # self.command_send_number = 0
        # self.udp_send_queue = queue.Queue()
        # self.RSSI: int = 0
        # self.ping: int = 0
        # self.ip = None


class Robot_1(Robot):
    def __init__(self, device_name) -> None:
        super().__init__()  # 親クラスの初期化
        self.device_name = device_name
        self.command_send_number = 0
        self.udp_send_queue = queue.Queue()
        self.RSSI: int = 0
        self.ping: int = 0
        self.ip = None
        
        self.wheelAssist_direction:Literal["left","right"] = "left"
        self.wheel_state:Literal["normal", "turn", "diagonal"] = "normal"

        self.wheel_FL = RoboMaster(self, 0)
        self.wheel_FR = RoboMaster(self, 1)
        self.wheel_RL = RoboMaster(self, 2)
        self.wheel_RR = RoboMaster(self, 3)

        self.wheels = Wheel.wheels((
            Wheel.mecanum_left((-0.7, 0.7), (0, 1.5)),
            Wheel.mecanum_right((0.7, 0.7), (0, -1.5)),
            Wheel.mecanum_right((-0.7, -0.7), (0, 1.5)),
            Wheel.mecanum_left((0.7, -0.7), (0, -1.5)),
        ))

        self.is_wheel_slow: bool = True

        self.servo_big = KondoServo(self, 0)
        self.servo_small = KondoServo(self, 1)

        self.Cyber_tension = CyberGear(self, 0)
        self.Cyber_tension_position: float = 0

        self.Cyber_pull = CyberGear(self, 1)  # for inject R2-2
        self.Cyber_pull_position: float = 0

        self.RM_pull = RoboMaster(self, 4)  # for inject R2-1
        self.RM_pull_position: int = 0
        self.RM_pull_state: int = 0 # 0:ノーマル 1:原点
        # self.RM_pull_state_previous: int = 0

    def initialize(self): # TODO initializeのやつはudp送信してもだいたい消される
        self.RM_pull_position = 0
        self.Cyber_pull_position = 0
        self.Cyber_tension_position = 0
        self.RM_pull.setMotorModel(1)  # M3508
        time.sleep(0.01)
        self.RM_pull.setCurrentLimit(5)
        # self.RM_pull.setVelocityLimit(300)
        # self.RM_pull.setPositionKI(0.0008)
        # self.RM_pull.setPositionKD(50)
        # self.RM_pull.setCurrentLimit(7) # TODO naosu
        # self.RM_pull.setVelocityKP(10) # vel 5 100 0.2
        # self.RM_pull.setPositionKP(0.6) # vel 5 100 0.2
        # self.wheel_FL.setCurrentLimit(6.0)
        # self.wheel_FR.setCurrentLimit(6.0)
        # self.wheel_RL.setCurrentLimit(6.0)
        # self.wheel_RR.setCurrentLimit(6.0)

    #             	pid_param_init(&RoboMaster->pid_position, 500 * 36, 10000, 10, 8000, 10, 0.1,
    # 				   200);
    # 	pid_param_init(&RoboMaster->pid_velocity, M2006_MAX_CONTROL_VALUE, 5000, 2,
    # 				   20000, 9, 0.1, 1);
    # 	case M3508:
    # 		pid_param_init(&RoboMaster->pid_velocity, M3508_MAX_CONTROL_VALUE, 5000,
    # 					   2, 20000, 5, 10, 20);
        time.sleep(0.01)
        self.Cyber_tension.Init(0x72)
        time.sleep(0.01)
        self.Cyber_tension.ResetMotor()
        time.sleep(0.01)
        self.Cyber_tension.SpeedLimit(2.0)
        time.sleep(0.01)
        self.Cyber_tension.TorqueLimit(12.0)
        time.sleep(0.01)
        self.Cyber_tension.CurrentLimit(20.0)
        time.sleep(0.01)
        self.Cyber_tension.SetMode(0x01)  # position
        time.sleep(0.01)
        self.Cyber_tension.ResetZEROPos()
        time.sleep(0.01)
        self.Cyber_tension.EnableMotor()
        time.sleep(0.01)

        self.Cyber_pull.Init(0x73)
        # self.Cyber_pull.Init(0x71)
        time.sleep(0.01)
        self.Cyber_pull.ResetMotor()
        time.sleep(0.01)
        self.Cyber_pull.SpeedLimit(30.0)
        time.sleep(0.01)
        self.Cyber_pull.TorqueLimit(12.0)
        time.sleep(0.01)
        self.Cyber_pull.CurrentLimit(23.0)
        time.sleep(0.01)
        self.Cyber_pull.SetMode(0x01)  # position
        time.sleep(0.01)
        self.Cyber_pull.ResetZEROPos()
        time.sleep(0.01)
        self.Cyber_pull.EnableMotor()
        time.sleep(0.01)

    def setFeedback(self, command_id, bytes_command_content):
        if command_id == 0xFFF0:
            # RSSI
            self.RSSI = UDPProtocol.decode(bytes_command_content, "i32")
            send_message_to_clients({self.device_name+"_RSSI": self.RSSI})
            send_message_to_clients({self.device_name+"_RSSI": self.RSSI})
            # logger.debug(f"RSSI {self.device_name}: {self.RSSI}")
        elif command_id == 0xFFF2:
            # pong
            self.ping = round((int(str(int(time.time_ns()/100))[-9:]) - UDPProtocol.decode(bytes_command_content, 'ui32'))/10000,1)
            send_message_to_clients({self.device_name+"_ping": self.ping})
            # logger.debug(f"ping {self.device_name}: {self.ping}")
        elif command_id == 0xE00:
            logger.debug(f"command_send:{self.command_send_number}")
            self.command_send_number = 0
        else:
            self.wheel_FL.setFeedback(command_id, bytes_command_content)
            self.wheel_FR.setFeedback(command_id, bytes_command_content)
            self.wheel_RL.setFeedback(command_id, bytes_command_content)
            self.wheel_RR.setFeedback(command_id, bytes_command_content)
            self.Cyber_tension.setFeedback(command_id, bytes_command_content)
            self.Cyber_pull.setFeedback(command_id, bytes_command_content)
            self.RM_pull.setFeedback(command_id, bytes_command_content)
            # logger.debug(f"finished")

class Robot_2_1(Robot):
    def __init__(self, device_name) -> None:
        super().__init__()  # 親クラスの初期化
        self.device_name = device_name
        self.command_send_number = 0
        self.RSSI: int = 0
        self.ping: int = 0
        self.ip = None

    def sendServoAngle(self, angle):
        UDPProtocol.send(self.ip, 0x0600, angle, 'ui32')

    def setFeedback(self, command_id, bytes_command_content):
        if command_id == 0xFFF0:
            # RSSI
            self.RSSI = UDPProtocol.decode(bytes_command_content, "i32")
            send_message_to_clients({self.device_name+"_RSSI": self.RSSI})
            # logger.debug(f"RSSI {self.device_name}: {self.RSSI}")
        elif command_id == 0xFFF2:
            # pong
            self.ping = round((int(str(int(time.time_ns()/100))[-9:]) - UDPProtocol.decode(bytes_command_content, 'ui32'))/10000,1)
            send_message_to_clients({self.device_name+"_ping": self.ping})
            # logger.debug(f"ping {self.device_name}: {self.ping}")
        elif command_id == 0xE00:
            logger.debug(f"command_send:{self.command_send_number}")
            self.command_send_number = 0
        else:
            logger.debug(f"rec {self.device_name} {hex(command_id)} {UDPProtocol.decode(bytes_command_content, 'ui32')}")


class Robot_2_2(Robot):
    def __init__(self, device_name) -> None:
        super().__init__()  # 親クラスの初期化
        self.device_name = device_name
        self.command_send_number = 0
        self.udp_send_queue = queue.Queue()
        self.RSSI: int = 0
        self.ping: int = 0
        self.ip = None

        self.wheel_F = RoboMaster(self, 0)
        self.wheel_RL = RoboMaster(self, 1)
        self.wheel_RR = RoboMaster(self, 2)
        
        self.collect_state:Literal["stop","forward","Reversing"] = "stop"
        self.collect_L = RoboMaster(self, 3)
        self.collect_R = RoboMaster(self, 4)

        self.wheels = Wheel.wheels((
            Wheel.omni((0, 0), (18/18, 0)),
            Wheel.omni((-0.5, -0.25), (0, -18/18)),
            # Wheel.omni((-1,-0.5),(0,-37/18)),
            Wheel.omni((0.5, -0.25), (0, 18/18)),
            # Wheel.omni((1,-0.5),(0,37/18)),
        ))

        self.is_wheel_slow = True

        self.collect_abjust = 0
        self.is_collect_fast: bool = False

    def initialize(self):
        self.is_wheel_slow = True
        self.collect_state = "stop"
        self.collect_abjust = 0
        self.is_collect_fast = False
        self.collect_L.setCurrentLimit(2)
        self.collect_R.setCurrentLimit(2)

    def setFeedback(self, command_id, bytes_command_content):
        if command_id == 0xFFF0:
            # RSSI
            self.RSSI = UDPProtocol.decode(bytes_command_content, "i32")
            send_message_to_clients({self.device_name+"_RSSI": self.RSSI})
            # logger.debug(f"RSSI {self.device_name}: {self.RSSI}")
        elif command_id == 0xFFF2:
            # pong
            self.ping = round((int(str(int(time.time_ns()/100))[-9:]) - UDPProtocol.decode(bytes_command_content, 'ui32'))/10000,1)
            send_message_to_clients({self.device_name+"_ping": self.ping})
            # logger.debug(f"ping {self.device_name}: {self.ping}")
        elif command_id == 0xE00:
            logger.debug(f"command_send:{self.command_send_number}")
            self.command_send_number = 0
        else:
            self.wheel_RL.setFeedback(command_id, bytes_command_content)
            self.wheel_RR.setFeedback(command_id, bytes_command_content)
            self.wheel_F.setFeedback(command_id, bytes_command_content)
            self.collect_L.setFeedback(command_id, bytes_command_content)
            self.collect_R.setFeedback(command_id, bytes_command_content)


class Robot_2_3(Robot):
    def __init__(self, device_name) -> None:
        super().__init__()  # 親クラスの初期化
        self.device_name = device_name
        self.command_send_number = 0
        self.udp_send_queue = queue.Queue()
        self.RSSI: int = 0
        self.ping: int = 0
        self.ip = None

        self.wheel_left = RoboMaster(self, 0)
        self.wheel_right = RoboMaster(self, 1)

        self.is_wheel_slow: bool = False

        self.Cyber_left = CyberGear(self, 0)
        self.Cyber_right = CyberGear(self, 1)
        self.last_set_time = datetime.now()
        self.Cyber_position: float = 0

        self.servo = KondoServo(self, 1)
        self.servo_position:int = 105

    def initialize(self):
        self.Cyber_position = 0
        # self.Cyber_right.Init(0x70)
        # self.Cyber_left.Init(0x71)
        self.Cyber_right.Init(0x74)
        time.sleep(0.02)
        self.Cyber_left.Init(0x75)
        time.sleep(0.02)
        self.Cyber_right.ResetMotor()
        time.sleep(0.02)
        self.Cyber_left.ResetMotor()
        time.sleep(0.02)
        self.Cyber_right.SpeedLimit(30.0)
        time.sleep(0.02)
        self.Cyber_left.SpeedLimit(30.0)
        time.sleep(0.02)
        self.Cyber_right.TorqueLimit(12.0)
        time.sleep(0.02)
        self.Cyber_left.TorqueLimit(12.0)
        time.sleep(0.02)
        self.Cyber_right.CurrentLimit(23.0)
        time.sleep(0.02)
        self.Cyber_left.CurrentLimit(23.0)
        time.sleep(0.02)
        self.Cyber_right.SetMode(0x01)  # position
        time.sleep(0.02)
        self.Cyber_left.SetMode(0x01)  # position
        time.sleep(0.02)
        self.Cyber_right.ResetZEROPos()
        time.sleep(0.02)
        self.Cyber_left.ResetZEROPos()
        time.sleep(0.02)
        self.Cyber_right.EnableMotor()
        time.sleep(0.02)
        self.Cyber_left.EnableMotor()
        time.sleep(0.02) 

    def Cyber_SetFree(self):
        self.Cyber_position = 0
        self.Cyber_right.ResetMotor()
        self.Cyber_left.ResetMotor()
        # self.Cyber_right.ResetZEROPos()
        # self.Cyber_left.ResetZEROPos()

    def Cyber_SetPositionRelative(self, position):
        Cyber_position_summed = self.Cyber_position + position
        if Cyber_position_summed < math.radians(190) and Cyber_position_summed > -10000:
            self.Cyber_position = Cyber_position_summed
            self.Cyber_left.ControlPosition(self.Cyber_position)
            self.Cyber_right.ControlPosition(-1 * self.Cyber_position)
            logger.info(f"R23 Cyber Position {self.Cyber_position}")
        else:
            logger.error("R23 Cyber over 0 ~ 190deg limit")

    def setFeedback(self, command_id, bytes_command_content):
        if command_id == 0xFFF0:
            # RSSI
            self.RSSI = UDPProtocol.decode(bytes_command_content, "i32")
            send_message_to_clients({self.device_name+"_RSSI": self.RSSI})
            # logger.debug(f"RSSI {self.device_name}: {self.RSSI}")
        elif command_id == 0xFFF2:
            # pong
            self.ping = round((int(str(int(time.time_ns()/100))[-9:]) - UDPProtocol.decode(bytes_command_content, 'ui32'))/10000,1)
            send_message_to_clients({self.device_name+"_ping": self.ping})
            # logger.debug(f"ping {self.device_name}: {self.ping}")
        elif command_id == 0xE00:
            logger.debug(f"command_send:{self.command_send_number}")
            self.command_send_number = 0
        else:
            self.wheel_left.setFeedback(command_id, bytes_command_content)
            self.wheel_right.setFeedback(command_id, bytes_command_content)
            self.Cyber_left.setFeedback(command_id, bytes_command_content)
            self.Cyber_right.setFeedback(command_id, bytes_command_content)
