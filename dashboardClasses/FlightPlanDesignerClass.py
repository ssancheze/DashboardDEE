import tkinter as tk
from ttkwidgets import CheckboxTreeview
from tkinter import *
import json
import math
from geographiclib.geodesic import Geodesic

from tkinter.filedialog import asksaveasfile, askopenfilename
from tkinter import messagebox
from PIL import Image, ImageTk
from dashboardClasses.TelemetryInfoFrameClass import TelemetryInfoFrame


class ComputeCoords:
    def __init__(self):
        self.geod = Geodesic.WGS84
        self.mpp = 0.1122
        self.ppm = 1 / self.mpp
        # one point (x,y) in the canvas and the corresponding position (lat,lon)
        self.refCoord = [651, 279]
        self.refPosition = [41.2763748, 1.9889669]

    def convertToCoords(self, position):
        g = self.geod.Inverse(
            float(position[0]),
            float(position[1]),
            self.refPosition[0],
            self.refPosition[1],
        )
        azimuth = 180 - float(g["azi2"])
        dist = float(g["s12"])

        # ATENCION: NO SE POR QUE AQUI TENGO QUE RESTAR EN VEZ DE SUMAR
        x = self.refCoord[0] - math.trunc(
            dist * self.ppm * math.sin(math.radians(azimuth))
        )
        y = self.refCoord[1] - math.trunc(
            dist * self.ppm * math.cos(math.radians(azimuth))
        )
        return x, y

    def convertToPosition(self, coords):
        # compute distance with ref coords
        dist = (
            math.sqrt(
                (coords[0] - self.refCoord[0]) ** 2
                + (coords[1] - self.refCoord[1]) ** 2
            )
            * self.mpp
        )
        # compute azimuth
        # azimuth = math.degrees(math.atan2((self.previousx - e.x), (self.previousy - e.y))) * (-1)

        azimuth = math.degrees(
            math.atan2((self.refCoord[0] - coords[0]), (self.refCoord[1] - coords[1]))
        ) * (-1)
        if azimuth < 0:
            azimuth = azimuth + 360
        # compute lat,log of new wayp
        g = self.geod.Direct(
            float(self.refPosition[0]), float(self.refPosition[1]), azimuth, dist
        )
        lat = float(g["lat2"])
        lon = float(g["lon2"])
        return lat, lon


class WaypointsWindow:
    def buildFrame(self, frame):
        self.window = tk.LabelFrame(frame, text="Waypoints")
        lab = tk.Label(self.window, text="List of waypoints", font=("Calibri", 20))
        lab.grid(row=0, column=0)

        self.table = CheckboxTreeview(self.window)
        self.table.grid(row=1, column=0, padx=20)
        self.wpNumber = 1
        return self.window

    def removeEntries(self):
        for i in self.table.get_children():
            self.table.delete(i)
        self.wpNumber = 1

    def insertHome(self, lat, lon):
        self.table.insert(
            parent="",
            index="end",
            iid=0,
            text="H:  {0:5}, {1:5}".format(round(lat, 6), round(lon, 6)),
        )

    def insertWP(self, lat, lon):
        # complete a single digit wpNumber with left-size zero
        res = str(self.wpNumber).rjust(2, "0")
        self.table.insert(
            parent="",
            index="end",
            iid=self.wpNumber,
            text="{0}:  {1:5}, {2:5}".format(res, round(lat, 6), round(lon, 6)),
        )
        self.wpNumber = self.wpNumber + 1

    def getCoordinates(self, wpId):
        entries = self.table.get_children()
        for i in range(1, len(entries)):
            if int(self.table.item(entries[i])["text"].split(":")[0]) == int(wpId):
                k = i
                break

        location = self.table.item(entries[k])["text"].split(":")[1].split(",")
        lat = float(location[0])
        lon = float(location[1])

        return lat, lon

    def changeCoordinates(self, wpId, lat, lon):
        entries = self.table.get_children()
        for i in range(1, len(entries)):
            if int(self.table.item(entries[i])["text"].split(":")[0]) == int(wpId):
                k = i
                break
        # complete a single digit wpNumber with left-size zero
        res = str(wpId).rjust(2, "0")
        self.table.item(
            entries[k],
            text="{0}:  {1:5}, {2:5}".format(res, round(lat, 6), round(lon, 6)),
        )

    def insertRTL(self):
        self.table.insert(parent="", index="end", iid=self.wpNumber, text="RTL")

    def getWaypoints(self):
        waypoints = []
        checkedList = self.table.get_checked()
        entries = self.table.get_children()

        for entry in entries[:-1]:
            if entry in checkedList:
                take = True
            else:
                take = False
            location = self.table.item(entry)["text"].split(":")[1].split(",")
            lat = float(location[0])
            lon = float(location[1])
            waypoints.append({"lat": lat, "lon": lon, "takePic": take})
        return waypoints

    def checkLastEntry(self):
        self.table.change_state(self.table.get_children()[-1], "checked")

    def focus_force(self):
        self.window.focus_force()


