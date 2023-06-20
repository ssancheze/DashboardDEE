import tkinter as tk
from PIL import Image, ImageTk
from geographiclib.geodesic import Geodesic
import math
from dashboardClasses.DroneClass import Drone

# FILL COLOR OF THE MAP CROSSHAIR DEPENDING ON THE DRONE STATE
TK_STATE_COLORS = {
    'connected': 'green',
    'arming': 'GreenYellow',
    'armed': 'yellow',
    'disarmed': 'green',
    'takingOff': 'orange',
    'flying': 'red',
    'returningHome': 'red4',
    'landing': 'red4',
    'onHearth': 'green',
}
# CROSSHAIR SIZE USED FOR DISPLAY IN MAP
_CROSSHAIR_SIZE = 10


def find_center(map_canvas, item):
    coords = map_canvas.bbox(item)
    offset = ((coords[2] - coords[0])/2, (coords[3] - coords[1])/2)
    return offset


class MapViewHandler:
    def __init__(self, parent, operation_drones):
        # Main frame hosting everything
        self.parent = parent
        self.masterFrame = tk.LabelFrame(parent, text="Map view", padx=5, pady=5)

        # Canvas hosting map and drone indicators
        self.map_canvas = tk.Canvas(self.masterFrame, width=800, height=600, bg="white")
        self.map_canvas.pack(expand=tk.YES, anchor=tk.CENTER)

        # Coordinate class to perform calculations
        self.coordinates = Coordinates()

        # Map class
        self.map = Map()
        self.map.load_map(self.map_canvas)

        """
        # Drone class list
        self.drone_list = None
        """

        # User-selected drone in map, used in telemetry frame
        self.selected_drone = 0

        # List of operation drones, defined in Dashboard.py
        self.operation_drones = operation_drones

        # operation_drones child class list for display purposes
        self.map_drones = list()

    def getFrame(self):
        return self.masterFrame

    def update_drone(self, _id):
        self.map_drones[_id].update_crosshair(self.coordinates, self.map_canvas)

    def set_selected_drone(self, selected_drone):
        self.selected_drone = selected_drone

    def operation_drones_max_drones_defined(self):
        self.map_drones = [MapDrone(drone, _id, self) for _id, drone in enumerate(self.operation_drones.drones)]


class Coordinates:
    def __init__(self):
        self.geode = Geodesic.WGS84
        self.ll_ref = [41.2763748, 1.9889669]
        self.px_ref = [651, 279]
        self.ppm = 8.91265597  # 1/0.1122

    def ll_to_xy(self, lat, long):
        g = self.geode.Inverse(
            float(lat),
            float(long),
            self.ll_ref[0],
            self.ll_ref[1],
        )
        azimuth = 180 - float(g["azi2"])
        dist = float(g["s12"])

        x = self.px_ref[0] - math.trunc(
            dist * self.ppm * math.sin(math.radians(azimuth))
        )
        y = self.px_ref[1] - math.trunc(
            dist * self.ppm * math.cos(math.radians(azimuth))
        )
        return x, y


class Crosshair:
    def __init__(self, drone):

        self.crosshair_args = ((0, 0), (_CROSSHAIR_SIZE, _CROSSHAIR_SIZE))
        self.canvas_tag = None
        self.visibility = tk.HIDDEN
        self.position = []
        self.id = None
        self.drone = drone

    def place_crosshair(self, map_canvas):
        self.id = map_canvas.create_oval(*self.crosshair_args, offset=tk.CENTER)
        self.canvas_tag = map_canvas.create_text(0, 0, text='', anchor='center', fill='white')
        map_canvas.tag_bind(self.id, '<Button-1>', self.on_crosshair_click)

    def set_visibility(self, map_canvas, visibility):
        self.visibility = visibility
        map_canvas.itemconfig(self.id, state=visibility)

    def set_position(self, map_canvas, position):
        self.position = position
        map_canvas.moveto(self.id, position[0] - _CROSSHAIR_SIZE/2, position[1] - _CROSSHAIR_SIZE/2)
        offset = find_center(map_canvas, self.canvas_tag)
        map_canvas.moveto(self.canvas_tag, position[0] - offset[0], position[1] + offset[1])

    def set_fill_color(self, map_canvas, color):
        map_canvas.itemconfig(self.id, fill=color)

    def set_canvas_tag(self, map_canvas, drone_id):
        map_canvas.itemconfig(self.canvas_tag, text=f'{drone_id+1}')

    def on_crosshair_click(self, event):
        self.drone.set_mapViewHandler_selected_drone(self.drone.drone_id)


class MapDrone:
    def __init__(self, drone, _id, mapViewHandler):
        self.drone = drone
        self.drone_id = _id
        self.crosshair = Crosshair(self)
        self.mapViewHandler = mapViewHandler

    def update_crosshair(self, coordinates, map_canvas):
        # If the crosshair is not in the map, place it
        if self.crosshair.id is None:
            self.crosshair.place_crosshair(map_canvas)
            self.crosshair.set_canvas_tag(map_canvas, self.drone_id)
        # Update its position
        if self.drone.telemetry_info:
            position = coordinates.ll_to_xy(self.drone.telemetry_info["lat"], self.drone.telemetry_info["lon"])
            self.crosshair.set_position(map_canvas, position)
            # Set its fill color
            self.crosshair.set_fill_color(map_canvas, TK_STATE_COLORS[self.drone.telemetry_info['state']])
            # Set its visibility
            if self.drone.telemetry_info["state"] == "disconnected":
                self.crosshair.set_visibility(map_canvas, tk.HIDDEN)
            else:
                self.crosshair.set_visibility(map_canvas, tk.NORMAL)

    def set_mapViewHandler_selected_drone(self, _id):
        self.mapViewHandler.set_selected_drone(_id)


class Map:
    def __init__(self):
        # Map image and loading to canvas
        self.map_image = Image.open(__file__[:-32]+"assets\\dronLab.png")
        self.map_image = self.map_image.resize((800, 600))
        self.map_image_tk = ImageTk.PhotoImage(self.map_image)

    def load_map(self, map_canvas):
        map_canvas.create_image(2, 0, image=self.map_image_tk, anchor=tk.NW)


if __name__ == "__main__":
    testMaster = tk.Tk()
    testMaster.title = "DEBUG"
    mapViewClass = MapViewHandler(testMaster)

    telemetry_info1 = {
        'lat': 41.27630767131425,
        'lon': 1.9886698469838262,
        'heading': 270,
        'groundSpeed': 6,
        'altitude': 10,
        'battery': 37,
        'state': 'flying'
    }

    telemetry_info2 = {
        'lat': 41.276485,
        'lon': 1.988801,
        'heading': 270,
        'groundSpeed': 6,
        'altitude': 10,
        'battery': 37,
        'state': 'takingOff'
    }

    mapViewClass.getFrame().pack()

    testMaster.mainloop()
