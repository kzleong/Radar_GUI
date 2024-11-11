import sys
import os

# add common folder to path
sys.path.insert(1, "C:\\ti\\radar_toolbox_2_20_00_05\\tools\\visualizers\\Applications_Visualizer\\common")

from serial_core import Core

# Demo List
from demo_defines import *

# Logging (possible levels: DEBUG, INFO, WARNING, ERROR, CRITICAL)
import logging

def main():
    core = Core()

    # Set the device and demo
    core.device = "xWR6843"
    core.demo = "DEMO_3D_PEOPLE_TRACKING"

    # Load a configuration file
    config_file = "C:\\ti\\radar_toolbox_2_20_00_05\\source\\ti\\examples\\People_Tracking\\Overhead_3D_People_Tracking\\chirp_configs\\pt_6843_3d_aop_overhead_3m_radial.cfg"
    core.selectCfg(config_file)

    # Connect to the COM ports
    core.connectCom("6", "7", QLabel(""))
    #
    # # Start the application
    # core.startApp()
    #
    # # Process data
    # while True:
    #     core.parseData()
    #     # Do something with the data, e.g., call core.updateGraph(output_dict)

if __name__ == "__main__":
    main()