class FlightPlanDesignerWindow:
    def __init__(self, frame, mode, client, originPosition):
        self.frame = frame  # father frame
        self.mode = mode
        self.client = client
        self.originPosition = originPosition
        self.originlat = originPosition[0]
        self.originlon = originPosition[1]

        self.done = False
        self.firstPoint = True
        self.secondPoint = False
        self.thirdPoint = False
        self.fourthPoint = False

        self.wpNumber = 1
        self.geod = Geodesic.WGS84
        self.waypointsIds = []
        self.defaultDistance = (
            10  # default distance for parallelogram and spiral scans (10 meters)
        )
        self.canvas = None
        self.dronePositionId = None
        self.myTelemetryInfoFrameClass = None
        self.converter = ComputeCoords()
        self.state = "waiting"

    def showTelemetryInfo(self, telemetyInfo):
        if not self.closed:
            self.myTelemetryInfoFrameClass.showTelemetryInfo(telemetyInfo)

            if self.canvas != None and self.dronePositionId != None:
                lat = telemetyInfo["lat"]
                lon = telemetyInfo["lon"]
                state = telemetyInfo["state"]
                newposx, newposy = self.converter.convertToCoords((lat, lon))
                # if state == 'arming' or state == 'disarmed':
                color = "yellow"

                if state == "takingOff" or state == "landing":
                    color = "orange"
                elif state == "flying":
                    color = "red"
                elif state == "returningHome":
                    color = "brown"
                self.canvas.itemconfig(self.dronePositionId, fill=color)
                self.canvas.coords(
                    self.dronePositionId,
                    newposx - 15,
                    newposy - 15,
                    newposx + 15,
                    newposy + 15,
                )

    """'
    def setArmed(self):
        self.state = 'armed'
    def setArming(self):
        self.state = 'arming'
    def setFlying(self):
        self.state = 'flying'
    def setAtHome(self):
        self.state = 'atHome'
    def setLanding (self):
        print ('landing')
        self.state = 'landing'
    def setDisarmed(self):
        self.state = 'disarmed'
    """

    def openWindowToCreateFlightPlan(self):
        self.newWindow = tk.Toplevel(self.frame)
        self.newWindow.title("Create and execute flight plan")
        self.newWindow.geometry("1200x800")
        self.newWindow.rowconfigure(0, weight=1)
        self.newWindow.rowconfigure(1, weight=5)
        self.newWindow.rowconfigure(2, weight=10)
        self.newWindow.columnconfigure(0, weight=5)
        self.newWindow.columnconfigure(1, weight=1)
        self.newWindow.columnconfigure(2, weight=5)

        title = tk.Label(
            self.newWindow, text="Create and execute flight plan", font=("Calibri", 25)
        )
        title.grid(row=0, column=0, columnspan=3)

        self.canvas = tk.Canvas(self.newWindow, width=800, height=600)
        self.canvas.grid(row=1, column=0, rowspan=2, padx=(5, 0))

        self.controlFrame = tk.LabelFrame(
            self.newWindow, text="Control", width=200, height=700
        )
        self.controlFrame.grid(row=1, column=1, rowspan=2, padx=10)
        if self.mode == 0 or self.mode == 1:
            self.clearButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Clear",
                bg="#375E97",
                fg="white",
                command=self.clear,
            )
            self.clearButton.grid(row=0, column=0, padx=10, pady=0)
            runButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Run",
                bg="#FFBB00",
                fg="black",
                command=self.runButtonClick,
            )
            runButton.grid(row=1, column=0, padx=10, pady=20)
            saveButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Save",
                bg="#FB6542",
                fg="white",
                command=self.saveButtonClick,
            )
            saveButton.grid(row=2, column=0, padx=10, pady=20)
            closeButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Close",
                bg="#B7BBB6",
                fg="white",
                command=self.closeWindowToToCreateFlightPlan,
            )
            closeButton.grid(row=3, column=0, padx=10, pady=20)

        else:
            self.sliderFrame = tk.LabelFrame(
                self.controlFrame, text="Select separation (meters)"
            )
            self.sliderFrame.grid(row=0, column=0, padx=10, pady=(20, 5))
            self.label = tk.Label(self.sliderFrame, text="create scan first").pack()

            self.clearButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Clear",
                bg="#375E97",
                fg="white",
                command=self.clear,
            )
            self.clearButton.grid(row=1, column=0, padx=10, pady=(5, 20))

            runButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Run",
                bg="#FFBB00",
                fg="black",
                command=self.runButtonClick,
            )
            runButton.grid(row=2, column=0, padx=10, pady=20)

            saveButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Save",
                bg="#FB6542",
                fg="white",
                command=self.saveButtonClick,
            )
            saveButton.grid(row=3, column=0, padx=10, pady=20)

            closeButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Close",
                bg="#B7BBB6",
                fg="white",
                command=self.closeWindowToToCreateFlightPlan,
            )
            closeButton.grid(row=4, column=0, padx=10, pady=20)

        self.wpWindow = WaypointsWindow()
        self.wpFrame = self.wpWindow.buildFrame(self.newWindow)
        self.wpFrame.grid(row=1, column=2, padx=10)

        self.myTelemetryInfoFrameClass = TelemetryInfoFrame()
        self.telemetryInfoFrame = self.myTelemetryInfoFrameClass.buldFrame(
            self.newWindow
        )
        self.telemetryInfoFrame.grid(row=2, column=2, padx=10)

        # self.mpp (meters per pixel) depends on the zoom level of the dronLab picture
        # we are using a picture with zoom level = 20
        # Zoom level: 19, mpp = 0.2235
        # Zoom level: 20, mpp = 0.1122
        # more interesting information here: https://docs.mapbox.com/help/glossary/zoom-level/
        self.mpp = 0.1122
        self.ppm = 1 / self.mpp
        self.d = self.defaultDistance

        self.img = Image.open("assets/dronLab.png")
        self.img = self.img.resize((800, 600), Image.ANTIALIAS)
        self.bg = ImageTk.PhotoImage(self.img)
        self.image = self.canvas.create_image(0, 0, image=self.bg, anchor="nw")

        # I do no know why but the next sentences is necessary
        self.frame.img = self.img

        if self.mode == 0:
            instructionsText = (
                "Click in home position \nand select the file with the flight plan"
            )
        if self.mode == 1:
            instructionsText = (
                "Click in home position \nand fix the sequence of waypoints"
            )
        if self.mode == 2:
            instructionsText = (
                "Click in home position \nand define parallelogram to be scaned"
            )
        if self.mode == 3:
            instructionsText = (
                "Click in home position \nand decide spiral direction and length"
            )

        self.instructionsTextId = self.canvas.create_text(
            300, 400, text=instructionsText, font=("Courier", 10, "bold")
        )

        bbox = self.canvas.bbox(self.instructionsTextId)
        self.instructionsBackground = self.canvas.create_rectangle(bbox, fill="yellow")
        self.canvas.tag_raise(self.instructionsTextId, self.instructionsBackground)
        home_x, home_y = self.converter.convertToCoords(
            (self.originPosition[0], self.originPosition[1])
        )
        self.homeMark = self.canvas.create_text(
            home_x, home_y, text="H", font=("Courier", 20, "bold"), fill="yellow"
        )

        self.canvas.bind("<ButtonPress-1>", self.click)
        self.canvas.bind("<Motion>", self.drag)
        if self.mode == 1:
            self.canvas.bind("<ButtonPress-3>", self.returnToLaunch)

        self.closed = False

    def closeWindowToToCreateFlightPlan(self):
        self.firstPoint = True
        self.secondPoint = False
        self.thirdPoint = False
        self.done = False
        self.closed = True
        self.newWindow.destroy()

    def runButtonClick(self):
        waypoints = self.wpWindow.getWaypoints()
        print("vaypoints ", waypoints)
        waypoints_json = json.dumps(waypoints)
        self.client.publish(
            "dashBoard/autopilotService/executeFlightPlan", waypoints_json
        )

        self.dronPositionx = self.originlat
        self.dronPositiony = self.originlon
        self.dronePositionPixelx = self.originx
        self.dronePositionPixely = self.originy
        if self.dronePositionId == None:
            self.dronePositionId = self.canvas.create_oval(
                self.originx - 15,
                self.originy - 15,
                self.originx + 15,
                self.originy + 15,
                fill="yellow",
            )
        self.state = "arming"

    def clear(self):
        self.firstPoint = True
        self.secondPoint = False
        self.thirdPoint = False
        self.done = False
        self.wpNumber = 1

        items = self.canvas.find_all()

        for item in items:
            if item != self.image and item != self.homeMark:
                self.canvas.delete(item)

        self.wpWindow.removeEntries()

        if self.mode == 2 or self.mode == 3:
            self.sliderFrame.destroy()

            self.sliderFrame = tk.LabelFrame(
                self.controlFrame, text="Select separation (meters)"
            )
            self.sliderFrame.grid(row=0, column=0, padx=10, pady=20)

            self.label = tk.Label(self.sliderFrame, text="create first").pack()

        self.d = self.defaultDistance

        if self.mode == 0:
            instructionsText = (
                "Click in home position \nand select the file with the flight plan"
            )
        if self.mode == 1:
            instructionsText = (
                "Click in home position \nand fix the sequence of waypoints"
            )
        if self.mode == 2:
            instructionsText = (
                "Click in home position \nand define parallelogram to be scaned"
            )
        if self.mode == 3:
            instructionsText = (
                "Click in home position \nand decide spiral direction and length"
            )

        self.instructionsTextId = self.canvas.create_text(
            300, 400, text=instructionsText, font=("Courier", 10, "bold")
        )
        bbox = self.canvas.bbox(self.instructionsTextId)
        self.instructionsBackground = self.canvas.create_rectangle(bbox, fill="yellow")
        self.canvas.tag_raise(self.instructionsTextId, self.instructionsBackground)
        self.canvas.bind("<Motion>", self.drag)

    def saveButtonClick(self):
        waypoints = self.wpWindow.getWaypoints()
        f = asksaveasfile(mode="w", defaultextension=".json")
        if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            messagebox.showinfo(message="Flight plan NOT saved", title="File save")
        else:
            waypoints_json = json.dumps(waypoints)
            f.write(waypoints_json)
            f.close()
            messagebox.showinfo(message="Flight plan saved", title="File save")
        self.newWindow.focus_force()

    def drawFlighPlan(self, waypoints):

        self.waypointsIds = []
        home = waypoints[0]
        ovalId = self.canvas.create_oval(
            self.originx - 10,
            self.originy - 10,
            self.originx + 10,
            self.originy + 10,
            fill="blue",
        )
        textId = self.canvas.create_text(
            self.originx,
            self.originy,
            text="H",
            font=("Courier", 10, "bold"),
            fill="white",
        )
        prev = home
        posx = self.originx
        posy = self.originy
        wpNum = 1
        self.waypointsIds.append(
            {
                "wpId": "H",
                "textId": textId,
                "ovalId": ovalId,
                "lineInId": 0,
                "lineOutId": 0,
                "distanceFromId": 0,
                "distanceToId": 0,
            }
        )
        self.wpWindow.insertHome(home["lat"], home["lon"])
        if home["takePic"]:
            self.wpWindow.checkLastEntry()

        for wp in waypoints[1:]:
            g = self.geod.Inverse(
                float(prev["lat"]),
                float(prev["lon"]),
                float(wp["lat"]),
                float(wp["lon"]),
            )
            azimuth = 180 - float(g["azi2"])
            dist = float(g["s12"])

            newposx = posx + math.trunc(
                dist * self.ppm * math.sin(math.radians(azimuth))
            )
            newposy = posy + math.trunc(
                dist * self.ppm * math.cos(math.radians(azimuth))
            )
            lineId = self.canvas.create_line(posx, posy, newposx, newposy)
            distId = self.canvas.create_text(
                posx + (newposx - posx) / 2,
                posy + (newposy - posy) / 2,
                text=str(round(dist, 2)),
                font=("Courier", 15, "bold"),
                fill="red",
            )
            posx = newposx
            posy = newposy
            ovalId = self.canvas.create_oval(
                posx - 10, posy - 10, posx + 10, posy + 10, fill="blue"
            )
            textId = self.canvas.create_text(
                posx, posy, text=str(wpNum), font=("Courier", 10, "bold"), fill="white"
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds[-1]["distanceToId"] = distId
            self.waypointsIds.append(
                {
                    "wpId": str(wpNum),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                    "distanceFromId": distId,
                    "distanceToId": 0,
                }
            )
            self.wpWindow.insertWP(wp["lat"], wp["lon"])
            if wp["takePic"]:
                self.wpWindow.checkLastEntry()
            wpNum = wpNum + 1
            prev = wp

        lineId = self.canvas.create_line(posx, posy, self.originx, self.originy)
        g = self.geod.Inverse(
            float(prev["lat"]),
            float(prev["lon"]),
            float(home["lat"]),
            float(home["lon"]),
        )
        dist = float(g["s12"])
        distId = self.canvas.create_text(
            posx + (self.originx - posx) / 2,
            posy + (self.originy - posy) / 2,
            text=str(round(dist, 2)),
            font=("Courier", 15, "bold"),
            fill="red",
        )
        self.waypointsIds[-1]["lineOutId"] = lineId
        self.waypointsIds[-1]["distanceToId"] = distId
        self.waypointsIds[0]["lineInId"] = lineId
        self.waypointsIds[0]["distanceFrom"] = distId
        self.wpWindow.insertRTL()
        self.wpWindow.focus_force()

    def click(self, e):
        if self.done:
            # if flight plan is done then the user wants to change the position of a waypoint
            # select the ids of elements of the canvas that are close to the clicked waypoint
            selected = self.canvas.find_overlapping(
                e.x - 10, e.y - 10, e.x + 10, e.y + 10
            )

            if selected:
                # finds the ids of the selected waypoint
                # Among the selected items there must be the id of the text of the selected waypoint
                self.waypointToMoveIds = [
                    wp for wp in self.waypointsIds if wp["textId"] in selected
                ][0]
                # now we are ready to drag the waypoint
                self.canvas.bind("<B1-Motion>", self.moveWp)

        elif self.mode == 0:
            if self.firstPoint:
                # origin point
                self.originx = e.x
                self.originy = e.y
                self.canvas.delete(self.instructionsTextId)
                self.canvas.delete(self.instructionsBackground)

                fileName = askopenfilename()
                if (
                    fileName is None
                ):  # asksaveasfile return `None` if dialog closed with "cancel".
                    messagebox.showinfo(message="NO file selected", title="File open")
                else:
                    messagebox.showinfo(message="File selected", title="File open")
                    file = open(fileName)
                    waypoints = json.load(file)
                    self.drawFlighPlan(waypoints)
                self.newWindow.focus_force()
                self.done = True
                self.firstPoint = False

        elif self.mode == 1:

            if self.firstPoint:
                self.canvas.delete(self.instructionsTextId)
                self.canvas.delete(self.instructionsBackground)
                # the user select the position for the initial waypoint
                self.firstPoint = False
                # I must remember the clicked coordinates, that in this case will be also the origin coordinates

                # previous point
                self.previousx = e.x
                self.previousy = e.y

                # origin point
                self.originx = e.x
                self.originy = e.y

                # Create a line starting in origin
                self.lineOutId = self.canvas.create_line(
                    self.originx, self.originy, e.x, e.y
                )
                # Create oval and text por the origin (H) waypoint
                self.ovalId = self.canvas.create_oval(
                    e.x - 10, e.y - 10, e.x + 10, e.y + 10, fill="blue"
                )
                self.textId = self.canvas.create_text(
                    e.x, e.y, text="H", font=("Courier", 10, "bold"), fill="white"
                )
                # create a text for the distance
                self.distanceToId = self.canvas.create_text(
                    e.x, e.y, text="0", font=("Courier", 15, "bold"), fill="red"
                )

                # adds to the list the ids of the elements corresponding to the home waypoint
                self.waypointsIds.append(
                    {
                        "wpId": "H",
                        "textId": self.textId,
                        "ovalId": self.ovalId,
                        "lineInId": 0,
                        "lineOutId": self.lineOutId,
                        "distanceFromId": 0,
                        "distanceToId": self.distanceToId,
                    }
                )

                # current lat, lon are the origin coordinates
                self.lat = self.originlat
                self.lon = self.originlon

                # insert information of origin waypoint in the table
                self.wpWindow.insertHome(self.lat, self.lon)
            else:
                # the user is fixing the next waypoint
                # create the elements (line, oval, text and distance) for the new waypoint
                self.lineId = self.canvas.create_line(e.x, e.y, e.x, e.y)
                self.ovalId = self.canvas.create_oval(
                    e.x - 10, e.y - 10, e.x + 10, e.y + 10, fill="blue"
                )
                self.textId = self.canvas.create_text(
                    e.x,
                    e.y,
                    text=str(self.wpNumber),
                    font=("Courier", 10, "bold"),
                    fill="white",
                )
                self.distanceId = self.canvas.create_text(
                    e.x, e.y, text="0", font=("Courier", 15, "bold"), fill="red"
                )

                # adds the ids of the new waypoint to the list
                self.waypointsIds.append(
                    {
                        "wpId": self.wpNumber,
                        "textId": self.textId,
                        "ovalId": self.ovalId,
                        "lineInId": self.waypointsIds[-1]["lineOutId"],
                        "lineOutId": self.lineId,
                        "distanceFromId": self.waypointsIds[-1]["distanceToId"],
                        "distanceToId": self.distanceId,
                    }
                )
                self.lat, self.lon = self.converter.convertToPosition((e.x, e.y))
                """
                    # compute distance from previous waypoint
                    dist = math.sqrt((e.x - self.previousx) ** 2 + (e.y - self.previousy) ** 2) * self.mpp
                    # compute azimuth
                    azimuth = math.degrees(math.atan2((self.previousx - e.x), (self.previousy - e.y))) * (-1)
                    if azimuth < 0:
                        azimuth = azimuth + 360
                    # compute lat,log of new waypoint
                    g = self.geod.Direct(float(self.lat), float(self.lon), azimuth, dist)
                    self.lat = float(g['lat2'])
                    self.lon = float(g['lon2'])
                    """
                # insert new waypoint in table
                self.wpWindow.insertWP(self.lat, self.lon)

                # update previouos point
                self.previousx = e.x
                self.previousy = e.y
                self.wpNumber = self.wpNumber + 1

        elif self.mode == 2:
            if self.firstPoint:
                self.canvas.delete(self.instructionsTextId)
                self.canvas.delete(self.instructionsBackground)
                # the user starts defining the area (rectangle) to be scanned
                # Four points (A, B, C and D) must be defined
                self.originposx = e.x
                self.originposy = e.y
                self.originx = e.x
                self.originy = e.y
                self.firstPoint = False
                self.secondPoint = True
                # I must remember the clicked coordinates, that in this case will be also the origin coordinates

                self.points = []
                # A point
                self.Ax = e.x
                self.Ay = e.y
                self.points.append((self.Ax, self.Ay))
                self.points.append((self.Ax, self.Ay))
                self.points.append((self.Ax, self.Ay))
                self.points.append((self.Ax, self.Ay))
                self.rectangle = self.canvas.create_polygon(
                    self.points, outline="red", fill="", width=5
                )
                self.distanceX = self.canvas.create_text(
                    e.x, e.y, text="0", font=("Courier", 15, "bold"), fill="red"
                )

            elif self.secondPoint:
                # the user is fixing point B
                self.secondPoint = False
                self.thirdPoint = True

                self.Bx = e.x
                self.By = e.y

                self.azimuth1 = math.degrees(
                    math.atan2((self.Ax - e.x), (self.Ay - e.y))
                ) * (-1)
                if self.azimuth1 < 0:
                    self.azimuth1 = self.azimuth1 + 360
                self.x = math.sqrt((e.x - self.Ax) ** 2 + (e.y - self.Ay) ** 2)
                self.distanceY = self.canvas.create_text(
                    e.x, e.y, text="0", font=("Courier", 15, "bold"), fill="red"
                )

                self.wpNumber = self.wpNumber + 1
            elif self.thirdPoint:
                # the user is fixing point C
                self.thirdPoint = False
                self.azimuth2 = math.degrees(
                    math.atan2((self.Bx - e.x), (self.By - e.y))
                ) * (-1)
                if self.azimuth2 < 0:
                    self.azimuth2 = self.azimuth2 + 360
                self.y = math.sqrt((e.x - self.Bx) ** 2 + (e.y - self.By) ** 2)

                self.createScan()

                self.sliderFrame.destroy()

                self.sliderFrame = tk.LabelFrame(
                    self.controlFrame, text="Select separation (meters)"
                )
                self.sliderFrame.grid(row=0, column=0, padx=10, pady=20)

                self.slider = tk.Scale(
                    self.sliderFrame,
                    from_=2,
                    to=10,
                    length=150,
                    orient="horizontal",
                    activebackground="green",
                    tickinterval=2,
                    resolution=2,
                    command=self.reCreate,
                )
                self.slider.grid(row=0, column=0, padx=0, pady=0)

        else:
            if self.firstPoint:

                self.canvas.delete(self.instructionsTextId)
                self.canvas.delete(self.instructionsBackground)

                # the user starts defining the area (rectangle) to be scanned
                # Four points (A, B, C and D) must be defined

                self.originx = e.x
                self.originy = e.y
                self.firstPoint = False
                self.secondPoint = True
                # I must remember the clicked coordinates, that in this case will be also the origin coordinates

                # A point
                self.Ax = e.x
                self.Ay = e.y

                self.line = self.canvas.create_line(
                    self.Ax, self.Ay, e.x, e.y, fill="red", width=3
                )
                self.distance = self.canvas.create_text(
                    e.x, e.y, text="0", font=("Courier", 15, "bold"), fill="red"
                )
            elif self.secondPoint:
                # the user is fixing point B
                self.secondPoint = False
                self.azimuth = math.degrees(
                    math.atan2((self.Ax - e.x), (self.Ay - e.y))
                ) * (-1)
                if self.azimuth < 0:
                    self.azimuth = self.azimuth + 360
                self.x = math.sqrt((e.x - self.Ax) ** 2 + (e.y - self.Ay) ** 2)

                self.createSpiral()

                self.sliderFrame.destroy()

                self.sliderFrame = tk.LabelFrame(
                    self.controlFrame, text="Select separation (meters)"
                )
                self.sliderFrame.grid(row=0, column=0, padx=10, pady=20)
                self.slider = tk.Scale(
                    self.sliderFrame,
                    from_=10,
                    to=50,
                    length=150,
                    orient="horizontal",
                    activebackground="green",
                    tickinterval=10,
                    resolution=10,
                    command=self.reCreate,
                )
                self.slider.grid(row=0, column=0, padx=0, pady=0)

    def drag(self, e):

        if self.mode == 1:
            if not self.firstPoint:
                # the user is draging the mouse to decide where to place next waypoint
                dist = (
                    math.sqrt((e.x - self.previousx) ** 2 + (e.y - self.previousy) ** 2)
                    * self.mpp
                )

                # show distance in the middle of the line
                self.canvas.coords(
                    self.waypointsIds[-1]["distanceToId"],
                    self.previousx + (e.x - self.previousx) / 2,
                    self.previousy + (e.y - self.previousy) / 2,
                )
                self.canvas.itemconfig(
                    self.waypointsIds[-1]["distanceToId"], text=str(round(dist, 2))
                )
                # Change the coordinates of the last created line to the new coordinates
                self.canvas.coords(
                    self.waypointsIds[-1]["lineOutId"],
                    self.previousx,
                    self.previousy,
                    e.x,
                    e.y,
                )

        if self.mode == 2:
            if self.secondPoint:
                # the user is draging the mouse to decide the direction and lenght of the first dimension of parallelogram
                self.points[1] = (e.x, e.y)
                self.points[2] = (e.x, e.y)
                self.canvas.delete(self.rectangle)
                self.rectangle = self.canvas.create_polygon(
                    self.points, outline="red", fill="", width=5
                )
                dist = math.sqrt((e.x - self.Ax) ** 2 + (e.y - self.Ay) ** 2) * self.mpp

                # show distance in the middle of the line
                self.canvas.coords(
                    self.distanceX,
                    self.Ax + (e.x - self.Ax) / 2,
                    self.Ay + (e.y - self.Ay) / 2,
                )
                self.canvas.itemconfig(self.distanceX, text=str(round(dist, 2)))
            elif self.thirdPoint:
                # the user is draging the mouse to decide the direction and lenght of the second dimension of parallelogram

                dist = math.sqrt((e.x - self.Bx) ** 2 + (e.y - self.By) ** 2)
                angle = math.degrees(math.atan2((self.Bx - e.x), (self.By - e.y))) * (
                    -1
                )
                if angle < 0:
                    angle = angle + 360

                Cx = self.Bx + dist * math.cos(math.radians(angle - 90))
                Cy = self.By + dist * math.sin(math.radians(angle - 90))

                Dx = self.Ax + dist * math.cos(math.radians(angle - 90))
                Dy = self.Ay + dist * math.sin(math.radians(angle - 90))

                self.points[2] = (Cx, Cy)
                self.points[3] = (Dx, Dy)
                self.canvas.delete(self.rectangle)
                self.rectangle = self.canvas.create_polygon(
                    self.points, outline="red", fill="", width=5
                )
                # show distance in the middle of the line
                self.canvas.coords(
                    self.distanceY,
                    self.Bx + (e.x - self.Bx) / 2,
                    self.By + (e.y - self.By) / 2,
                )
                self.canvas.itemconfig(
                    self.distanceY, text=str(round(dist * self.mpp, 2))
                )

        if self.mode == 3:
            if self.secondPoint:
                # the user is draging the mouse to decide the direction and lenght of spiral
                self.canvas.coords(self.line, self.Ax, self.Ay, e.x, e.y)
                dist = math.sqrt((e.x - self.Ax) ** 2 + (e.y - self.Ay) ** 2) * self.mpp

                # show distance in the middle of the line
                self.canvas.coords(
                    self.distance,
                    self.Ax + (e.x - self.Ax) / 2,
                    self.Ay + (e.y - self.Ay) / 2,
                )
                self.canvas.itemconfig(self.distance, text=str(round(dist, 2)))

    def moveWp(self, e):
        # the user is moving a waypoints
        # the ids of this waypoint are in waypointToMoveIds
        if not self.waypointToMoveIds["wpId"] == "H":
            # can move any waypoint except home
            # move the oval and the text
            self.canvas.coords(
                self.waypointToMoveIds["ovalId"], e.x - 10, e.y - 10, e.x + 10, e.y + 10
            )
            self.canvas.coords(self.waypointToMoveIds["textId"], e.x, e.y)

            # get coordinates of lineIn and lineout
            lineInCoord = self.canvas.coords(self.waypointToMoveIds["lineInId"])
            lineOutCoord = self.canvas.coords(self.waypointToMoveIds["lineOutId"])

            # these are the coordinates of the waypoint
            wpCoord = (lineInCoord[2], lineInCoord[3])

            # compute distance and azimuth from the current position of the waypoint

            dist = (
                math.sqrt((e.x - wpCoord[0]) ** 2 + (e.y - wpCoord[1]) ** 2) * self.mpp
            )
            azimuth = math.degrees(
                math.atan2((wpCoord[0] - e.x), (wpCoord[1] - e.y))
            ) * (-1)
            if azimuth < 0:
                azimuth = azimuth + 360
            lat, lon = self.wpWindow.getCoordinates(self.waypointToMoveIds["wpId"])

            # compute new position of the waypoint
            g = self.geod.Direct(lat, lon, azimuth, dist)
            lat = float(g["lat2"])
            lon = float(g["lon2"])

            # change info in the table
            self.wpWindow.changeCoordinates(self.waypointToMoveIds["wpId"], lat, lon)
            # self.table.item(entry, values=(self.waypointToMoveIds['wpId'], lat, lon))

            # change coordinates of arriving and departing lines
            self.canvas.coords(
                self.waypointToMoveIds["lineInId"],
                lineInCoord[0],
                lineInCoord[1],
                e.x,
                e.y,
            )
            self.canvas.coords(
                self.waypointToMoveIds["lineOutId"],
                e.x,
                e.y,
                lineOutCoord[2],
                lineOutCoord[3],
            )

            if self.mode == 0 or self.mode == 1:
                # change distance labels
                distFrom = (
                    math.sqrt((e.x - lineInCoord[0]) ** 2 + (e.y - lineInCoord[1]) ** 2)
                    * self.mpp
                )
                distTo = (
                    math.sqrt(
                        (e.x - lineOutCoord[2]) ** 2 + (e.y - lineOutCoord[3]) ** 2
                    )
                    * self.mpp
                )

                # show distance in the middle of the line
                self.canvas.coords(
                    self.waypointToMoveIds["distanceFromId"],
                    lineInCoord[0] + (e.x - lineInCoord[0]) / 2,
                    lineInCoord[1] + (e.y - lineInCoord[1]) / 2,
                )
                self.canvas.itemconfig(
                    self.waypointToMoveIds["distanceFromId"],
                    text=str(round(distFrom, 2)),
                )

                self.canvas.coords(
                    self.waypointToMoveIds["distanceToId"],
                    lineOutCoord[2] + (e.x - lineOutCoord[2]) / 2,
                    lineOutCoord[3] + (e.y - lineOutCoord[3]) / 2,
                )
                self.canvas.itemconfig(
                    self.waypointToMoveIds["distanceToId"], text=str(round(distTo, 2))
                )

    def returnToLaunch(self, e):

        # right button click to finish the flight plan (only in mode 1)

        # complete the ids of the home waypoint
        self.waypointsIds[0]["lineInId"] = self.waypointsIds[-1]["lineOutId"]
        self.waypointsIds[0]["distanceFromId"] = self.waypointsIds[-1]["distanceToId"]

        # modify last line to return to launch

        self.canvas.coords(
            self.waypointsIds[-1]["lineOutId"],
            self.previousx,
            self.previousy,
            self.originx,
            self.originy,
        )

        # compute distance to home
        dist = (
            math.sqrt(
                (self.originx - self.previousx) ** 2
                + (self.originy - self.previousy) ** 2
            )
            * self.mpp
        )

        self.canvas.coords(
            self.distanceId,
            self.previousx + (self.originx - self.previousx) / 2,
            self.previousy + (self.originy - self.previousy) / 2,
        )
        self.canvas.itemconfig(self.distanceId, text=str(round(dist, 2)))

        # insert return to launch in the table
        self.wpWindow.insertRTL()

        # change color of all lines
        for wp in self.waypointsIds:
            self.canvas.itemconfig(wp["lineOutId"], fill="blue")
            self.canvas.itemconfig(wp["lineOutId"], width=3)

        # ignore mouse drag from now on
        self.canvas.unbind("<Motion>")

        self.done = True

    def reCreate(self, event):
        # new distance for scan has been selected
        self.d = self.slider.get()
        self.wpWindow.removeEntries()
        self.dronePositionId = None

        items = self.canvas.find_all()
        if self.mode == 2:
            for item in items:
                if (
                    item != self.rectangle
                    and item != self.image
                    and item != self.distanceY
                    and item != self.distanceX
                ):
                    self.canvas.delete(item)
            self.createScan()

        if self.mode == 3:
            for item in items:
                if item != self.line and item != self.image and item != self.distance:
                    self.canvas.delete(item)
            self.createSpiral()

    def createScan(self):

        # azimuth1 = 180 - self.azimuth1
        # azimuth2 = 180 - self.azimuth2
        azimuth1 = self.azimuth1
        azimuth2 = self.azimuth2
        self.posx = self.originposx
        self.posy = self.originposy
        num = math.ceil(self.y / (self.d * self.ppm))
        waypoints = []
        self.waypointToMoveIds = []
        lat = float(self.originlat)
        lon = float(self.originlon)
        ovalId = self.canvas.create_oval(
            self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill="blue"
        )
        textId = self.canvas.create_text(
            self.posx, self.posy, text="H", font=("Courier", 10, "bold"), fill="white"
        )
        self.waypointsIds.append(
            {
                "wpId": "H",
                "textId": textId,
                "ovalId": ovalId,
                "lineInId": 0,
                "lineOutId": 0,
            }
        )

        # insert information of origin waypoint in the table
        self.wpWindow.insertHome(lat, lon)
        cont = 1
        for i in range(num // 2):
            g = self.geod.Direct(lat, lon, azimuth1, self.x * self.mpp)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))
            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx =self.posx +  math.trunc(self.x * math.sin(math.radians(azimuth1)))
            # newposy = self.posy + math.trunc(self.x * math.cos(math.radians(azimuth1)))

            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy

            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            # ----------------------------------
            g = self.geod.Direct(lat, lon, azimuth2, self.d)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx = self.posx + math.trunc(self.d*self.ppm * math.sin(math.radians(azimuth2)))
            # newposy = self.posy + math.trunc(self.d*self.ppm * math.cos(math.radians(azimuth2)))

            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy

            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            # -------------------------------------
            g = self.geod.Direct(lat, lon, (azimuth1 + 180) % 360, self.x * self.mpp)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx = self.posx + math.trunc(self.x * math.sin(math.radians((azimuth1 + 180)%360)))
            # newposy = self.posy + math.trunc(self.x * math.cos(math.radians((azimuth1 + 180)%360)))
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1
            # ----------------
            g = self.geod.Direct(lat, lon, azimuth2, self.d)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx = self.posx + math.trunc(self.d*self.ppm * math.sin(math.radians(azimuth2)))
            # newposy = self.posy + math.trunc(self.d *self.ppm * math.cos(math.radians(azimuth2)))
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

        g = self.geod.Direct(lat, lon, azimuth1, self.x * self.mpp)
        lat = float(g["lat2"])
        lon = float(g["lon2"])
        waypoints.append({"lat": lat, "lon": lon, "takePic": False})
        self.wpWindow.insertWP(lat, lon)
        newposx, newposy = self.converter.convertToCoords((lat, lon))

        # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
        # newposx = self.posx + math.trunc(self.x * math.sin(math.radians(azimuth1)))
        # newposy = self.posy + math.trunc(self.x * math.cos(math.radians(azimuth1)))
        lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
        self.posx = newposx
        self.posy = newposy
        ovalId = self.canvas.create_oval(
            self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill="blue"
        )
        textId = self.canvas.create_text(
            self.posx,
            self.posy,
            text=str(cont),
            font=("Courier", 10, "bold"),
            fill="white",
        )
        self.waypointsIds[-1]["lineOutId"] = lineId
        self.waypointsIds.append(
            {
                "wpId": str(cont),
                "textId": textId,
                "ovalId": ovalId,
                "lineInId": lineId,
                "lineOutId": 0,
            }
        )
        cont = cont + 1

        if num % 2 != 0:
            g = self.geod.Direct(lat, lon, azimuth2, self.d)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx = self.posx + math.trunc(self.d*self.ppm * math.sin(math.radians(azimuth2)))
            # newposy = self.posy + math.trunc(self.d*self.ppm * math.cos(math.radians(azimuth2)))
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1
            # ----------------------------------
            g = self.geod.Direct(lat, lon, (azimuth1 + 180) % 360, self.x * self.mpp)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx = self.posx + math.trunc(self.x * math.sin(math.radians((azimuth1 + 180) % 360)))
            # newposy = self.posy + math.trunc(self.x * math.cos(math.radians((azimuth1 + 180) % 360)))
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
        # insert return to launch in the table
        self.wpWindow.insertRTL()

        self.done = True
        # waypoints_json = json.dumps(waypoints)
        # self.client.publish("autopilotControllerCommand/executeFlightPlan", waypoints_json)

    def createScan2(self):

        azimuth1 = 180 - self.azimuth1
        azimuth2 = 180 - self.azimuth2
        self.posx = self.originposx
        self.posy = self.originposy
        num = math.ceil(self.y / (self.d * self.ppm))
        waypoints = []
        self.waypointToMoveIds = []
        lat = float(self.originlat)
        lon = float(self.originlon)
        ovalId = self.canvas.create_oval(
            self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill="blue"
        )
        textId = self.canvas.create_text(
            self.posx, self.posy, text="H", font=("Courier", 10, "bold"), fill="white"
        )
        self.waypointsIds.append(
            {
                "wpId": "H",
                "textId": textId,
                "ovalId": ovalId,
                "lineInId": 0,
                "lineOutId": 0,
            }
        )

        # insert information of origin waypoint in the table
        self.wpWindow.insertHome(lat, lon)
        cont = 1
        for i in range(num // 2):
            g = self.geod.Direct(lat, lon, azimuth1, self.x * self.mpp)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            newposx = self.posx + math.trunc(self.x * math.sin(math.radians(azimuth1)))
            newposy = self.posy + math.trunc(self.x * math.cos(math.radians(azimuth1)))

            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy

            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            # ----------------------------------
            g = self.geod.Direct(lat, lon, azimuth2, self.d)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            newposx = self.posx + math.trunc(
                self.d * self.ppm * math.sin(math.radians(azimuth2))
            )
            newposy = self.posy + math.trunc(
                self.d * self.ppm * math.cos(math.radians(azimuth2))
            )

            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy

            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            # -------------------------------------
            g = self.geod.Direct(lat, lon, (azimuth1 + 180) % 360, self.x * self.mpp)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            newposx = self.posx + math.trunc(
                self.x * math.sin(math.radians((azimuth1 + 180) % 360))
            )
            newposy = self.posy + math.trunc(
                self.x * math.cos(math.radians((azimuth1 + 180) % 360))
            )
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            g = self.geod.Direct(lat, lon, azimuth2, self.d)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            newposx = self.posx + math.trunc(
                self.d * self.ppm * math.sin(math.radians(azimuth2))
            )
            newposy = self.posy + math.trunc(
                self.d * self.ppm * math.cos(math.radians(azimuth2))
            )
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

        g = self.geod.Direct(lat, lon, azimuth1, self.x * self.mpp)
        lat = float(g["lat2"])
        lon = float(g["lon2"])
        waypoints.append({"lat": lat, "lon": lon, "takePic": False})
        self.wpWindow.insertWP(lat, lon)

        # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
        newposx = self.posx + math.trunc(self.x * math.sin(math.radians(azimuth1)))
        newposy = self.posy + math.trunc(self.x * math.cos(math.radians(azimuth1)))
        lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
        self.posx = newposx
        self.posy = newposy
        ovalId = self.canvas.create_oval(
            self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill="blue"
        )
        textId = self.canvas.create_text(
            self.posx,
            self.posy,
            text=str(cont),
            font=("Courier", 10, "bold"),
            fill="white",
        )
        self.waypointsIds[-1]["lineOutId"] = lineId
        self.waypointsIds.append(
            {
                "wpId": str(cont),
                "textId": textId,
                "ovalId": ovalId,
                "lineInId": lineId,
                "lineOutId": 0,
            }
        )
        cont = cont + 1

        if num % 2 != 0:
            g = self.geod.Direct(lat, lon, azimuth2, self.d)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            newposx = self.posx + math.trunc(
                self.d * self.ppm * math.sin(math.radians(azimuth2))
            )
            newposy = self.posy + math.trunc(
                self.d * self.ppm * math.cos(math.radians(azimuth2))
            )
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            g = self.geod.Direct(lat, lon, (azimuth1 + 180) % 360, self.x * self.mpp)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            newposx = self.posx + math.trunc(
                self.x * math.sin(math.radians((azimuth1 + 180) % 360))
            )
            newposy = self.posy + math.trunc(
                self.x * math.cos(math.radians((azimuth1 + 180) % 360))
            )
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )

        self.done = True
        # waypoints_json = json.dumps(waypoints)
        # self.client.publish("autopilotControllerCommand/executeFlightPlan", waypoints_json)

    def createSpiral(self):

        # azimuth = 180 - self.azimuth
        azimuth = self.azimuth
        self.posx = self.originx
        self.posy = self.originy
        num = math.ceil(self.x / (self.d * self.ppm))
        waypoints = []
        self.waypointToMoveIds = []
        lat = float(self.originlat)
        lon = float(self.originlon)
        ovalId = self.canvas.create_oval(
            self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill="blue"
        )
        textId = self.canvas.create_text(
            self.posx, self.posy, text="H", font=("Courier", 10, "bold"), fill="white"
        )
        self.waypointsIds.append(
            {
                "wpId": "H",
                "textId": textId,
                "ovalId": ovalId,
                "lineInId": 0,
                "lineOutId": 0,
            }
        )

        # insert information of origin waypoint in the table
        self.wpWindow.insertHome(lat, lon)
        # self.table.insert(parent='', index='end', iid=0, text='', values=('H', lat,lon))
        cont = 1
        for i in range(num):
            dist = (2 * i + 1) * self.d
            g = self.geod.Direct(lat, lon, azimuth, dist)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx =self.posx +  math.trunc(dist*self.ppm * math.sin(math.radians(azimuth)))
            # newposy = self.posy + math.trunc(dist*self.ppm * math.cos(math.radians(azimuth)))

            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy

            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            g = self.geod.Direct(lat, lon, azimuth + 90, dist)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx = self.posx + math.trunc(dist*self.ppm * math.sin(math.radians(azimuth+90)))
            # newposy = self.posy + math.trunc(dist*self.ppm * math.cos(math.radians(azimuth+90)))

            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy

            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            g = self.geod.Direct(lat, lon, azimuth + 180, dist + self.d)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx = self.posx + math.trunc((dist+self.d)*self.ppm * math.sin(math.radians(azimuth + 180)))
            # newposy = self.posy + math.trunc((dist+self.d)*self.ppm * math.cos(math.radians(azimuth + 180)))
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            g = self.geod.Direct(lat, lon, azimuth + 270, (dist + self.d))
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx = self.posx + math.trunc((dist+self.d)*self.ppm * math.sin(math.radians(azimuth + 270)))
            # newposy = self.posy + math.trunc((dist+self.d)*self.ppm * math.cos(math.radians(azimuth + 270)))
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1
        self.wpWindow.insertRTL()
        self.done = True
