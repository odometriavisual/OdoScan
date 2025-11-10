from array import *
from numpy import *
from numpy.random import *
from math import *
from M2M_Remote_lib import *

Get_M2M_Ascan = 1
Simul_Ascan = 0


############################################################
# GUI class
class mon_ihm():
    def __init__(self):
        global Get_M2M_Ascan

        self.m2m_system=M2k_system()
        self.m2m_system.set_ip("127.0.0.1",4444)
        self.m2m_system.set_ip_data_server("127.0.0.1",4445)
        self.m2m_system.connect()

        version = str(M2K_GetMulti2000Version(self.m2m_system.socket))
        if "UV" in version:
            self.m2m_system.UV_detected = True
            print("UV detected")
        else:
            self.m2m_system.UV_detected = False


    def get_ascan(self):
        global fenetre
        # print('getting ascans')
        if self.m2m_system.UV_detected:
            # bug for the moment in UV; Ascan is sent in big_indian which is not the case in Acquire / Multi2000
            self.ascan_list=M2K_Get_All_Ascans_big_indian(self.m2m_system.socket)
        else:
            self.ascan_list=M2K_Get_All_Ascans(self.m2m_system.socket)

        # self.new_time=time.perf_counter()
        # fps = 1 / (self.new_time-self.last_time)
        # self.last_time=self.new_time

        # texte = "FPS : " + '%10.2f' % (fps)
        # self.Texte_Affiche_Temps.set(texte)
        # print(f'ascans: {len(self.ascan_list)}')
        # print(f'length: {len(self.ascan_list[0])}')
    


def main():
    run = mon_ihm()
    frames = 0
    seconds = 0
    last_time = time.perf_counter()

    while frames < 100:
        run.get_ascan()
        new_time = time.perf_counter()
        diff = new_time - last_time
        seconds += diff
        last_time = new_time
        print(f"fps: {1 / diff}")
        frames += 1

    print(f"frames per second (avg): {frames / seconds}")

if __name__ == '__main__':
    main()

