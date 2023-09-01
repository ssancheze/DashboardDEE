import json
import math
import threading
import paho.mqtt.client as mqtt
import time
import dronekit
import typing
from dronekit import connect, Command, VehicleMode
from pymavlink import mavutil

import dashboardClasses.ConnectionManagerClass as ConnectionManagerClass
from dashboardClasses.ConnectionManagerClass import ConnectionManager

_APPLICATION_NAME = __file__.split("\\")[-1][:-3]


def distanceInMeters(aLocation1, aLocation2):
    """
    Returns the ground distance in metres between two LocationGlobal objects.

    This method is an approximation, and will not be accurate over large distances and close to the
    earth's poles. It comes from the ArduPilot test code:
    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    """
    dlat = aLocation2.lat - aLocation1.lat
    dlong = aLocation2.lon - aLocation1.lon
    return math.sqrt((dlat * dlat) + (dlong * dlong)) * 1.113195e5


class AutopilotInstance:
    def __init__(self):

        self.operation_mode = str()
        """
        The type of operation, either 'simulation' or 'production'.
        """
        self.connection_mode = str()
        """
        How the drone is connected. It can be any of the following: \n
        'global' \n
        'local' \n
        'direct' \n
        """

        self.direct_com_port = int()
        """
        COM port, as shown in the device manager, where the telemetry radio is connected to. \n
        This attribute is only relevant when working in direct connection mode.
        """

        self.drone_identifier = int()
        """
        Drone identification number, used internally. \n
        It can be any integer between 0 and 5 (inclusive).
        """

        self.drone_identifier_string = str()
        """
        Contains the drone id preceded with a '/' (e.g. '/0') for use in mqtt messages
        """

        self.swarmMode = bool()
        """
        If true, more than one drone is being flown
        """

        self.sending_telemetry_info = bool()
        """
        Indicates whether the vehicle's telemetry is being casted
        """

        self.sending_topic = str()
        """
        Indicates the reply topic for any particular message received\n
        Example: Let the dashBoard send a connect message and the autopilot reply with a connection acknowledge: \n
        Dashboard: publish "dashBoard/autopilotService/connect" \n
        then: \n
        sending_topic = 'autopilotService/dashBoard' \n
        So that: \n
        autopilotService: publish sending_topic + '/connectAck' \n
        """

        self.vehicle = None
        """
        vehicle: dronekit.Vehicle \n
        Stores the dronekit Vehicle class
        """
        self.state = str()
        """
        These are the different values for the state of the autopilot: \n
        'connected' (only when connected the telemetry_info packet will be sent every 250 miliseconds) \n
        'arming' \n
        'armed' \n
        'disarmed' \n
        'takingOff' \n
        'flying' \n
        'returningHome' \n
        'landing' \n
        'onHearth' \n
        The autopilot can also be 'disconnected' but this state will never appear in the telemetry_info packet
        when disconnected the service will not send any packet
        """
        self.direction = str()
        """
        The direction the drone is moving to. Possible values include: \n
        'North' \n
        'South' \n
        'Est' \n
        'West' \n
        'NorthEst' \n
        'NorthWest' \n
        'SouthEst' \n
        'SouthWest' \n
        'Stop' \n
        'RTL'
        """
        self.go = bool()
        """
        Indicates whether the vehicle is going (moving) somewhere
        """

        self.rc_checks = True
        """
        If true, the drone won't operate unless a Radio Transmitter (RC) is also connected to it.
        """

        self.external_client = None
        """
        external_client = paho.mqtt.client.Client \n
        External client used for mqtt communications between services that use the AutopilotService.
        """

        self.internal_client = None
        """
        internal_client = paho.mqtt.client.Client \n
        Internal client used for mqtt communications between on-board services.
        """

        self.verbose = bool()
        """
        verbose: bool
        If true, most processes will be verbally displayed through console.
        """

    def set_verbose(self, verbose):
        if isinstance(verbose, bool):
            self.verbose = verbose

    def arm(self):
        """Arms vehicle and fly to aTargetAltitude"""
        if self.verbose:
            print("Basic pre-arm checks")  # Don't try to arm until autopilot is ready
        self.vehicle.mode = dronekit.VehicleMode("GUIDED")
        while not self.vehicle.is_armable:
            print(" Waiting for vehicle to initialise...")
            time.sleep(1)
        if self.verbose:
            print("Arming motors")
        # Copter should arm in GUIDED mode

        self.vehicle.armed = True
        # Confirm vehicle armed before attempting to take off
        while not self.is_armed():
            if self.verbose:
                print(" Waiting for arming...")
            time.sleep(1)
        if self.verbose:
            print(" Armed")

    def take_off(self, a_target_altitude, manualControl):
        self.vehicle.simple_takeoff(a_target_altitude)
        while True:
            print(" Altitude: ", self.vehicle.location.global_relative_frame.alt)
            # Break and return from function just below target altitude.
            if (
                self.vehicle.location.global_relative_frame.alt
                >= a_target_altitude * 0.95
            ):
                print("Reached target altitude")
                break
            time.sleep(1)

        self.state = "flying"
        if manualControl:
            w = threading.Thread(target=self.flying)
            w.start()

    def prepare_command(self, velocity_x, velocity_y, velocity_z):
        """
        Move vehicle in direction based on specified velocity vectors.
        """
        msg = self.vehicle.message_factory.set_position_target_local_ned_encode(
            0,  # time_boot_ms (not used)
            0,
            0,  # target system, target component
            mavutil.mavlink.MAV_FRAME_LOCAL_NED,  # frame
            0b0000111111000111,  # type_mask (only speeds enabled)
            0,
            0,
            0,  # x, y, z positions (not used)
            velocity_x,
            velocity_y,
            velocity_z,  # x, y, z velocity in m/s
            0,
            0,
            0,  # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
            0,
            0,
        )  # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

        return msg

    def get_telemetry_info(self):
        telemetry_info = {
            "lat": self.vehicle.location.global_frame.lat,
            "lon": self.vehicle.location.global_frame.lon,
            "heading": self.vehicle.heading,
            "groundSpeed": self.vehicle.groundspeed,
            "altitude": self.vehicle.location.global_relative_frame.alt,
            "battery": self.vehicle.battery.level,
            "state": self.state,
        }
        return telemetry_info

    def send_telemetry_info(self):
        while self.sending_telemetry_info:
            self.external_client.publish(
                self.sending_topic + self.drone_identifier_string + "/telemetryInfo",
                json.dumps(self.get_telemetry_info()),
            )
            time.sleep(0.25)

    def returning(self):
        # wait until the drone is at home
        while self.is_armed():
            time.sleep(1)
        self.state = "onHearth"

    def flying(self):
        speed = 1
        end = False
        cmd = self.prepare_command(0, 0, 0)  # stop
        while not end:
            self.go = False
            while not self.go:
                self.vehicle.send_mavlink(cmd)
                time.sleep(1)
            # a new go command has been received. Check direction
            if self.direction == "North":
                cmd = self.prepare_command(speed, 0, 0)  # NORTH
            if self.direction == "South":
                cmd = self.prepare_command(-speed, 0, 0)  # SOUTH
            if self.direction == "East":
                cmd = self.prepare_command(0, speed, 0)  # EAST
            if self.direction == "West":
                cmd = self.prepare_command(0, -speed, 0)  # WEST
            if self.direction == "NorthWest":
                cmd = self.prepare_command(speed, -speed, 0)  # NORTHWEST
            if self.direction == "NorthEst":
                cmd = self.prepare_command(speed, speed, 0)  # NORTHEST
            if self.direction == "SouthWest":
                cmd = self.prepare_command(-speed, -speed, 0)  # SOUTHWEST
            if self.direction == "SouthEst":
                cmd = self.prepare_command(-speed, speed, 0)  # SOUTHEST
            if self.direction == "Stop":
                cmd = self.prepare_command(0, 0, 0)  # STOP
            if self.direction == "RTL":
                end = True

    def executeFlightPlan(self, waypoints_json):
        """
        global vehicle
        global internal_client, external_client
        global sending_topic
        global state
        """
        altitude = 6
        origin = self.sending_topic.split("/")[1]

        waypoints = json.loads(waypoints_json)

        self.state = "arming"
        self.arm()
        self.state = "takingOff"
        self.take_off(altitude, False)
        self.state = "flying"

        wp = waypoints[0]
        originPoint = dronekit.LocationGlobalRelative(
            float(wp["lat"]), float(wp["lon"]), altitude
        )

        distanceThreshold = 0.50
        for wp in waypoints[1:]:

            destinationPoint = dronekit.LocationGlobalRelative(
                float(wp["lat"]), float(wp["lon"]), altitude
            )
            self.vehicle.simple_goto(destinationPoint)

            currentLocation = self.vehicle.location.global_frame
            dist = distanceInMeters(destinationPoint, currentLocation)

            while dist > distanceThreshold:
                currentLocation = self.vehicle.location.global_frame
                dist = distanceInMeters(destinationPoint, currentLocation)
                time.sleep(0.25)
            if self.verbose:
                print("reached")
            waypointReached = {"lat": currentLocation.lat, "lon": currentLocation.lon}

            self.external_client.publish(
                self.sending_topic + "/waypointReached", json.dumps(waypointReached)
            )

            if wp["takePic"]:
                # ask to send a picture to origin
                self.internal_client.publish(origin + "/cameraService/takePicture")

        self.vehicle.mode = dronekit.VehicleMode("RTL")
        self.state = "returningHome"

        currentLocation = self.vehicle.location.global_frame
        dist = distanceInMeters(originPoint, currentLocation)

        while dist > distanceThreshold:
            currentLocation = self.vehicle.location.global_frame
            dist = distanceInMeters(originPoint, currentLocation)
            # time.sleep(0.25)

        self.state = "landing"
        while self.is_armed():
            time.sleep(1)
        self.state = "onHearth"

    def executeFlightPlan2(self, waypoints_json):
        altitude = 6

        waypoints = json.loads(waypoints_json)
        self.state = "arming"
        self.arm()
        self.state = "takingOff"
        self.take_off(altitude, False)
        self.state = "flying"
        cmds = self.vehicle.commands
        cmds.clear()

        # wp = waypoints[0]
        # originPoint = dronekit.LocationGlobalRelative(float(wp['lat']), float(wp['lon']), altitude)
        for wp in waypoints:
            cmds.add(
                Command(
                    0,
                    0,
                    0,
                    mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                    mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    float(wp["lat"]),
                    float(wp["lon"]),
                    altitude,
                )
            )
        wp = waypoints[0]
        cmds.add(
            Command(
                0,
                0,
                0,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                0,
                0,
                0,
                0,
                0,
                0,
                float(wp["lat"]),
                float(wp["lon"]),
                altitude,
            )
        )
        cmds.upload()

        self.vehicle.commands.next = 0
        # Set mode to AUTO to start mission
        self.vehicle.mode = VehicleMode("AUTO")
        while True:
            nextwaypoint = self.vehicle.commands.next
            if self.verbose:
                print("next ", nextwaypoint)
            time.sleep(0.5)
            if nextwaypoint == len(
                waypoints
            ):  # Dummy waypoint - as soon as we reach waypoint 4 this is true and we exit.
                print("Last waypoint reached")
                break

        if self.verbose:
            print("Return to launch")
        self.state = "returningHome"
        self.vehicle.mode = VehicleMode("RTL")
        while self.is_armed():
            time.sleep(1)
        self.state = "onHearth"

    def connect_vehicle(self, origin):
        if self.verbose:
            print("Autopilot service connected by " + origin)
        _baud_rate = 115200
        if self.operation_mode == "simulation":
            connection_string = "tcp:127.0.0.1:" + str(
                5763 + self.drone_identifier * 10
            )
        else:
            if self.connection_mode == "direct":
                connection_string = f"com{self.direct_com_port}"
                _baud_rate = 57600
            else:
                connection_string = "/dev/ttyS0"

        if self.verbose:
            print(f"Connecting to {connection_string}")

        self.vehicle = connect(connection_string, wait_ready=False, baud=_baud_rate)
        self.vehicle.wait_ready(True, timeout=5000)

        if self.verbose:
            print(f"Vehicle {self.vehicle.__str__()} is ready")
            print(
                f"AutopilotService{self.drone_identifier_string} Connected to flight controller"
            )
        self.state = "connected"

    def disconnect_vehicle(self):
        if self.state != "disconnected":
            self.reset_rc_checks()
            # external_client.publish(sending_topic + "/connected", json.dumps(get_telemetry_info()))
            self.vehicle.close()
            self.sending_telemetry_info = False
            self.state = "disconnected"
            self.external_client.publish(
                self.sending_topic + self.drone_identifier_string + "/disconnectAck"
            )

    def process_message(self, message, client):
        if self.verbose:
            print(f"Received: {message.topic}")

        splitted = message.topic.split("/")
        origin = splitted[0]
        command = splitted[-1]
        if self.swarmMode:
            drone_identifier = int(splitted[-2])
            if drone_identifier != self.drone_identifier:
                self.drone_identifier = drone_identifier
        sending_topic = "autopilotService/" + origin
        if sending_topic != self.sending_topic:
            self.sending_topic = sending_topic

        if command == "connect":
            if self.state == "disconnected":
                self.connect_vehicle(origin)

                if self.rc_checks:
                    self.reset_rc_checks()
                else:
                    self.disable_rc_checks()
                # external_client.publish(sending_topic + "/connected", json.dumps(get_telemetry_info()))

                self.sending_telemetry_info = True
                y = threading.Thread(target=self.send_telemetry_info)
                y.start()
            else:
                print("Autopilot already connected")

        if command == "disconnect":
            self.disconnect_vehicle()

        if command == "takeOff":
            self.state = "takingOff"
            w = threading.Thread(target=self.take_off, args=[5, True])
            w.start()

        if command == "returnToLaunch":
            # stop the process of getting positions
            self.vehicle.mode = dronekit.VehicleMode("RTL")
            self.state = "returningHome"
            self.direction = "RTL"
            self.go = True
            w = threading.Thread(target=self.returning)
            w.start()

        if command == "armDrone":
            self.state = "arming"
            self.arm()

            # the vehicle will disarm automatically is takeOff does not come soon
            # when attribute 'armed' changes run function armed_change
            self.vehicle.add_attribute_listener("armed", self.attr_listen)
            self.state = "armed"

        if command == "disarmDrone":
            self.vehicle.armed = False
            while self.is_armed():
                time.sleep(1)
            self.state = "disarmed"

        if command == "land":

            self.vehicle.mode = dronekit.VehicleMode("LAND")
            self.state = "landing"
            while self.is_armed():
                time.sleep(1)
            self.state = "onHearth"

        if command == "go":
            self.direction = message.payload.decode("utf-8")
            print("Going ", self.direction)
            self.go = True

        if command == "executeFlightPlan":
            waypoints_json = str(message.payload.decode("utf-8"))
            w = threading.Thread(
                target=self.executeFlightPlan2,
                args=[
                    waypoints_json,
                ],
            )
            w.start()

    def is_armed(self):
        return self.vehicle.armed

    def disable_rc_check(self):
        self.vehicle.parameters["ARMING_CHECK"] = 65470

    def reset_rc_check(self):
        self.vehicle.parameters["ARMING_CHECK"] = 1

    def disable_thr_fs_check(self):
        self.vehicle.parameters["FS_THR_ENABLE"] = 0

    def reset_thr_fs_check(self):
        self.vehicle.parameters["FS_THR_ENABLE"] = 1

    def disable_rc_checks(self):
        self.disable_rc_check()
        self.disable_thr_fs_check()
        if self.verbose:
            print(f"Drone #{self.drone_identifier}: RC checks disabled\n")

    def reset_rc_checks(self):
        if self.state == "disconnected":
            self.connect_vehicle("dashBoard")
            self.reset_rc_check()
            self.reset_thr_fs_check()
            self.disconnect_vehicle()
        else:
            self.reset_rc_check()
            self.reset_thr_fs_check()
        if self.verbose:
            print(f"Drone #{self.drone_identifier}: RC checks reset\n")

    def attr_listen(self, innerself, attr_name, value):
        def armed_change(innerself, attr_name, value):
            if self.is_armed():
                self.state = "armed"
            else:
                self.state = "disarmed"

        return armed_change

    def on_internal_message(self, client, userdata, message):
        self.process_message(message, self.internal_client)

    def on_external_message(self, client, userdata, message):
        self.process_message(message, self.external_client)

    def AutopilotService(
        self,
        connection_mode,
        operation_mode,
        external_broker,
        username,
        password,
        droneId="",
        hold=False,
        local_mode=None,
        direct_com_port=None,
        max_drones=1,
    ):

        if self.verbose:
            print("Connection mode: ", connection_mode)
            print("Operation mode: ", operation_mode)
        self.connection_mode = connection_mode
        self.operation_mode = operation_mode

        _args = (self.connection_mode, _APPLICATION_NAME)

        self.state = "disconnected"

        self.drone_identifier = 0
        self.drone_identifier_string = ""

        _kwargs = dict()
        if droneId != "" and max_drones > 1:
            self.swarmMode = True
            _kwargs["max_drones"] = max_drones
            self.drone_identifier = int(droneId)
            self.drone_identifier_string = "/" + str(self.drone_identifier)
            if self.verbose:
                print("(SWARM MODE) drone number: ", self.drone_identifier)
        if (
            self.connection_mode == "local"
            and isinstance(local_mode, int)
            and isinstance(direct_com_port, int)
        ):
            self.direct_com_port = direct_com_port
            _kwargs["local_mode"] = local_mode
        if droneId != "":
            _kwargs["max_drones"] = max_drones
        _kwargs["external_broker_address"] = external_broker
        _kwargs["broker_credentials"] = (username, password)

        myConnectionManager = ConnectionManager()
        broker_settings = myConnectionManager.setParameters(
            connection_mode, _APPLICATION_NAME, **_kwargs
        )

        if self.verbose:
            print("External broker: ", broker_settings["external"])

        self.external_client = mqtt.Client(
            "Autopilot_external " + self.drone_identifier_string, transport="websockets"
        )
        self.external_client.on_message = self.on_external_message

        if "credentials" in broker_settings["external"].keys():
            self.external_client.username_pw_set(
                *broker_settings["external"]["credentials"]
            )

        self.internal_client = mqtt.Client(
            "Autopilot_internal " + self.drone_identifier_string
        )
        self.internal_client.on_message = self.on_internal_message

        self.external_client.connect(
            host=broker_settings["external"]["address"],
            port=broker_settings["external"]["port"],
        )
        self.internal_client.connect(
            host=broker_settings["internal"]["address"],
            port=broker_settings["internal"]["port"],
        )

        if self.verbose:
            print("Waiting....")
        topic_string = "+/autopilotService" + self.drone_identifier_string + "/#"
        self.external_client.subscribe(topic_string, 2)
        self.internal_client.subscribe(topic_string)
        if hold:
            self.external_client.loop_forever()
        else:
            self.external_client.loop_start()
        self.internal_client.loop_start()


