import os
import sys
import tkinter as tk
from PIL import Image, ImageTk
from geographiclib.geodesic import Geodesic
import math


class MapViewHandler:
    def __init__(self, parent):
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

        # Drone class list
        self.drone_list = None

    def getFrame(self):
        return self.masterFrame

    def set_telemetry_info(self, _id, telemetry_info):
        for _drone in self.drone_list:
            if _drone.id == _id:
                _drone.set_telemetry_info(telemetry_info)
                _drone.update_crosshair(self.coordinates, self.map_canvas)

    def set_max_drones(self, max_drones):
        self.drone_list = set(Drone(drone_id) for drone_id in range(max_drones))


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
    def __init__(self):
        self.crosshair_image_tk = tk.PhotoImage(file=__file__[:-32]+"assets\\crosshair_smaller.png")
        self.state = tk.HIDDEN
        self.position = []
        self.id = None

    def place_crosshair(self, map_canvas):
        self.id = map_canvas.create_image(0, 0, image=self.crosshair_image_tk, anchor=tk.NW,
                                                    state=self.state)

    def set_state(self, map_canvas, state):
        self.state = state
        map_canvas.itemconfig(self.id, state=state)

    def set_position(self, map_canvas, position):
        self.position = position
        map_canvas.moveto(self.id, position[0] - 19, position[1] - 19)


class Drone:
    def __init__(self, _id):
        self.id = _id
        self.telemetry_info = None
        self.crosshair = Crosshair()

    def set_telemetry_info(self, telemetry_info):
        self.telemetry_info = telemetry_info

    def update_crosshair(self, coordinates, map_canvas):
        # If the crosshair is not in the map, place it
        if self.crosshair.id is None:
            self.crosshair.place_crosshair(map_canvas)
        # Update its position
        position = coordinates.ll_to_xy(self.telemetry_info["lat"], self.telemetry_info["lon"])
        self.crosshair.set_position(map_canvas, position)
        # Set its state
        if self.telemetry_info["state"] == "disconnected":
            self.crosshair.set_state(map_canvas, tk.HIDDEN)
        else:
            self.crosshair.set_state(map_canvas, tk.NORMAL)


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
    mapViewClass = MapViewHandler(testMaster, 1)
    mapViewClass.getFrame().pack()
    testMaster.mainloop()
