import base64
import json

import tkinter as tk
import cv2 as cv
import numpy as np

import paho.mqtt.client as mqtt

from dashboardClasses.LEDsControllerClass import LEDsController
from dashboardClasses.CameraControllerClass import CameraController
from dashboardClasses.AutopilotControllerClass import AutopilotController
from dashboardClasses.ShowRecordedPositionsClass import RecordedPositionsWindow


class ConfigurationPanel:
    def buildFrame(self, fatherFrame, callback):
        self.callback = callback
        self.fatherFrame = fatherFrame
        self.ParameterFrame = tk.Frame(fatherFrame)
        self.ParameterFrame.rowconfigure(0, weight=4)
        self.ParameterFrame.rowconfigure(1, weight=1)

        self.ParameterFrame.columnconfigure(0, weight=1)
        self.ParameterFrame.columnconfigure(1, weight=1)
        self.ParameterFrame.columnconfigure(2, weight=1)
        self.ParameterFrame.columnconfigure(3, weight=1)
        self.ParameterFrame.columnconfigure(4, weight=1)
        self.ParameterFrame.columnconfigure(5, weight=1)

        self.operationModeFrame = tk.LabelFrame(
            self.ParameterFrame, text="Operation mode"
        )
        self.operationModeFrame.grid(row=0, column=0, padx=10, pady=10, sticky="nesw")
        self.var1 = tk.StringVar()
        self.var1.set("simulation")
        tk.Radiobutton(
            self.operationModeFrame,
            text="simulation",
            variable=self.var1,
            value="simulation",
            command=self.operationModeChanged,
        ).grid(row=0, sticky="W")

        tk.Radiobutton(
            self.operationModeFrame,
            text="production",
            variable=self.var1,
            value="production",
            command=self.operationModeChanged,
        ).grid(row=1, sticky="W")

        self.communicationModeFrame = tk.LabelFrame(
            self.ParameterFrame, text="Communication mode"
        )
        self.communicationModeFrame.grid(
            row=0, column=1, padx=10, pady=10, sticky="nesw"
        )
        self.var2 = tk.StringVar()
        self.var2.set("global")
        tk.Radiobutton(
            self.communicationModeFrame,
            text="local",
            variable=self.var2,
            value="local",
            command=self.communicationModeChanged,
        ).grid(row=0, sticky="W")

        tk.Radiobutton(
            self.communicationModeFrame,
            text="global",
            variable=self.var2,
            value="global",
            command=self.communicationModeChanged,
        ).grid(row=1, sticky="W")

        self.externalBrokerFrame = tk.LabelFrame(
            self.ParameterFrame, text="External broker"
        )
        self.externalBrokerFrame.grid(row=0, column=2, padx=10, pady=10, sticky="nesw")
        self.var3 = tk.StringVar()
        self.var3.set("localhost")
        self.externalBrokerOption1 = tk.Radiobutton(
            self.externalBrokerFrame,
            text="localhost",
            variable=self.var3,
            value="localhost",
            command=self.credentialsToggle,
        )
        self.externalBrokerOption1.grid(row=0, sticky="W")

        self.externalBrokerOption2 = tk.Radiobutton(
            self.externalBrokerFrame,
            text="broker.hivemq.com",
            variable=self.var3,
            value="broker.hivemq.com",
            command=self.credentialsToggle,
        )
        self.externalBrokerOption2.grid(row=1, sticky="W")

        self.externalBrokerOption3 = tk.Radiobutton(
            self.externalBrokerFrame,
            text="classpip.upc.edu",
            variable=self.var3,
            value="classpip.upc.edu",
            command=self.credentialsToggle,
        )
        self.externalBrokerOption3.grid(row=2, sticky="W")

        self.credentialsFrame = tk.LabelFrame(
            self.externalBrokerFrame, text="Credentials"
        )

        self.usernameLbl = tk.Label(self.credentialsFrame, text="username")
        self.usernameLbl.grid(row=0, column=0)
        self.usernameBox = tk.Entry(self.credentialsFrame)
        self.usernameBox.grid(row=0, column=1)
        self.passLbl = tk.Label(self.credentialsFrame, text="pass")
        self.passLbl.grid(row=1, column=0)
        self.passBox = tk.Entry(self.credentialsFrame)
        self.passBox.grid(row=1, column=1)

        self.monitorFrame = tk.LabelFrame(self.ParameterFrame, text="Monitor")
        self.monitorFrame.grid(row=0, column=3, padx=10, pady=10, sticky="nesw")
        self.monitorOptions = [
            "Autopilot service in external broker",
            "Camera service in external broker",
            "Dashboard in external broker",
        ]
        self.monitorOptionsSelected = []
        self.monitorCheckBox = []

        for option in self.monitorOptions:
            self.monitorOptionsSelected.append(tk.Variable(value=0))
            self.monitorCheckBox.append(
                tk.Checkbutton(
                    self.monitorFrame,
                    text=option,
                    variable=self.monitorOptionsSelected[-1],
                ).pack(anchor=tk.W)
            )

        self.dataServiceFrame = tk.LabelFrame(self.ParameterFrame, text="Data service")
        self.dataServiceFrame.grid(row=0, column=4, padx=10, pady=10, sticky="nesw")
        self.dataServiceOptions = ["Record positions"]
        self.dataServiceOptionsSelected = []
        self.dataServiceCheckBox = []

        for option in self.dataServiceOptions:
            self.dataServiceOptionsSelected.append(tk.Variable(value=0))
            checkOption = tk.Checkbutton(
                self.dataServiceFrame,
                text=option,
                variable=self.dataServiceOptionsSelected[-1],
            )
            checkOption.pack(anchor=tk.W)
            self.dataServiceCheckBox.append(checkOption)

        self.swarmModeFrame = tk.LabelFrame(self.ParameterFrame, text="(EXP) Swarm mode")
        self.swarmModeFrame.grid(row=0, column=5, padx=10, pady=10, sticky="nesw")
        self.swarmModeState = tk.Variable(value=0)
        self.swarmModeButton = tk.Checkbutton(self.swarmModeFrame, text="Swarm mode",
                                              command=self.swarmModeButtonClicked,
                                              variable=self.swarmModeState)
        self.swarmModeButton.pack()

        optionList = ("2", "3", "4", "5", "6")
        self.swarmModeNumber = tk.StringVar(value="2")
        self.swarmModeOptionMenu = tk.OptionMenu(self.swarmModeFrame,
                                                 self.swarmModeNumber,
                                                 *optionList)

        self.closeButton = tk.Button(
            self.ParameterFrame,
            text="Configure the Drone Engineering Ecosystem",
            bg="red",
            fg="white",
            command=self.closeButtonClicked,
        )

        self.closeButton.grid(
            row=2, column=0, columnspan=6, padx=10, pady=10, sticky="nesw"
        )

        return self.ParameterFrame

    def credentialsToggle(self):
        if self.var3.get() == "classpip.upc.edu":
            self.credentialsFrame.grid(row=3, sticky="W")
        else:
            self.credentialsFrame.grid_forget()

    def communicationModeChanged(self):
        if self.var2.get() == "local":
            for checkBox in self.dataServiceCheckBox:
                checkBox.pack_forget()
        else:
            for checkBox in self.dataServiceCheckBox:
                checkBox.pack()

        if self.var1.get() == "simulation" and self.var2.get() == "global":
            self.externalBrokerOption1.grid(row=0, sticky="W")
            self.externalBrokerOption2.grid(row=1, sticky="W")
            self.externalBrokerOption3.grid(row=2, sticky="W")
            if self.var3.get() == "classpip.upc.edu":
                self.credentialsFrame.grid(row=3, sticky="W")
        else:
            self.externalBrokerOption1.grid_forget()
            self.externalBrokerOption2.grid_forget()
            self.externalBrokerOption3.grid_forget()
            if self.var3.get() == "classpip.upc.edu":
                self.credentialsFrame.grid_forget()

    def operationModeChanged(self):
        if self.var1.get() == "simulation" and self.var2.get() == "global":
            self.externalBrokerOption1.grid(row=0, sticky="W")
            self.externalBrokerOption2.grid(row=1, sticky="W")
            self.externalBrokerOption3.grid(row=2, sticky="W")
            if self.var3.get() == "classpip.upc.edu":
                self.credentialsFrame.grid(row=3, sticky="W")
        else:
            self.externalBrokerOption1.grid_forget()
            self.externalBrokerOption2.grid_forget()
            self.externalBrokerOption3.grid_forget()
            if self.var3.get() == "classpip.upc.edu":
                self.credentialsFrame.grid_forget()

    def swarmModeButtonClicked(self):
        _buttonClicked = int(self.swarmModeState.get())
        if _buttonClicked == 1:
            self.swarmModeOptionMenu.pack()
        elif _buttonClicked == 0:
            self.swarmModeOptionMenu.pack_forget()

    def closeButtonClicked(self):
        myAutopilotController.setSwarmMode((int(self.swarmModeState.get()), int(self.swarmModeNumber.get())))

        monitorOptions = []
        for i in range(0, len(self.monitorCheckBox)):
            if self.monitorOptionsSelected[i].get() == "1":
                monitorOptions.append(self.monitorOptions[i])

        dataServiceOptions = []
        for i in range(0, len(self.dataServiceCheckBox)):
            if self.dataServiceOptionsSelected[i].get() == "1":
                dataServiceOptions.append(self.dataServiceOptions[i])

        parameters = {
            "operationMode": self.var1.get(),
            "communicationMode": self.var2.get(),
            "externalBroker": self.var3.get(),
            "monitorOptions": monitorOptions,
            "dataServiceOptions": dataServiceOptions,
        }
        if self.var3.get() == "classpip.upc.edu":
            parameters["username"] = self.usernameBox.get()
            parameters["pass"] = self.passBox.get()

        self.callback(parameters)
        self.fatherFrame.destroy()