class AutoBoot:
    def __init__(self):
        self.myInstances = list()

    def autoBoot(
        self,
        connection_mode,
        operation_mode,
        external_broker,
        username,
        password,
        _max_drones=1,
        hold=False,
        verbose=False,
    ):
        if _max_drones == 1:
            myAutopilotInstance = AutopilotInstance()
            if isinstance(verbose, bool) and verbose:
                myAutopilotInstance.verbose = verbose
            self.myInstances.append(myAutopilotInstance)
            thread = threading.Thread(
                target=self.myInstances[0].AutopilotService(
                    connection_mode, operation_mode, external_broker, username, password
                )
            )
            thread.start()
        else:
            _range = _max_drones - 1
            _threads: typing.List[threading.Thread] = [None] * _max_drones
            self.myInstances = [AutopilotInstance() for _ in range(_max_drones)]
            for _id in range(_range):
                if isinstance(verbose, bool) and verbose:
                    self.myInstances[_id].verbose = verbose
                thread_service = threading.Thread(
                    target=self.myInstances[_id].AutopilotService(
                        connection_mode,
                        operation_mode,
                        external_broker,
                        username,
                        password,
                        str(_id),
                        max_drones=_max_drones,
                    )
                )
                _threads[_id] = thread_service
                _threads[_id].start()
                if isinstance(verbose, bool) and verbose:
                    self.myInstances[_range].verbose = verbose
            _last_thread_service = threading.Thread(
                target=self.myInstances[_range].AutopilotService(
                    connection_mode,
                    operation_mode,
                    external_broker,
                    username,
                    password,
                    str(_range),
                    max_drones=_max_drones,
                )
            )
            _threads[_range] = _last_thread_service
            _threads[_range].start()

    def disable_rc_checks(self):
        for autopilotInstance in self.myInstances:
            autopilotInstance.rc_checks = False

    def reset_rc_checks(self):
        for autopilotInstance in self.myInstances:
            autopilotInstance.rc_checks = True
            autopilotInstance.reset_rc_checks()

    def disconnect_instances(self):
        for autopilotInstance in self.myInstances:
            autopilotInstance.disconnect_vehicle()


