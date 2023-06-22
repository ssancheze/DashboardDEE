import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from pyppeteer import launch
import os
import math
from dashboardClasses.FlightPlanDesignerClass import FlightPlanDesignerWindow
from dashboardClasses.ControlFrameClass import ControlFrame

from dashboardClasses.TelemetryInfoFrameClass import TelemetryInfoFrame


class AutopilotController:
    def __init__(self, operation_drones):
        self.operation_drones = operation_drones

    def buildFrame(self, frame):

        self.swarmNumber = [0]
        self.swarmAll = [0]
        self.frame = frame
        self.flightPlanDesignerWindow = None
        self.autopilotControlFrame = tk.LabelFrame(
            frame, text="Flight control", padx=5, pady=5
        )
        self.autopilotControlFrame.rowconfigure(0, weight=1)
        self.autopilotControlFrame.rowconfigure(1, weight=5)
        self.autopilotControlFrame.rowconfigure(2, weight=1)
        self.autopilotControlFrame.rowconfigure(3, weight=1)
        self.autopilotControlFrame.columnconfigure(0, weight=1)
        self.autopilotControlFrame.columnconfigure(1, weight=1)

        self.connectButton = tk.Button(
            self.autopilotControlFrame,
            text="Connect",
            bg="red",
            fg="white",
            command=self.connect_button_clicked,
        )
        self.connectButton.grid(
            row=0,
            column=0,
            columnspan=2,
            padx=5,
            pady=5,
            sticky=tk.N + tk.S + tk.E + tk.W,
        )

        # Telemetry info ----------------------
        self.myTelemetryInfoFrameClass = [TelemetryInfoFrame(0), ]
        self.telemetryInfoFrame = [self.myTelemetryInfoFrameClass[0].buildFrame(self.autopilotControlFrame)]
        self.telemetryInfoFrame[0].grid(
                row=1, column=0, padx=20, sticky=tk.N + tk.S + tk.E + tk.W
            )
        self.telemetryInfoFrame[0].tkraise()
        self.raisedFrame = 0
        # Control ----------------------
        self.myControlFrameClass = ControlFrame(self.operation_drones)
        self.myControlFrame = self.myControlFrameClass.buldFrame(
            self.autopilotControlFrame
        )
        self.myControlFrame.grid(
            row=1, column=1, padx=20, sticky=tk.N + tk.S + tk.E + tk.W
        )

        # Mission planner frame ----------------------
        self.missionPlannerFrame = tk.LabelFrame(
            self.autopilotControlFrame, text="Mission planner"
        )
        self.missionPlannerFrame.grid(
            row=2,
            column=0,
            columnspan=2,
            padx=5,
            pady=5,
            sticky=tk.N + tk.S + tk.E + tk.W,
        )

        missionPlannerButton = tk.Button(
            self.missionPlannerFrame,
            text="Start mission planner",
            bg="red",
            fg="white",
            height=3,
            width=80,
            command=self.openSelectionWindow,
        )
        missionPlannerButton.pack()

        self.ppm = 2.78
        self.connected = False

        # Swarm control frame ----------------------
        self.swarmControlFrame = tk.LabelFrame(
            self.autopilotControlFrame, text="Swarm control"
        )
        self.swarmControlFrame.grid(
            row=3,
            column=0,
            columnspan=2,
            padx=5,
            pady=5,
            sticky=tk.N + tk.S + tk.E + tk.W,
        )

        self.swarmControlFrame.rowconfigure(0, weight=1)
        self.swarmControlFrame.columnconfigure(0, weight=1)
        self.swarmControlFrame.columnconfigure(0, weight=1)
        self.swarmControlFrame.columnconfigure(1, weight=1)
        self.swarmControlFrame.columnconfigure(2, weight=1)
        self.swarmControlFrame.columnconfigure(3, weight=1)
        self.swarmControlFrame.columnconfigure(4, weight=1)
        self.swarmControlFrame.columnconfigure(5, weight=1)

        self.drone1Var = tk.BooleanVar(value=False)
        drone1CheckButton = tk.Checkbutton(
            master=self.swarmControlFrame,
            text="#1",
            variable=self.drone1Var,
            state=tk.DISABLED,
            command=self.swarmControlCheckButtonChanged
        )
        drone1CheckButton.grid(row=0, column=0, pady=5)

        self.drone2Var = tk.BooleanVar(value=False)
        drone2CheckButton = tk.Checkbutton(
            master=self.swarmControlFrame,
            text="#2",
            variable=self.drone2Var,
            state=tk.DISABLED,
            command=self.swarmControlCheckButtonChanged
        )
        drone2CheckButton.grid(row=0, column=1, pady=5)

        self.drone3Var = tk.BooleanVar(value=False)
        drone3CheckButton = tk.Checkbutton(
            master=self.swarmControlFrame,
            text="#3",
            variable=self.drone3Var,
            state=tk.DISABLED,
            command=self.swarmControlCheckButtonChanged
        )
        drone3CheckButton.grid(row=0, column=2, pady=5)

        self.drone4Var = tk.BooleanVar(value=False)
        drone4CheckButton = tk.Checkbutton(
            master=self.swarmControlFrame,
            text="#4",
            variable=self.drone4Var,
            state=tk.DISABLED,
            command=self.swarmControlCheckButtonChanged
        )
        drone4CheckButton.grid(row=0, column=3, pady=5)

        self.drone5Var = tk.BooleanVar(value=False)
        drone5CheckButton = tk.Checkbutton(
            master=self.swarmControlFrame,
            text="#5",
            variable=self.drone5Var,
            state=tk.DISABLED,
            command=self.swarmControlCheckButtonChanged
        )
        drone5CheckButton.grid(row=0, column=4, pady=5)

        self.drone6Var = tk.BooleanVar(value=False)
        drone6CheckButton = tk.Checkbutton(
            master=self.swarmControlFrame,
            text="#6",
            variable=self.drone6Var,
            state=tk.DISABLED,
            command=self.swarmControlCheckButtonChanged
        )
        drone6CheckButton.grid(row=0, column=5, pady=5)

        self.swarmModeButtonsList = [
            drone1CheckButton,
            drone2CheckButton,
            drone3CheckButton,
            drone4CheckButton,
            drone5CheckButton,
            drone6CheckButton,
        ]

        return self.autopilotControlFrame

    def connect_button_clicked(self):
        if self.connectButton["text"] == "Connect":
            for drone_id in self.swarmAll:
                self.client.publish("dashBoard/autopilotService/"+str(drone_id)+"/connect")
                self.operation_drones.set_connected(drone_id, True)

            self.connectButton["text"] = "Connecting ..."
            self.connectButton["bg"] = "orange"

        else:
            if self.operation_drones.on_air < 0 and self.operation_drones.armed < 0:
                for drone_id in self.swarmAll:
                    drone = self.operation_drones.drones[drone_id]
                    if drone.on_air or drone.armed:
                        return
                    else:
                        self.client.publish("dashBoard/autopilotService/"+str(drone_id)+"/disconnect")
                        drone.telemetry_info['state'] = 'disconnected'
                        self.operation_drones.set_connected(drone_id, False)

                if self.operation_drones.connected < 0:
                    self.connected = False
                    self.connectButton["text"] = "Connect"
                    self.connectButton["bg"] = "red"
            else:
                messagebox.showwarning(
                    "Warning", "No puedes desconectar. Estás volando"
                )

    def putClient(self, client):
        self.client = client
        self.myControlFrameClass.putClient(self.client)

    def operation_drones_max_drones_defined(self):
        if len(self.operation_drones.drones) > 1:
            for drone_id in range(1, self.operation_drones.max_drones):
                telemetry_frame_class = TelemetryInfoFrame(drone_id)
                self.myTelemetryInfoFrameClass.append(telemetry_frame_class)
                telemetry_frame = telemetry_frame_class.buildFrame(self.autopilotControlFrame)
                telemetry_frame.grid(row=1, column=0, padx=20, sticky=tk.N + tk.S + tk.E + tk.W)
                self.telemetryInfoFrame.append(telemetry_frame)

    def raiseTelemetryFrame(self, _id):
        self.telemetryInfoFrame[_id].tkraise()
        self.raisedFrame = _id

    def showTelemetryInfo(self, telemetry_info, drone_id):
        if self.raisedFrame == drone_id:
            self.myTelemetryInfoFrameClass[drone_id].showTelemetryInfo(telemetry_info)
        if self.flightPlanDesignerWindow is not None:
            self.flightPlanDesignerWindow.showTelemetryInfo(telemetry_info)

        if telemetry_info["state"] == "connected" and self.operation_drones.connected == 1:
            self.connected = True
            self.connectButton["text"] = "Disconnect"
            self.connectButton["bg"] = "green"
            originlat = telemetry_info["lat"]
            originlon = telemetry_info["lon"]
            self.originPosition = (originlat, originlon)

    """
    def setDisconnected(self):
        self.connected = False
        self.connectButton["text"] = "Connect"
        self.connectButton["bg"] = "red"
        self.myControlFrameClass.setDisconnected()

    def setArmed (self):
        if self.flightPlanDesignerWindow != None:
            self.flightPlanDesignerWindow.setArmed()
        self.myControlFrameClass.setArmed()
    def setArming (self):
        if self.flightPlanDesignerWindow != None:
            self.flightPlanDesignerWindow.setArming()
        self.myControlFrameClass.setArming()

    def setFlying (self):
        if self.flightPlanDesignerWindow != None:
            self.flightPlanDesignerWindow.setFlying()
        self.myControlFrameClass.setFlying()

    def setLanding(self):
        if self.flightPlanDesignerWindow != None:
            self.flightPlanDesignerWindow.setLanding()
        #self.myControlFrameClass.setAtHome()

    def setAtHome(self):
        if self.flightPlanDesignerWindow != None:
            self.flightPlanDesignerWindow.setAtHome()
        self.myControlFrameClass.setAtHome()

    def setDisarmed (self):
        if self.flightPlanDesignerWindow != None:
            self.flightPlanDesignerWindow.setDisarmed()
        self.myControlFrameClass.setDisarmed()
    """

    def openSelectionWindow(self):
        if self.connected:

            self.newWindow = tk.Toplevel(self.frame)
            self.newWindow.title("Selection window")
            self.newWindow.geometry("1000x500")
            self.label = tk.Label(
                self.newWindow,
                text="Select the method to build the flight plan",
                width=50,
                font=("Colibri", 25),
            )
            self.label.grid(column=0, row=0, columnspan=4, pady=30)

            canvas1 = tk.Canvas(self.newWindow, width=200, height=200)
            canvas1.grid(row=2, column=0, padx=40, sticky="W")
            self.photoPoints = ImageTk.PhotoImage(
                Image.open("assets/points.png").resize((200, 200))
            )
            canvas1.create_image(0, 0, image=self.photoPoints, anchor="nw")
            pointsButton = tk.Button(
                self.newWindow,
                text="Fix waypoints by hand",
                bg="#375E97",
                fg="white",
                width=25,
                command=self.selectPoints,
            )
            pointsButton.grid(row=3, column=0, padx=50, sticky="W")

            canvas2 = tk.Canvas(self.newWindow, width=200, height=200)
            canvas2.grid(row=2, column=1, sticky="W")
            self.photoScan = ImageTk.PhotoImage(
                Image.open("assets/parallelogram.png").resize((200, 200))
            )
            canvas2.create_image(0, 0, image=self.photoScan, anchor="nw")
            scanButton = tk.Button(
                self.newWindow,
                text="Scan a parallelogram",
                bg="#FB6542",
                fg="black",
                width=25,
                command=self.selectScan,
            )
            scanButton.grid(row=3, column=1, padx=10, sticky="W")

            canvas3 = tk.Canvas(self.newWindow, width=200, height=200)
            canvas3.grid(row=2, column=2, sticky="W")
            self.photoSpiral = ImageTk.PhotoImage(
                Image.open("assets/spiral.png").resize((200, 200))
            )
            canvas3.create_image(0, 0, image=self.photoSpiral, anchor="nw")
            spiral = tk.Button(
                self.newWindow,
                text="Scan in spiral",
                bg="#FFBB00",
                fg="white",
                width=25,
                command=self.selectSpiral,
            )
            spiral.grid(row=3, column=2, padx=10, sticky="W")

            canvas4 = tk.Canvas(self.newWindow, width=200, height=200)
            canvas4.grid(row=2, column=3, sticky="W")
            self.photoLoad = ImageTk.PhotoImage(
                Image.open("assets/load.png").resize((200, 200))
            )
            canvas4.create_image(0, 0, image=self.photoLoad, anchor="nw")
            load = tk.Button(
                self.newWindow,
                text="Load flight plan",
                bg="#3F681C",
                fg="white",
                width=25,
                command=self.loadFlightPlan,
            )
            load.grid(row=3, column=3, padx=10, sticky="W")

            close = tk.Button(
                self.newWindow,
                text="close",
                bg="#B7BBB6",
                fg="white",
                width=100,
                command=self.close,
            )
            close.grid(row=4, column=0, columnspan=4, pady=30)
        else:
            messagebox.showwarning("Warning", "Debes conectarte antes")

    def selectPoints(self):
        self.flightPlanDesignerWindow = FlightPlanDesignerWindow(
            self.frame, 1, self.client, self.originPosition
        )
        self.flightPlanDesignerWindow.openWindowToCreateFlightPlan()
        self.newWindow.destroy()

    def selectScan(self):
        self.flightPlanDesignerWindow = FlightPlanDesignerWindow(
            self.frame, 2, self.client, self.originPosition
        )
        self.flightPlanDesignerWindow.openWindowToCreateFlightPlan()
        self.newWindow.destroy()

    def selectSpiral(self):
        self.flightPlanDesignerWindow = FlightPlanDesignerWindow(
            self.frame, 3, self.client, self.originPosition
        )
        self.flightPlanDesignerWindow.openWindowToCreateFlightPlan()
        self.newWindow.destroy()

    def loadFlightPlan(self):
        self.flightPlanDesignerWindow = FlightPlanDesignerWindow(
            self.frame, 0, self.client, self.originPosition
        )
        self.flightPlanDesignerWindow.openWindowToCreateFlightPlan()
        self.newWindow.destroy()

    def setSwarmMode(self, swarmMode):
        if swarmMode[0] == 1:
            self.swarmAll = range(swarmMode[1])
            for nn in self.swarmAll:
                self.swarmModeButtonsList[nn]["state"] = tk.NORMAL
        else:
            self.swarmAll = [0]

    def swarmControlCheckButtonChanged(self):
        self.swarmModeDronesList = [
            self.drone1Var.get(),
            self.drone2Var.get(),
            self.drone3Var.get(),
            self.drone4Var.get(),
            self.drone5Var.get(),
            self.drone6Var.get(),
        ]
        self.swarmNumber = [index for index, value in enumerate(self.swarmModeDronesList) if value]
        self.myControlFrameClass.setSwarmDroneNumber(self.swarmNumber)

    def close(self):
        self.newWindow.destroy()