# treatment of messages received from global broker
def on_message(client, userdata, message):
    global myAutopilotController
    global myCameraController
    global panel
    global lbl
    global table
    global originlat, originlon
    global new_window

    splited = message.topic.split("/")
    origin = splited[0]
    destination = splited[1]
    command = splited[2]

    if origin == "cameraService":
        if command == "videoFrame":
            img = base64.b64decode(message.payload)
            # converting into numpy array from buffer
            npimg = np.frombuffer(img, dtype=np.uint8)
            # Decode to Original Frame
            img = cv.imdecode(npimg, 1)
            # show stream in a separate opencv window
            img = cv.resize(img, (640, 480))
            cv.imshow("Stream", img)
            cv.waitKey(1)

        if command == "picture":
            print("recibo picture")
            img = base64.b64decode(message.payload)
            myCameraController.putPicture(img)

    if origin == "autopilotService":

        if command == "telemetryInfo":
            # telemetry_info contains the state of the autopilot.
            # this is enough for the autopilot controller to decide what to do next
            telemetry_info = json.loads(message.payload)
            myAutopilotController.showTelemetryInfo(telemetry_info)

    if origin == "dataService" and command == "storedPositions":
        # receive the positions stored by the data service
        data = message.payload.decode("utf-8")
        # converts received string to json
        data_json = json.loads(data)
        myRecordedPositionsWindow.putStoredPositions(data_json)


