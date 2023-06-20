TELEMETRY_DICT_KEYS = {
        'lat',
        'lon',
        'heading',
        'groundSpeed',
        'altitude',
        'battery',
        'state'
}

# Maximum time permitted between telemetry updates (currently x5 the telemetry update rate set in AutopilotService)
# If the last telemetry package has an age greater than this value the connection is considered closed and thus the
# drone is considered disconnected.
TELEMETRY_AGE_MAX = 1.25

# Maximum amount of drones supported by the dashboard.
DASHBOARD_MAX_DRONES = 6

'''
These are the different values for the state of the autopilot: 
(only when connected the telemetry_info packet will be sent every 250 miliseconds)
    'connected' 
    'arming'
    'armed'
    'disarmed'
    'takingOff'
    'flying'
    'returningHome'
    'landing'
    'onHearth'

The autopilot can also be 'disconnected' but this state will never appear in the telemetry_info packet 
when disconnected the service will not send any packet
'''


class Drone:
    def __init__(self):
        self.active = False
        self.connected = False
        self.armed = False
        self.on_air = False
        self.telemetry_info = dict()

    def set_active(self, active):
        if type(active) is bool:
            self.active = active
        else:
            raise TypeError("'active' must be bool type")

    def set_telemetry_info(self, telemetry_info):
        if not all(key in TELEMETRY_DICT_KEYS for key in telemetry_info):
            raise KeyError("'telemetry_info' contains invalid key")
        if not all(key in telemetry_info for key in TELEMETRY_DICT_KEYS):
            raise KeyError("'telemetry_info' missing key(s)")
        self.telemetry_info = telemetry_info
        self.update_attributes()

    def update_attributes(self):
        _state = self.telemetry_info['state']

        if _state == 'connected':
            self.connected = True
            self.armed = False
            self.on_air = False
        elif _state == 'arming':
            self.connected = True
            self.armed = False
            self.on_air = False
        elif _state == 'armed':
            self.connected = True
            self.armed = True
            self.on_air = False
        elif _state == 'disarmed':
            self.connected = True
            self.armed = False
            self.on_air = False
        elif _state == 'takingOff':
            self.connected = True
            self.armed = True
            self.on_air = True
        elif _state == 'flying':
            self.connected = True
            self.armed = True
            self.on_air = True
        elif _state == 'returningHome':
            self.connected = True
            self.armed = True
            self.on_air = True
        elif _state == 'landing':
            self.connected = True
            self.armed = True
            self.on_air = True
        elif _state == 'onHearth':
            self.connected = True
            self.armed = False
            self.on_air = False


def updateAttributes(func):
    def wrapper(self, telemetry_info, drone_id):
        func(self, telemetry_info, drone_id)
        for attr in {'connected', 'armed', 'on_air'}:
            self.update_attribute(attr)
    return wrapper


class OperationDrones:
    def __init__(self):
        self.drones = []
        self.max_drones = 1
        # Control attributes for self.drones
        # -1: No drones connected/armed/on air
        # 0: any (one or more) drones connected/armed/on air
        # 1: all drones connected/armed/on air
        self.connected = -1
        self.armed = -1
        self.on_air = -1

    def set_active(self, max_drones=1):
        self.max_drones = max_drones
        self.drones = [Drone() for _ in range(max_drones)]

    @updateAttributes
    def set_telemetry_info(self, telemetry_info, drone_id):
        if drone_id >= len(self.drones) or drone_id < 0:
            return Exception("Invalid drone_id")
        else:
            self.drones[drone_id].set_telemetry_info(telemetry_info)

    @updateAttributes
    def set_connected(self, drone_id, connected):
        self.drones[drone_id].connected = connected

    def update_attribute(self, attribute):
        attribute_drones = [getattr(drone, attribute) is True for drone in self.drones]
        if all(attribute_drones):
            setattr(self, attribute, 1)
        elif any(attribute_drones):
            setattr(self, attribute, 0)
        else:
            setattr(self, attribute, -1)
