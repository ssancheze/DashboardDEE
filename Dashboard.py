import atexit
import base64
import json

import tkinter as tk
from PIL import Image, ImageTk
import cv2 as cv
import numpy as np

import paho.mqtt.client as mqtt

from dashboardClasses.LEDsControllerClass import LEDsController
from dashboardClasses.AutopilotControllerClass import AutopilotController
from dashboardClasses.ShowRecordedPositionsClass import RecordedPositionsWindow
from dashboardClasses.FrameSelectorClass import FrameSelector
from dashboardClasses.ConnectionManagerClass import ConnectionManager, PROTECTED_BROKERS
from dashboardClasses.DroneClass import OperationDrones
import dashboardClasses.NewAutopilotService as NewAutopilotService

_ABSOLUTE_DIR_PATH = __file__[:-12]


class ConfigurationPanel:
    def buildFrame(self, fatherFrame, callback):
        self.callback = callback
        self.fatherFrame = fatherFrame
        self.ParameterFrame = tk.Frame(fatherFrame)
        self.ParameterFrame.rowconfigure(0, weight=4)
        self.ParameterFrame.rowconfigure(1, weight=1)
        self.ParameterFrame.rowconfigure(2, weight=1)

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

        tk.Radiobutton(
            self.communicationModeFrame,
            text="direct",
            variable=self.var2,
            value="direct",
            command=self.communicationModeChanged,
        ).grid(row=2, sticky="W")

        self.localModeFrame = tk.LabelFrame(
            self.communicationModeFrame,
            text="Local mode"
        )

        self.localModeVar = tk.IntVar(value=0)

        tk.Radiobutton(
            self.localModeFrame,
            text='Onboard broker',
            variable=self.localModeVar,
            value=0,
            command=self.communicationModeChanged
        ).pack()
        tk.Radiobutton(
            self.localModeFrame,
            text='Single broker',
            variable=self.localModeVar,
            value=1,
            command=self.communicationModeChanged
        ).pack()

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

        self.externalBrokerLocal0Frame = tk.LabelFrame(
            self.ParameterFrame,
            text='External broker'
        )

        self.externalBrokerLocal0Entries = (
            tk.Entry(self.externalBrokerLocal0Frame),
            tk.Entry(self.externalBrokerLocal0Frame),
            tk.Entry(self.externalBrokerLocal0Frame),
            tk.Entry(self.externalBrokerLocal0Frame),
            tk.Entry(self.externalBrokerLocal0Frame),
            tk.Entry(self.externalBrokerLocal0Frame)
        )

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

        self.swarmModeFrame = tk.LabelFrame(
            self.ParameterFrame, text="(EXP) Swarm mode"
        )
        self.swarmModeFrame.grid(row=0, column=5, padx=10, pady=10, sticky="nesw")
        self.swarmModeState = tk.Variable(value=0)
        self.swarmModeButton = tk.Checkbutton(
            self.swarmModeFrame,
            text="Swarm mode",
            command=self.swarmModeButtonClicked,
            variable=self.swarmModeState,
        )
        self.swarmModeButton.pack()

        self.rcChecksVar = tk.BooleanVar(value=True)
        self.rcChecksButton = tk.Checkbutton(
            self.swarmModeFrame,
            text='RC checks',
            variable=self.rcChecksVar
        )
        self.rcChecksButton.pack()

        optionList = ("2", "3", "4", "5", "6")
        self.swarmModeNumber = tk.StringVar(value="2")
        self.swarmModeOptionMenu = tk.OptionMenu(
            self.swarmModeFrame, self.swarmModeNumber, *optionList
        )

        self.closeButton = tk.Button(
            self.ParameterFrame,
            text="Configure the Drone Engineering Ecosystem",
            bg="red",
            fg="white",
            command=self.closeButtonClicked,
        )

        self.closeButton.grid(
            row=1, column=0, columnspan=6, padx=10, pady=10, sticky="nesw"
        )

        self.global_png = ImageTk.PhotoImage(Image.open(f"{_ABSOLUTE_DIR_PATH}assets\\global_scheme.png")
                                             .resize((640, 360)))
        self.local0_png = ImageTk.PhotoImage(Image.open(f"{_ABSOLUTE_DIR_PATH}assets\\local0_scheme.png")
                                             .resize((640, 360)))
        self.local1_png = ImageTk.PhotoImage(Image.open(f"{_ABSOLUTE_DIR_PATH}assets\\local1_scheme.png")
                                             .resize((640, 360)))
        self.direct_png = ImageTk.PhotoImage(Image.open(f"{_ABSOLUTE_DIR_PATH}assets\\direct_scheme.png")
                                             .resize((640, 360)))

        self.commsModeImageContainer = tk.Label(self.ParameterFrame, image=self.local0_png, height=360, width=640)

        return self.ParameterFrame

    def credentialsToggle(self):
        if self.var3.get() in PROTECTED_BROKERS:
            self.credentialsFrame.grid(row=3, sticky="W")
        else:
            self.credentialsFrame.grid_forget()

    def communicationModeChanged(self):
        if self.var2.get() == "local":
            self.localModeFrame.grid(row=3, sticky="W")

            if int(self.swarmModeState.get()) == 1:
                activeDrones = int(self.swarmModeNumber.get())
            else:
                activeDrones = 1
            for drone in range(activeDrones):
                self.externalBrokerLocal0Entries[drone].pack()
            self.externalBrokerFrame.grid_forget()
            self.externalBrokerLocal0Frame.grid(row=0, column=2, padx=5, pady=5, sticky="nesw")

            for checkBox in self.dataServiceCheckBox:
                checkBox.pack_forget()
        else:
            for drone in self.externalBrokerLocal0Entries:
                drone.pack_forget()
            self.externalBrokerFrame.grid(row=0, column=2, padx=10, pady=10, sticky="nesw")
            self.externalBrokerLocal0Frame.grid_forget()

            self.localModeFrame.grid_forget()
            for checkBox in self.dataServiceCheckBox:
                checkBox.pack()

        if self.var2.get() == "global":
            self.externalBrokerOption1.grid(row=0, sticky="W")
            self.externalBrokerOption2.grid(row=1, sticky="W")
            self.externalBrokerOption3.grid(row=2, sticky="W")
            if self.var3.get() in PROTECTED_BROKERS:
                self.credentialsFrame.grid(row=3, sticky="W")
        else:
            self.externalBrokerOption1.grid_forget()
            self.externalBrokerOption2.grid_forget()
            self.externalBrokerOption3.grid_forget()
            if self.var3.get() in PROTECTED_BROKERS:
                self.credentialsFrame.grid_forget()

        if self.var1.get() == 'simulation':
            self.commsModeImageContainer.grid_forget()
        else:
            if self.var2.get() == 'global':
                self.commsModeImageContainer.configure(image=self.global_png)
            elif self.var2.get() == 'local':
                if self.localModeVar.get() == 0:
                    self.commsModeImageContainer.configure(image=self.local0_png)
                elif self.localModeVar.get() == 1:
                    self.commsModeImageContainer.configure(image=self.local1_png)
            elif self.var2.get() == 'direct':
                self.commsModeImageContainer.configure(image=self.direct_png)
            self.commsModeImageContainer.grid(row=2, columnspan=6, padx=10, pady=10)

    def operationModeChanged(self):
        if self.var2.get() == "global":
            self.externalBrokerOption1.grid(row=0, sticky="W")
            self.externalBrokerOption2.grid(row=1, sticky="W")
            self.externalBrokerOption3.grid(row=2, sticky="W")
            if self.var3.get() in PROTECTED_BROKERS:
                self.credentialsFrame.grid(row=3, sticky="W")
        else:
            self.externalBrokerOption1.grid_forget()
            self.externalBrokerOption2.grid_forget()
            self.externalBrokerOption3.grid_forget()
            if self.var3.get() in PROTECTED_BROKERS:
                self.credentialsFrame.grid_forget()

    def swarmModeButtonClicked(self):
        _buttonClicked = int(self.swarmModeState.get())
        if _buttonClicked == 1:
            self.swarmModeOptionMenu.pack()
        elif _buttonClicked == 0:
            self.swarmModeOptionMenu.pack_forget()

    def closeButtonClicked(self):
        global max_drones
        global swarmModeActive
        max_drones = 1
        swarmModeActive = self.swarmModeState.get()
        if swarmModeActive == "1":
            swarmModeActive = True
            max_drones = int(self.swarmModeNumber.get())

        myAutopilotController.setSwarmMode(
            (int(self.swarmModeState.get()), int(self.swarmModeNumber.get()))
        )

        monitorOptions = []
        for i in range(0, len(self.monitorCheckBox)):
            if self.monitorOptionsSelected[i].get() == "1":
                monitorOptions.append(self.monitorOptions[i])

        dataServiceOptions = []
        for i in range(0, len(self.dataServiceCheckBox)):
            if self.dataServiceOptionsSelected[i].get() == "1":
                dataServiceOptions.append(self.dataServiceOptions[i])

        localMode = -1
        if self.var2.get() == 'local':
            localMode = self.localModeVar.get()

        communicationMode = self.var2.get()
        if communicationMode == "local" and self.localModeVar.get() == 0:
            externalBroker = [self.externalBrokerLocal0Entries[drones].get() for drones in range(max_drones)]
        else:
            externalBroker = self.var3.get()

        parameters = {
            "operationMode": self.var1.get(),
            "communicationMode": self.var2.get(),
            "externalBroker": externalBroker,
            "monitorOptions": monitorOptions,
            "dataServiceOptions": dataServiceOptions,
            "localMode": localMode,
            'max_drones': max_drones,
            'rc_checks': self.rcChecksVar.get(),
        }
        if self.var3.get() in PROTECTED_BROKERS:
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
    global confPanel

    splited = message.topic.split("/")
    origin = splited[0]
    destination = splited[1]
    command = splited[-1]

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
            drone_id = 0
            if swarmModeActive is True:
                drone_id = int(splited[-2])
            operation_drones.set_telemetry_info(telemetry_info, drone_id)
            myFrameSelector.myMapView.update_drone(drone_id)
            if drone_id == myFrameSelector.myMapView.selected_drone:
                myAutopilotController.raiseTelemetryFrame(drone_id)
            myAutopilotController.showTelemetryInfo(telemetry_info, drone_id)

        elif command == "disconnectAck":
            drone_id = 0
            if swarmModeActive is True:
                drone_id = int(splited[-2])
            myFrameSelector.myMapView.update_drone(drone_id)

    if origin == "dataService" and command == "storedPositions":
        # receive the positions stored by the data service

        data = message.payload.decode("utf-8")
        # converts received string to json
        data_json = json.loads(data)
        myRecordedPositionsWindow.putStoredPositions(data_json)


