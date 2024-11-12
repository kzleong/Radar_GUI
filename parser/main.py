from core import Core


if __name__ == "__main__":
    core = Core()
    core.device = "xWR6843"
    core.demo = "DEMO_3D_PEOPLE_TRACKING"
    config_file = "C:\\ti\\radar_toolbox_2_20_00_05\\source\\ti\\examples\\People_Tracking\\Overhead_3D_People_Tracking\\chirp_configs\\pt_6843_3d_aop_overhead_3m_radial.cfg"
    core.selectCfg(config_file)
    core.connectCom("6", "7")
    core.sendCfg()
    while True:
        core.parseData()