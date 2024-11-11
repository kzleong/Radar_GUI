# General Library Imports
import json
import time
from serial.tools import list_ports
import os
import sys
from contextlib import suppress

# PyQt Imports
from PySide2 import QtGui
from PySide2.QtCore import QTimer, Qt
from PySide2.QtGui import QKeySequence
from PySide2.QtWidgets import (
    QAction,
    QTabWidget,
    QGridLayout,
    QMenu,
    QGroupBox,
    QLineEdit,
    QLabel,
    QPushButton,
    QComboBox,
    QFileDialog,
    QMainWindow,
    QWidget,
    QShortcut,
    QSlider,
    QCheckBox
)

# Local Imports
from common.cached_data import CachedDataType
from common.demo_defines import *
from common.gui_threads import *
from common.parseFrame import parseStandardFrame
from common.Common_Tabs.plot_1d import Plot1D
from common.Common_Tabs.plot_2d import Plot2D
from common.Common_Tabs.plot_3d import Plot3D
from common.Demo_Classes.surface_classification import SurfaceClassification
from common.Demo_Classes.people_tracking import PeopleTracking
from common.Demo_Classes.gesture_recognition import GestureRecognition
from common.Demo_Classes.level_sensing import LevelSensing
from common.Demo_Classes.small_obstacle import SmallObstacle
from common.Demo_Classes.out_of_box_x843 import OOBx843
from common.Demo_Classes.out_of_box_x432 import OOBx432
from common.Demo_Classes.true_ground_speed import TrueGroundSpeed
from common.Demo_Classes.long_range_pd import LongRangePD
from common.Demo_Classes.mobile_tracker import MobileTracker
from common.Demo_Classes.kick_to_open import KickToOpen
from common.Demo_Classes.calibration import Calibration
from common.Demo_Classes.vital_signs import VitalSigns
from common.Demo_Classes.dashcam import Dashcam
from common.Demo_Classes.ebikes_x432 import EBikes
from common.Demo_Classes.video_doorbell import VideoDoorbell
from common.Demo_Classes.two_pass_video_doorbell import TwoPassVideoDoorbell

# Logger
import logging

log = logging.getLogger(__name__)