autoBootInstances: NewAutopilotService.AutoBoot = None


def configure(configuration_parameters):
    global panelFrame
    global client
    global autoBootInstances

    operation_mode = configuration_parameters['communicationMode']
    local_mode = configuration_parameters['localMode']
    application_name = __file__.split('\\')[-1][:-3]
    external_broker_address = configuration_parameters['externalBroker']
    if 'pass' in configuration_parameters.keys():
        broker_credentials = (configuration_parameters['username'], configuration_parameters['pass'])
    else:
        broker_credentials = None

    myConnectionManager = ConnectionManager()
    broker_settings = myConnectionManager.setParameters(operation_mode,
                                                        application_name,
                                                        local_mode=local_mode,
                                                        max_drones=max_drones,
                                                        external_broker_address=external_broker_address,
                                                        broker_credentials=broker_credentials)

    if broker_credentials is not None:
        apsUsername, apsPassword = broker_credentials
    else:
        apsUsername, apsPassword = None, None

    autoBootInstances = NewAutopilotService.AutoBoot()
    autoBootInstances.autoBoot(configuration_parameters['communicationMode'], configuration_parameters['operationMode'],
                               external_broker_address, apsUsername, apsPassword, max_drones, verbose=True)

    if configuration_parameters['rc_checks'] is False:
        autoBootInstances.disable_rc_checks()

    client = mqtt.Client("Dashboard", transport="websockets")
    client.on_message = on_message
    if 'credentials' in broker_settings['external'].keys():
        client.username_pw_set(*broker_settings['external']['credentials'])
    client.connect(host=broker_settings['external']['address'], port=broker_settings['external']['port'])
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

    operation_drones.set_active(configuration_parameters['max_drones'])
    myAutopilotController.operation_drones_max_drones_defined()
    myFrameSelector.myMapView.operation_drones_max_drones_defined()

    # this is to maximize the main window
    master.deiconify()


############################################################################
############################################################################
global max_drones
global swarmModeActive

master = tk.Tk()
new_window = tk.Toplevel(master)
new_window.title("Configuration panel")
new_window.geometry("900x600")
confPanel = ConfigurationPanel()
confPanelFrame = confPanel.buildFrame(new_window, configure)
confPanelFrame.pack()

master.title("Main window")
master.geometry("1150x600")
master.rowconfigure(0, weight=1)
master.rowconfigure(1, weight=15)
client = None
operation_drones = OperationDrones()
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
myAutopilotController = AutopilotController(operation_drones)
autopilotControlFrame = myAutopilotController.buildFrame(panelFrame)
autopilotControlFrame.grid(
    row=0, column=0, columnspan=3, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
)

# Camera control  frame ----------------------
myFrameSelector = FrameSelector(panelFrame, operation_drones)
myCameraController = myFrameSelector.myCameraController
myFrameSelector.getFrame().grid(
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

atexit.register(autoBootInstances.disconnect_instances)