if __name__ == "__main__":
    import sys

    _APPLICATION_NAME = __file__.split("\\")[-1][:-3]
    """
    SCRIPT PARAMETERS SYNTAX
    connection_mode (local_mode OR direct_com_port) operation_mode
    external_broker_address (username pwd) ("multi" drone_id,max_drones)
    """

    connection_mode = sys.argv[1]  # global, local or direct
    external_broker_address, username, password, local_mode, direct_com_port = [
        None
    ] * 5
    if connection_mode == "global":
        operation_mode = sys.argv[2]  # simulation or production
        external_broker_address = sys.argv[3]
        if external_broker_address in ConnectionManagerClass.PROTECTED_BROKERS:
            username = sys.argv[4]
            password = sys.argv[5]
    else:
        operation_mode = sys.argv[3]
        if connection_mode == "local":
            local_mode = sys.argv[2]
        elif connection_mode == "direct":
            direct_com_port = sys.argv[2]

    if sys.argv[-2] == "multi":
        max_drones = sys.argv[-1]

    if sys.argv[-2] == "multi":
        drone_id, max_drones = sys.argv[-1].split(",")
    else:
        drone_id, max_drones = "", ""

    kwargs = {
        "droneId": drone_id,
        "hold": True,
        "local_mode": local_mode,
        "direct_com_port": direct_com_port,
        "max_drones": max_drones,
    }

    myInstance = AutopilotInstance()
    myInstance.verbose = True

    myInstance.AutopilotService(
        connection_mode,
        operation_mode,
        external_broker_address,
        username,
        password,
        **kwargs,
    )