class Core:
    def __init__(self):
        self.cachedData = CachedDataType()

        self.device = "xWR6843"
        self.demo = DEMO_OOB_x843

        self.frameTime = 50
        self.parser = UARTParser(type="DoubleCOMPort")

        self.replayFile = "replay.json"
        self.replay = False

        # set to 1
        self.isGUILaunched = 0
        self.playing = False
        self.replayFrameNum = 0

        # Populated with each demo and it's corresponding object
        self.demoClassDict = {
            #DEMO_OOB_x843: OOBx843(),
            #DEMO_OOB_x432: OOBx432(),
            #DEMO_3D_PEOPLE_TRACKING: PeopleTracking(),
            #DEMO_VITALS: VitalSigns(),
            #DEMO_SMALL_OBSTACLE: SmallObstacle(),
            #DEMO_GESTURE: GestureRecognition(),
            #DEMO_SURFACE: SurfaceClassification(),
            #DEMO_LEVEL_SENSING: LevelSensing(),
            #DEMO_GROUND_SPEED: TrueGroundSpeed(),
            #DEMO_LONG_RANGE: LongRangePD(),
            #DEMO_MOBILE_TRACKER: MobileTracker(),
            #DEMO_KTO: KickToOpen(),
            #DEMO_CALIBRATION: Calibration(),
            #DEMO_DASHCAM: Dashcam(),
            #DEMO_EBIKES: EBikes(),
            #DEMO_VIDEO_DOORBELL: VideoDoorbell(),
            #DEMO_TWO_PASS_VIDEO_DOORBELL: TwoPassVideoDoorbell(),
        }

    def loadCachedData(self, demoList, deviceList, recordAction, gridLayout, demoTabs):
        deviceName = self.cachedData.getCachedDeviceName()
        demoName = self.cachedData.getCachedDemoName()
        recordState = bool(self.cachedData.getCachedRecord())

        if deviceName in self.getDeviceList():
            deviceList.setCurrentIndex(self.getDeviceList().index(deviceName))

        if demoName in self.getDemoList():
            demoList.setCurrentIndex(self.getDemoList().index(demoName))
            self.changeDemo(demoList, deviceList, gridLayout, demoTabs)

        if recordState:
            recordAction.setChecked(True)

    def getDemoList(self):
        return DEVICE_DEMO_DICT[self.device]["demos"]

    def getDeviceList(self):
        return list(DEVICE_DEMO_DICT.keys())

    def changeDemo(self, demoList, deviceList, gridLayout, demoTabs):
        self.demo = demoList.currentText()

        if (self.isGUILaunched):
            self.cachedData.setCachedDemoName(self.demo)
            self.cachedData.setCachedDeviceName(deviceList.currentText())

        permanentWidgetsList = ["Connect to COM Ports", "Configuration", "Tabs", "Replay"]
        # Destroy current contents of graph pane
        for _ in range(demoTabs.count()):
            demoTabs.removeTab(0)
        for i in range(gridLayout.count()):
            try:
                currWidget = gridLayout.itemAt(i).widget()
                if currWidget.title() not in permanentWidgetsList:
                    currWidget.setVisible(False)
            except AttributeError as e:
                log.log(0, "Demo Tabs don't have title attribute. This is OK")
                continue

        # Make call to selected demo's initialization function
        if self.demo in self.demoClassDict:
            self.demoClassDict[self.demo].setupGUI(gridLayout, demoTabs, self.device)

    def changeDevice(self, demoList, deviceList, gridLayout, demoTabs):
        self.device = deviceList.currentText()

        if (self.isGUILaunched):
            self.cachedData.setCachedDemoName(demoList.currentText())
            self.cachedData.setCachedDeviceName(self.device)

        if DEVICE_DEMO_DICT[self.device]["singleCOM"]:
            self.parser.parserType = "SingleCOMPort"
        else:
            self.parser.parserType = "DoubleCOMPort"

        demoList.clear()
        demoList.addItems(DEVICE_DEMO_DICT[self.device]["demos"])

    def updateCOMPorts(self, cliCom, dataCom):
        if DEVICE_DEMO_DICT[self.device]["isxWRLx432"]:
            dataCom.setText(cliCom.text())
            dataCom.setEnabled(False)
        else:
            dataCom.setEnabled(True)

    def updateResetButton(self, sensorStopButton):
        if DEVICE_DEMO_DICT[self.device]["isxWRLx432"]:
            sensorStopButton.setHidden(True)  # TODO change to false once sending sensorStop is implemented
        else:
            sensorStopButton.setHidden(True)

    def stopSensor(self):
        self.parser.sendLine("sensorStop 0")

    def selectFile(self, filename):
        try:
            current_dir = os.getcwd()
            configDirectory = current_dir
            path = self.cachedData.getCachedCfgPath()
            if path != "":
                configDirectory = path
        except:
            configDirectory = ""

        fname = QFileDialog.getOpenFileName(caption="Open .cfg File", dir=configDirectory, filter="cfg(*.cfg)")
        filename.setText(str(fname[0]))
        return fname[0]

    def parseCfg(self, fname):
        if (self.replay):
            self.cfg = self.data['cfg']
        else:
            with open(fname, "r") as cfg_file:
                self.cfg = cfg_file.readlines()
                self.parser.cfg = self.cfg
                self.parser.demo = self.demo
                self.parser.device = self.device
        for line in self.cfg:
            args = line.split()
            if len(args) > 0:
                # trackingCfg
                if args[0] == "trackingCfg":
                    if len(args) < 5:
                        log.error("trackingCfg had fewer arguments than expected")
                    else:
                        with suppress(AttributeError):
                            self.demoClassDict[self.demo].parseTrackingCfg(args)
                elif args[0] == "SceneryParam" or args[0] == "boundaryBox":
                    if len(args) < 7:
                        log.error(
                            "SceneryParam/boundaryBox had fewer arguments than expected"
                        )
                    else:
                        with suppress(AttributeError):
                            self.demoClassDict[self.demo].parseBoundaryBox(args)
                elif args[0] == "frameCfg":
                    if len(args) < 4:
                        log.error("frameCfg had fewer arguments than expected")
                    else:
                        self.frameTime = float(args[5]) / 2
                elif args[0] == "sensorPosition":
                    # sensorPosition for x843 family has 3 args
                    if DEVICE_DEMO_DICT[self.device]["isxWRx843"] and len(args) < 4:
                        log.error("sensorPosition had fewer arguments than expected")
                    elif DEVICE_DEMO_DICT[self.device]["isxWRLx432"] and len(args) < 6:
                        log.error("sensorPosition had fewer arguments than expected")
                    else:
                        with suppress(AttributeError):
                            self.demoClassDict[self.demo].parseSensorPosition(
                                args, DEVICE_DEMO_DICT[self.device]["isxWRx843"]
                            )
                # Only used for Small Obstacle Detection
                elif args[0] == "occStateMach":
                    numZones = int(args[1])
                # Only used for Small Obstacle Detection
                elif args[0] == "zoneDef":
                    if len(args) < 8:
                        log.error("zoneDef had fewer arguments than expected")
                    else:
                        with suppress(AttributeError):
                            self.demoClassDict[self.demo].parseBoundaryBox(args)
                elif args[0] == "mpdBoundaryBox":
                    if len(args) < 8:
                        log.error("mpdBoundaryBox had fewer arguments than expected")
                    else:
                        with suppress(AttributeError):
                            self.demoClassDict[self.demo].parseBoundaryBox(args)
                elif args[0] == "chirpComnCfg":
                    if len(args) < 8:
                        log.error("chirpComnCfg had fewer arguments than expected")
                    else:
                        with suppress(AttributeError):
                            self.demoClassDict[self.demo].parseChirpComnCfg(args)
                elif args[0] == "chirpTimingCfg":
                    if len(args) < 6:
                        log.error("chirpTimingCfg had fewer arguments than expected")
                    else:
                        with suppress(AttributeError):
                            self.demoClassDict[self.demo].parseChirpTimingCfg(args)
                # TODO This is specifically guiMonitor for 60Lo, this parsing will break the gui when an SDK 3 config is sent
                elif args[0] == "guiMonitor":
                    if DEVICE_DEMO_DICT[self.device]["isxWRLx432"]:
                        if len(args) < 12:
                            log.error("guiMonitor had fewer arguments than expected")
                        else:
                            with suppress(AttributeError):
                                self.demoClassDict[self.demo].parseGuiMonitor(args)
                elif args[0] == "presenceDetectCfg":
                    with suppress(AttributeError):
                        self.demoClassDict[self.demo].parsePresenceDetectCfg(args)
                elif args[0] == "sigProcChainCfg2":
                    with suppress(AttributeError):
                        self.demoClassDict[self.demo].parseSigProcChainCfg2(args)
                elif args[0] == "mpdBoundaryArc":
                    if len(args) < 8:
                        log.error("mpdBoundaryArc had fewer arguments than expected")
                    else:
                        with suppress(AttributeError):
                            self.demoClassDict[self.demo].parseBoundaryBox(args)
                elif args[0] == "measureRangeBiasAndRxChanPhase":
                    with suppress(AttributeError):
                        self.demoClassDict[self.demo].parseRangePhaseCfg(args)
                elif args[0] == "clutterRemoval":
                    with suppress(AttributeError):
                        self.demoClassDict[self.demo].parseClutterRemovalCfg(args)
                elif args[0] == "sigProcChainCfg":
                    with suppress(AttributeError):
                        self.demoClassDict[self.demo].parseSigProcChainCfg(args)
                elif args[0] == "channelCfg":
                    with suppress(AttributeError):
                        self.demoClassDict[self.demo].parseChannelCfg(args)

        # Initialize 1D plot values based on cfg file
        with suppress(AttributeError):
            self.demoClassDict[self.demo].setRangeValues()

    def selectCfg(self, filename):
        try:
            file = self.selectFile(filename)
            self.cachedData.setCachedCfgPath(file)  # cache the file and demo used
            self.parseCfg(file)
        except Exception as e:
            log.error(e)
            log.error(
                "Parsing .cfg file failed. Did you select a valid configuration file?"
            )

        log.debug("Demo Changed to " + self.demo)
        if self.demo == DEMO_CALIBRATION:
            self.demoClassDict[self.demo].checkCalibrationParams()

    def sendCfg(self):
        try:
            if self.demo != "Replay":
                self.parser.sendCfg(self.cfg)
                sys.stdout.flush()
                self.parseTimer.start(int(self.frameTime))  # need this line
        except Exception as e:
            log.error(e)
            log.error("Parsing .cfg file failed. Did you select the right file?")

    def updateGraph(self, outputDict):
        self.demoClassDict[self.demo].updateGraph(outputDict)

    def connectCom(self, cliCom, dataCom, connectStatus):
        if self.demo == DEMO_GESTURE:
            self.frameTime = 25  # Gesture demo runs at 35ms frame time
        # init threads and timers
        self.uart_thread = parseUartThread(self.parser)

        self.uart_thread.fin.connect(self.updateGraph)
        self.parseTimer = QTimer()
        self.parseTimer.setSingleShot(False)
        self.parseTimer.timeout.connect(self.parseData)
        try:
            if os.name == "nt":
                uart = "COM" + cliCom.text()
                data = "COM" + dataCom.text()
            else:
                uart = cliCom.text()
                data = dataCom.text()
            if DEVICE_DEMO_DICT[self.device]["isxWRx843"]:  # If using x843 device
                self.parser.connectComPorts(uart, data)
            else:  # If not x843 device then defer to x432 device
                if self.demo == DEMO_GESTURE or self.demo == DEMO_KTO or self.demo == DEMO_TWO_PASS_VIDEO_DOORBELL or self.demo == DEMO_VIDEO_DOORBELL:
                    self.parser.connectComPort(uart, 1250000)
                else:
                    self.parser.connectComPort(uart)
            connectStatus.setText("Connected")
        except Exception as e:
            log.error(e)
            connectStatus.setText("Unable to Connect")
            return -1

        return 0

    def startApp(self):
        if (self.replay and self.playing is False):
            self.replayTimer = QTimer()
            self.replayTimer.setSingleShot(True)
            self.replayTimer.timeout.connect(self.replayData)
            self.playing = True
            self.replayTimer.start(100)  # arbitrary value to start plotting
        elif (self.replay and self.playing is True):
            self.playing = False
        else:
            self.parseTimer.start(int(self.frameTime))  # need this line, this is for normal plotting

    def loadForReplay(self, state):
        if (state):
            self.cachedData.setCachedRecord = "True"
            with open(self.replayFile[0], 'r') as fp:
                self.data = json.load(fp)
            self.parseCfg("")
            self.sl.setMinimum(0)
            self.sl.setMaximum(len(self.data['data']) - 1)
            self.sl.setValue(0)
            self.sl.setTickInterval(5)
            # TODO need to load correct demo from file
        else:
            self.cachedData.setCachedRecord = "False"

    def replayData(self):
        if (self.playing):
            outputDict = self.data['data'][self.replayFrameNum]['frameData']
            self.updateGraph(outputDict)
            self.replayFrameNum += 1
            self.sl.setValue(self.replayFrameNum)
            if (self.replayFrameNum < len(self.data['data'])):
                self.replayTimer.start(
                    self.data['data'][self.replayFrameNum]['timestamp'] - self.data['data'][self.replayFrameNum - 1][
                        'timestamp'])

    def sliderValueChange(self):
        self.replayFrameNum = self.sl.value()

    def parseData(self):
        self.uart_thread.start(priority=QThread.HighestPriority)

    def gracefulReset(self):
        self.parseTimer.stop()
        self.uart_thread.stop()
        if self.parser.cliCom is not None:
            self.parser.cliCom.close()
        if self.parser.dataCom is not None:
            self.parser.dataCom.close()
        for demo in self.demoClassDict.values():
            if hasattr(demo, "plot_3d_thread"):
                demo.plot_3d_thread.stop()
            if hasattr(demo, "plot_3d"):
                demo.removeAllBoundBoxes()


if __name__ == "__main__":
    core = Core()

    core.isGUILaunched = 0
    print("memes")
    cliCom = QLineEdit("")
    dataCom = QLineEdit("")
    connectStatus = QLabel("Not Connected")
    print("memes")
    core.connectCom(cliCom, dataCom, connectStatus)

    core.startApp()
    print("memes")
    core.gracefulReset()
    print("hi")