def configure(configuration_parameters):
    global panelFrame
    global client

    if configuration_parameters["communicationMode"] == "global":
        external_broker_address = configuration_parameters["externalBroker"]
    else:
        external_broker_address = "localhost"

    # the external broker must run always in port 8000
    external_broker_port = 8000

    client = mqtt.Client("Dashboard", transport="websockets")
    client.on_message = on_message
    if external_broker_address == "classpip.upc.edu":
        client.username_pw_set(
            configuration_parameters["username"], configuration_parameters["pass"]
        )

    client.connect(external_broker_address, external_broker_port)
    client.loop_start()
    client.subscribe("+/dashBoard/#")

    if configuration_parameters["monitorOptions"]:
        monitorOptions = json.dumps(configuration_parameters["monitorOptions"])
        client.publish("dashBoard/monitor/setOptions", monitorOptions)

    if configuration_parameters["dataServiceOptions"]:
        dataServiceOptions = json.dumps(configuration_parameters["dataServiceOptions"])
        print("envio al data service ", dataServiceOptions)
        client.publish("dashBoard/dataService/setOptions", dataServiceOptions)

    myCameraController.putClient(client)
    myAutopilotController.putClient(client)
    myRecordedPositionsWindow.putClient(client)
    # this is to maximize the main window
    master.deiconify()


