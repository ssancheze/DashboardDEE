import tkinter as tk
from tkinter import messagebox


class ControlFrame:
    def buldFrame(self, fatherFrame):
        self.controlFrame = tk.LabelFrame(fatherFrame, text="Control")

        self.controlFrame.rowconfigure(0, weight=1)
        self.controlFrame.rowconfigure(1, weight=1)
        self.controlFrame.rowconfigure(2, weight=3)
        self.controlFrame.rowconfigure(3, weight=1)

        self.controlFrame.columnconfigure(0, weight=1)
        self.controlFrame.columnconfigure(1, weight=1)
        self.controlFrame.columnconfigure(2, weight=1)

        self.armButton = tk.Button(
            self.controlFrame, text="Arm", bg="red", fg="white", command=self.arm
        )
        self.armButton.grid(
            row=0,
            column=0,
            columnspan=3,
            padx=5,
            pady=5,
            sticky=tk.N + tk.S + tk.E + tk.W,
        )

        self.altitude = tk.Entry(self.controlFrame)
        self.altitude.grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.takeOffButton = tk.Button(
            self.controlFrame,
            text="TakeOff",
            bg="red",
            fg="white",
            command=self.takeOff,
        )
        self.takeOffButton.grid(
            row=1,
            column=1,
            columnspan=2,
            padx=5,
            pady=5,
            sticky=tk.N + tk.S + tk.E + tk.W,
        )

        self.buttonsFrame = tk.LabelFrame(self.controlFrame, text="go")
        self.buttonsFrame.grid(row=2, column=0, columnspan=3, padx=15, pady=5)
        self.buttonsFrame.rowconfigure(0, weight=1)
        self.buttonsFrame.rowconfigure(1, weight=1)
        self.buttonsFrame.rowconfigure(2, weight=1)

        self.buttonsFrame.columnconfigure(0, weight=1)
        self.buttonsFrame.columnconfigure(1, weight=1)
        self.buttonsFrame.columnconfigure(2, weight=1)

        self.NWButton = tk.Button(
            self.buttonsFrame,
            text="\u2B09",
            width=3,
            bg="#FFBB00",
            fg="black",
            command=self.goNW,
        )
        self.NWButton.grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.NButton = tk.Button(
            self.buttonsFrame,
            text="N",
            width=3,
            bg="#FFBB00",
            fg="black",
            command=self.goN,
        )
        self.NButton.grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.NEButton = tk.Button(
            self.buttonsFrame,
            text="\u2B08",
            width=3,
            bg="#FFBB00",
            fg="black",
            command=self.goNE,
        )
        self.NEButton.grid(
            row=0, column=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.WButton = tk.Button(
            self.buttonsFrame,
            text="W",
            width=3,
            bg="#FFBB00",
            fg="black",
            command=self.goW,
        )
        self.WButton.grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.StopButton = tk.Button(
            self.buttonsFrame,
            text="Stop",
            width=3,
            bg="#FFBB00",
            fg="black",
            command=self.stop,
        )
        self.StopButton.grid(
            row=1, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.EButton = tk.Button(
            self.buttonsFrame,
            text="E",
            width=3,
            bg="#FFBB00",
            fg="black",
            command=self.goE,
        )
        self.EButton.grid(
            row=1, column=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.SWButton = tk.Button(
            self.buttonsFrame,
            text="\u2B0B",
            width=3,
            bg="#FFBB00",
            fg="black",
            command=self.goSW,
        )
        self.SWButton.grid(
            row=2, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.SButton = tk.Button(
            self.buttonsFrame,
            text="S",
            width=3,
            bg="#FFBB00",
            fg="black",
            command=self.goS,
        )
        self.SButton.grid(
            row=2, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.SEButton = tk.Button(
            self.buttonsFrame,
            text="\u2B0A",
            width=3,
            bg="#FFBB00",
            fg="black",
            command=self.goSE,
        )
        self.SEButton.grid(
            row=2, column=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.RTLButton = tk.Button(
            self.controlFrame, text="RTL", bg="red", fg="white", command=self.RTL
        )
        self.RTLButton.grid(
            row=3, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.LandButton = tk.Button(
            self.controlFrame, text="Land", bg="red", fg="white", command=self.land
        )
        self.LandButton.grid(
            row=3, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.DropButton = tk.Button(
            self.controlFrame, text="Drop", bg="#FFBB00", fg="black", command=self.drop
        )
        self.DropButton.grid(
            row=3, column=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.swarmNumber = [0]
        self.activeDronesList = [0, 0, 0, 0, 0, 0]
        self.state = ["disconnected" for _ in range(6)]
        self.onAir = [False for _ in range(6)]
        self.connected = [False for _ in range(6)]

        return self.controlFrame

    def setSwarmDroneNumber(self, swarmNumber):
        print(swarmNumber)
        self.swarmNumber = swarmNumber

    #    def getLogicList(self):
    #        return [((self.swarmNumber >> n) & 1) for n in range(6)]
    #
    #    def getIndexes(self):
    #        logicList = self.getLogicList()
    #        trueArr = []
    #        for nn in range(len(logicList)):
    #            if logicList[nn] == 1:
    #                trueArr.append(nn)
    #        return trueArr

    def allOnAir(self):
        for _vals in self.swarmNumber:
            if self.onAir[_vals] is False:
                return False
        return True

    def allConnected(self):
        for _vals in self.swarmNumber:
            if self.connected[_vals] is False:
                return False
        return True

    def anyFlying(self):
        for _vals in self.swarmNumber:
            if self.state[_vals] == "flying":
                return True
        return False

    def allFlying(self):
        for _vals in self.swarmNumber:
            if self.state[_vals] != "flying":
                return False
        return True

    def _setState(self, _list, _val):
        for _index in self.swarmNumber:
            _list[_index] = _val

    def putClient(self, client):
        self.client = client

    def goN(self):
        if self.allOnAir():
            for droneId in self.swarmNumber:
                self.client.publish("dashBoard/autopilotService/" + str(droneId) + "/go", "North")
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def goS(self):
        if self.allOnAir():
            for droneId in self.swarmNumber:
                self.client.publish("dashBoard/autopilotService/" + str(droneId) + "/go", "South")
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def goE(self):
        if self.allOnAir():
            for droneId in self.swarmNumber:
                self.client.publish("dashBoard/autopilotService/" + str(droneId) + "/go", "East")
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def goW(self):
        if self.allOnAir():
            for droneId in self.swarmNumber:
                self.client.publish("dashBoard/autopilotService/" + str(droneId) + "/go", "West")
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def goNW(self):
        if self.allOnAir():
            for droneId in self.swarmNumber:
                self.client.publish("dashBoard/autopilotService/" + str(droneId) + "/go", "NorthWest")
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def goNE(self):
        if self.allOnAir():
            for droneId in self.swarmNumber:
                self.client.publish("dashBoard/autopilotService/" + str(droneId) + "/go", "NorthEst")
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def goSW(self):
        if self.allOnAir():
            for droneId in self.swarmNumber:
                self.client.publish("dashBoard/autopilotService/" + str(droneId) + "/go", "SouthWest")
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def goSE(self):
        if self.allOnAir():
            for droneId in self.swarmNumber:
                self.client.publish("dashBoard/autopilotService/" + str(droneId) + "/go", "SouthEst")
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def stop(self):
        if self.allOnAir():
            for droneId in self.swarmNumber:
                self.client.publish("dashBoard/autopilotService/" + str(droneId) + "/go", "Stop")
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def RTL(self):
        if self.allOnAir():
            for droneId in self.swarmNumber:
                self.client.publish("dashBoard/autopilotService/" + str(droneId) + "/returnToLaunch")
            self.RTLButton["text"] = "Returning"
            self.RTLButton["bg"] = "orange"
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def arm(self):
        if self.armButton["text"] == "Arm":
            if not self.allConnected():
                messagebox.showwarning(
                    "Warning", "No puedes armar. Primero debes conectarte"
                )
            else:
                for droneId in self.swarmNumber:
                    self.client.publish("dashBoard/autopilotService/" + str(droneId) + "/armDrone")
                self.armButton["text"] = "Arming ..."
                self.armButton["bg"] = "orange"
        elif not self.anyFlying():
            for droneId in self.swarmNumber:
                self.client.publish("dashBoard/autopilotService/" + str(droneId) + "/disarmDrone")
        else:
            messagebox.showwarning("Warning", "No puedes desarmar. Estas volando")

    def takeOff(self):
        if self.armButton["text"] == "Arm":
            messagebox.showwarning("Warning", "Antes de despegar debes armar")
        elif not self.anyFlying():
            for droneId in self.swarmNumber:
                self.client.publish(
                    "dashBoard/autopilotService/" + str(droneId) + "/takeOff", self.altitude.get()
                )
            self._setState(self.onAir, True)
            self.takeOffButton["text"] = "taking off ..."
            self.takeOffButton["bg"] = "orange"
        else:
            messagebox.showwarning("Warning", "Ya estas volando")

    def land(self):
        if self.allFlying():
            for droneId in self.swarmNumber:
                self.client.publish("dashBoard/autopilotService/" + str(droneId) + "/land")
            self.LandButton["text"] = "Landing"
            self.LandButton["bg"] = "orange"
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def drop(self):
        for droneId in self.swarmNumber:
            self.client.publish("dashBoard/LEDsService/drop/") # POR IMPLEMENTAR
        """if self.onAir:
            self.client.publish('dashBoard/LEDsService/drop')
        else:
            messagebox.showwarning("Warning", "No estas volando")"""

    def setState(self, state):
        for droneId in self.swarmNumber:
            if self.state[droneId] != state:
                self.state[droneId] = state
                if self.state[droneId] == "connected":
                    self.connected[droneId] = True
                if self.state[droneId] == "arming":
                    self.armButton["text"] = "Arming ..."
                    self.armButton["bg"] = "orange"
                elif self.state[droneId] == "armed":
                    self.armButton["text"] = "Disarm"
                    self.armButton["bg"] = "green"
                elif self.state[droneId] == "disarmed":
                    self.armButton["text"] = "Arm"
                    self.armButton["bg"] = "red"
                elif self.state[droneId] == "flying":
                    self.takeOffButton["text"] = "Flying"
                    self.takeOffButton["bg"] = "green"
                elif self.state[droneId] == "onHearth":
                    self.LandButton["text"] = "Land"
                    self.LandButton["bg"] = "red"
                    self.onAir[droneId] = False
                    self.takeOffButton["text"] = "TakeOff"
                    self.takeOffButton["bg"] = "red"
                    self.armButton["text"] = "Arm"
                    self.armButton["bg"] = "red"
                    self.RTLButton["text"] = "RTL"
                    self.RTLButton["bg"] = "red"

    def isOnAir(self):
        return any(self.onAir)
        # Checks all drones rather than those selected

    def setDisconnected(self):
        for n in self.connected:
            self.connected[n] = False
