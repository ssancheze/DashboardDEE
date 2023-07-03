import tkinter as tk
from dashboardClasses.CameraControllerClass import CameraController
from dashboardClasses.MapViewClass import MapViewHandler


class FrameSelector:
    def __init__(self, parent, operation_drones):
        # Main frame hosting everything
        self.masterFrame = tk.Frame(parent, padx=5, pady=5)
        self.masterFrame.rowconfigure(0, weight=4)
        self.masterFrame.rowconfigure(1, weight=1)
        self.masterFrame.columnconfigure(0, weight=1)
        self.masterFrame.columnconfigure(1, weight=1)
        self.masterFrame.columnconfigure(2, weight=3)

        # Frame hosting camera / map
        """self.contentFrame = tk.LabelFrame(self.masterFrame, text="Camera control", padx=5, pady=5)
        self.contentFrame.grid(column=0, sticky=tk.N + tk.S + tk.E + tk.W)"""
        self.myMapView = MapViewHandler(self.masterFrame, operation_drones)
        mapViewFrame = self.myMapView.getFrame()
        mapViewFrame.grid(
            row=0, columnspan=3, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.myCameraController = CameraController()
        cameraControllerFrame = self.myCameraController.buildFrame(self.masterFrame)
        cameraControllerFrame.grid(
            row=0, columnspan=3, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        # Frame hosting selector buttons
        self.cameraControllerButton = tk.Button(
            self.masterFrame,
            text="<",
            bg="red",
            fg="white",
            command=lambda: self.showFrame(0),
        )
        self.cameraControllerButton.grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.mapViewButton = tk.Button(
            self.masterFrame,
            text=">",
            bg="red",
            fg="white",
            command=lambda: self.showFrame(1),
        )
        self.mapViewButton.grid(
            row=1, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.frames = (
            cameraControllerFrame,
            mapViewFrame,
        )

    def showFrame(self, frame):
        self.frames[frame].tkraise()

    def getFrame(self):
        return self.masterFrame


if __name__ == "__main__":
    master = tk.Tk()
    master.title("DEBUG")
    myFrameSelector = FrameSelector(master)
    myFrameSelector.getFrame().pack(expand=tk.YES, fill=tk.BOTH)
    master.mainloop()