############################################################################
############################################################################

master = tk.Tk()
new_window = tk.Toplevel(master)
new_window.title("Configuration panel")
new_window.geometry("900x300")
confPanel = ConfigurationPanel()
confPanelFrame = confPanel.buildFrame(new_window, configure)
confPanelFrame.pack()


master.title("Main window")
master.geometry("1150x600")
master.rowconfigure(0, weight=1)
master.rowconfigure(1, weight=15)
client = None
# this is to minimize the master window so that the configuration window can be seen
master.iconify()


def close_button_clicked():
    master.destroy()


closeButton = tk.Button(
    master,
    text="Close",
    width=160,
    height=1,
    bg="red",
    fg="white",
    command=close_button_clicked,
)
closeButton.grid(row=0, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


# panel frame -------------------------------------------
panelFrame = tk.Frame(master)
panelFrame.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
panelFrame.columnconfigure(0, weight=1)
panelFrame.columnconfigure(1, weight=1)
panelFrame.columnconfigure(2, weight=1)
panelFrame.columnconfigure(3, weight=3)
panelFrame.rowconfigure(0, weight=4)
panelFrame.rowconfigure(1, weight=1)

# Autopilot control frame ----------------------
myAutopilotController = AutopilotController()
autopilotControlFrame = myAutopilotController.buildFrame(panelFrame)
autopilotControlFrame.grid(
    row=0, column=0, columnspan=3, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
)


# Camera control  frame ----------------------
myCameraController = CameraController()
cameraControlFrame = myCameraController.buildFrame(panelFrame)
cameraControlFrame.grid(
    row=0, column=3, rowspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
)

# LEDs control frame ----------------------
ledsControlFrame = LEDsController().buildFrame(panelFrame, client)
ledsControlFrame.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


# Monitor control frame ----------------------
monitorControlFrame = tk.LabelFrame(panelFrame, text="Monitor control")
monitorControlFrame.grid(
    row=1, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
)


def monitor_toggle():
    global client
    if monitorControlButton["text"] == "Start monitor":
        monitorControlButton["text"] = "Stop monitor"
        client.publish("dashBoard/monitor/start")
    else:
        monitorControlButton["text"] = "Start monitor"
        client.publish("dashBoard/monitor/stop")


monitorControlButton = tk.Button(
    monitorControlFrame,
    text="Start monitor",
    bg="red",
    fg="white",
    height=3,
    width=20,
    command=monitor_toggle,
)
monitorControlButton.pack(pady=5)

# Data management ----------------------
myRecordedPositionsWindow = RecordedPositionsWindow(master)

dataManagementFrame = tk.LabelFrame(panelFrame, text="Data management")
dataManagementFrame.grid(
    row=1, column=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
)
showRecordedPositionsButton = tk.Button(
    dataManagementFrame,
    text="Show recorded positions",
    bg="red",
    fg="white",
    height=3,
    width=20,
    command=myRecordedPositionsWindow.openWindowToShowRecordedPositions,
)
showRecordedPositionsButton.pack(pady=5)

master.mainloop()
