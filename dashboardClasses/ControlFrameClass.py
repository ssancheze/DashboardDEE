import tkinter as tk
from tkinter import messagebox


class ControlFrame:
    def __init__(self, operation_drones):
        self.operation_drones = operation_drones

    def buildFrame(self, fatherFrame):
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
            padx=5,
            pady=5,
            sticky=tk.N + tk.S + tk.E + tk.W,
        )

        self.disarmButton = tk.Button(
            self.controlFrame,
            text="Disarm",
            bg="green",
            fg="white",
            command=self.disarm,
        )
        self.disarmButton.grid(
            row=0,
            column=2,
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

        return self.controlFrame

    def setSwarmDroneNumber(self, swarmNumber):
        print(swarmNumber)
        self.swarmNumber = swarmNumber

    def _setState(self, _list, _val):
        for _index in self.swarmNumber:
            _list[_index] = _val

    def putClient(self, client):
        self.client = client

    def goN(self):
        if self.operation_drones.on_air > -1:
            for drone_id in self.swarmNumber:
                drone = self.operation_drones.drones[drone_id]
                if drone.on_air:
                    self.client.publish(
                        "dashBoard/autopilotService/" + str(drone_id) + "/go", "North"
                    )
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def goS(self):
        if self.operation_drones.on_air > -1:
            for drone_id in self.swarmNumber:
                drone = self.operation_drones.drones[drone_id]
                if drone.on_air:
                    self.client.publish(
                        "dashBoard/autopilotService/" + str(drone_id) + "/go", "South"
                    )
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def goE(self):
        if self.operation_drones.on_air > -1:
            for drone_id in self.swarmNumber:
                drone = self.operation_drones.drones[drone_id]
                if drone.on_air:
                    self.client.publish(
                        "dashBoard/autopilotService/" + str(drone_id) + "/go", "East"
                    )
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def goW(self):
        if self.operation_drones.on_air > -1:
            for drone_id in self.swarmNumber:
                drone = self.operation_drones.drones[drone_id]
                if drone.on_air:
                    self.client.publish(
                        "dashBoard/autopilotService/" + str(drone_id) + "/go", "West"
                    )
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def goNW(self):
        if self.operation_drones.on_air > -1:
            for drone_id in self.swarmNumber:
                drone = self.operation_drones.drones[drone_id]
                if drone.on_air:
                    self.client.publish(
                        "dashBoard/autopilotService/" + str(drone_id) + "/go",
                        "NorthWest",
                    )
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def goNE(self):
        if self.operation_drones.on_air > -1:
            for drone_id in self.swarmNumber:
                drone = self.operation_drones.drones[drone_id]
                if drone.on_air:
                    self.client.publish(
                        "dashBoard/autopilotService/" + str(drone_id) + "/go",
                        "NorthEst",
                    )
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def goSW(self):
        if self.operation_drones.on_air > -1:
            for drone_id in self.swarmNumber:
                drone = self.operation_drones.drones[drone_id]
                if drone.on_air:
                    self.client.publish(
                        "dashBoard/autopilotService/" + str(drone_id) + "/go",
                        "SouthWest",
                    )
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def goSE(self):
        if self.operation_drones.on_air > -1:
            for drone_id in self.swarmNumber:
                drone = self.operation_drones.drones[drone_id]
                if drone.on_air:
                    self.client.publish(
                        "dashBoard/autopilotService/" + str(drone_id) + "/go",
                        "SouthEst",
                    )
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def stop(self):
        if self.operation_drones.on_air > -1:
            for drone_id in self.swarmNumber:
                drone = self.operation_drones.drones[drone_id]
                if drone.on_air:
                    self.client.publish(
                        "dashBoard/autopilotService/" + str(drone_id) + "/go", "Stop"
                    )
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def RTL(self):
        if self.operation_drones.on_air > -1:
            for drone_id in self.swarmNumber:
                drone = self.operation_drones.drones[drone_id]
                if drone.on_air:
                    self.client.publish(
                        "dashBoard/autopilotService/"
                        + str(drone_id)
                        + "/returnToLaunch"
                    )
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def arm(self):
        if self.operation_drones.connected > -1:
            for drone_id in self.swarmNumber:
                drone = self.operation_drones.drones[drone_id]
                if drone.connected and not drone.on_air:
                    self.client.publish(
                        "dashBoard/autopilotService/" + str(drone_id) + "/armDrone"
                    )
        else:
            messagebox.showwarning(
                "Warning", "No puedes armar. Primero debes conectarte"
            )

    def disarm(self):
        if self.operation_drones.on_air < 1:
            for drone_id in self.swarmNumber:
                drone = self.operation_drones.drones[drone_id]
                if drone.connected and not drone.on_air:
                    self.client.publish(
                        "dashBoard/autopilotService/" + str(drone_id) + "/disarmDrone"
                    )
        else:
            messagebox.showwarning("Warning", "No puedes desarmar. Estas volando")

    def takeOff(self):
        if self.operation_drones.armed == -1:
            messagebox.showwarning("Warning", "Antes de despegar debes armar")
        elif self.operation_drones.armed > -1:
            for drone_id in self.swarmNumber:
                drone = self.operation_drones.drones[drone_id]
                if drone.armed and not drone.on_air:
                    self.client.publish(
                        "dashBoard/autopilotService/" + str(drone_id) + "/takeOff",
                        self.altitude.get(),
                    )
            # self._setState(self.onAir, True)
        else:
            messagebox.showwarning("Warning", "Ya estas volando")

    def land(self):
        if self.operation_drones.on_air > -1:
            for drone_id in self.swarmNumber:
                drone = self.operation_drones.drones[drone_id]
                if drone.on_air:
                    self.client.publish(
                        "dashBoard/autopilotService/" + str(drone_id) + "/land"
                    )
        else:
            messagebox.showwarning("Warning", "No estas volando")

    def drop(self):  # TBI
        if self.operation_drones.on_air > -1:
            for drone_id in self.swarmNumber:
                drone = self.operation_drones.drones[drone_id]
                if drone.on_air:
                    self.client.publish(
                        "dashBoard/LEDsService/" + str(drone_id) + "/drop"
                    )
        else:
            messagebox.showwarning("Warning", "No estas volando")
