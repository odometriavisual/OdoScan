#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EBoujon
#
# Created:     09/10/2014
# Copyright:   (c) EBoujon 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import win32com.client
import ctypes
from array import *
from numpy import *
from numpy.random import *
from math import *
import tkinter
from M2M_Remote_lib import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

Get_M2M_Ascan = 1
Simul_Ascan = 0


############################################################
# GUI class
class mon_ihm(tkinter.Tk):
    def __init__(self, parent):
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


        tkinter.Tk.__init__(self, parent)

        # for digital filter tests
        #self.sf1_filter_dll=ctypes.WinDLL("sf1_filter_calc.dll")
        #self.sf1_filter_Init_Filter = self.sf1_filter_dll.sf1_filter_Init_Filter
        #self.sf1_filter_Apply_Filter = self.sf1_filter_dll.sf1_filter_Apply_Filter

        self.parent = parent
        self.initialize()

    def initialize(self):

        row = 0
        self.nb_click = 0
        self.grid
        self.height = 100

        self.width = 100
        self.gain = 0
        self.coeff_gain = 1
        self.num_seq = 0
        self.disp_ascan_size = 1200

        self.new_time=time.perf_counter()
        self.last_time=self.new_time

        self.ratio = 1
        self.export=0

        self.plot_created = False
        self.mem_ascan_list=0
        
        #----------------------------------------------------------------------------------
        # Menu initialization (buttons and so on...)
        self.bouton_sortir = tkinter.Button(self, text="Exit",
                                            command=self.destroy)
        row = 1
        self.bouton_sortir.grid(row=row, column=0)

        self.Texte_Affiche_Temps = tkinter.StringVar()
        self.texte1 = tkinter.Label(self, textvariable=self.Texte_Affiche_Temps, fg='black')
        self.texte1.grid(row=row, column=1)


        row += 1

        self.widget_gain = tkinter.Scale(self, from_=0, to=40, command=self.set_gain, orient=tkinter.HORIZONTAL,
                                         label="Digital Gain")
        self.widget_gain.grid(row=row, column=1)
        row += 1


        self.bouton_export = tkinter.Button(self,
                                            text="                              Export Ascan                        ",
                                            command=self.action_export)

        self.bouton_export.grid(row=row, column=1)
        row += 1

        self.bouton_raz_codeur = tkinter.Button(self,text="                                                     set image ref                                                      ",command=self.action_set_ref)
        self.bouton_raz_codeur.grid(row = row, column = 3)
        row += 1

        #----------------------------------------------------------------------------------
        # Ascan Area definition



        if self.plot_created == False:
        #if 0:
            plt.ion()
            plt.show()
            self.list_fig=[]
            self.list_implot=[]

            self.dynamic_amplitude=self.m2m_system.get_dynamic_amplitude()
            self.dynamic_amplitude /= 100.0
            print("Dynamic amplitude: ",self.dynamic_amplitude)

            self.get_ascan()

            #fenetre.cscans.append ( numpy.arange(long(fenetre.acquisition_length*fenetre.incremental_array_size[salvo]), dtype="float").reshape(int(fenetre.incremental_array_size[salvo]),fenetre.acquisition_length))
            salvo=0
            self.list_fig.append(plt.figure(salvo))

            self.plt_subplot = self.list_fig[salvo].add_subplot(111)  # Add subplot to the figure

            self.list_implot.append( plt.imshow(self.ascan_list, clim=(0, 32768/self.dynamic_amplitude)))
            self.list_implot[salvo].set_cmap('jet')


            #self.fig,self.ax=self.plt_subplots()

            plt.ion()
            plt.colorbar(self.list_implot[salvo], ax=self.plt_subplot, shrink=0.5)
            plt.subplots_adjust(left=0.125, bottom=0.125, right=0.9, top=0.9, wspace=None, hspace=None)
            #plt.colorbar()

            ratio=float(self.length)/float(self.nb_ascans)
            self.plt_subplot.set_aspect(ratio)

            texte = "Cscan Salvo " + str(salvo +1)
            plt.title(texte)

            print ("Bscan of columns:",self.length)
            print ("Bscan of lines:",self.nb_ascans)
            self.zone_dessin = tkinter.Canvas(self, width=self.width, height=self.height, bd=4, relief="raised", bg="black")
            self.zone_dessin.grid(row=2, column=0, rowspan=row)  #Affiche le canevas



        # Ascan lines creation, will be updated in position in refresh function
        
    ############################ managing GUI #########################

    def action_export(self):
        self.export=1

    def set_gain(self, gain):
        """

        :type self: object
        """
        self.gain = float(gain)
        self.coeff_gain = pow(10.0, self.gain / 20.0)
        print (self.coeff_gain)

    ##################################################################
    ## refresh ascan
    def display_ascan(self, ascan):
        global Get_M2M_Ascan
        global Simul_Ascan
        global fenetre

        fenetre.new_time=time.perf_counter()
        fenetre.last_time=fenetre.new_time
        fps=1.0/(fenetre.new_time-fenetre.last_time)

        texte = "FPS : " + '%10.2f' % (fps)
        fenetre.Texte_Affiche_Temps.set(texte)
        # display Ascan by redefinig lines position on the screen in function of scale, compression...

        self.get_ascan()

        if self.export:
            excel = win32com.client.gencache.EnsureDispatch('Excel.Application')
            xls = excel.Workbooks.Add()
            xls_open = True
            xls_line = 1
            ws = xls.ActiveSheet
            ws.Name = "Ascan"
            excel.Visible = True

            for i in range(0, ascan.length - 1):
                ws.Cells(i + 1, 1).Value = float(ascan.data[i])*100.0/32768.0
            self.export=0


        #texte = "RMS : " + str(ascan.RMS_value()-ascan.average())
        #fenetre.Texte_Affiche_Temps.set(texte)


    ####################################################################################


    ##################################################################################################
    # Get setting Ascan from M2000 when in "Setting" menu
    ##################################################################################################
    def get_ascan(self):
        global fenetre
        # print('getting ascans')
        if self.m2m_system.UV_detected:
            # bug for the moment in UV; Ascan is sent in big_indian which is not the case in Acquire / Multi2000
            self.ascan_list=M2K_Get_All_Ascans_big_indian(self.m2m_system.socket)
        else:
            self.ascan_list=M2K_Get_All_Ascans(self.m2m_system.socket)

        self.new_time=time.perf_counter()
        fps=1 / (self.new_time-self.last_time)
        self.last_time=self.new_time

        texte = "FPS : " + '%10.2f' % (fps)
        self.Texte_Affiche_Temps.set(texte)
        print(texte)
        # display Ascan by redefinig lines position on the screen in function of scale, compression...

        self.length = len(self.ascan_list[0])
        self.nb_ascans = len(self.ascan_list)
        #self.ratio = float(self.length)/float(self.compressed_length)
        #if self.ratio == 0:
        #    self.ratio = 1
        print(f'ascans: {self.nb_ascans}')
        print(f'length: {self.length}')


    def action_set_ref(self):
        
        if isinstance(fenetre.mem_ascan_list,int):
            fenetre.get_ascan()
            self.mem_ascan_list=fenetre.ascan_list
            print("set_ref")
        else:
            self.mem_ascan_list = 0
            
#################################################################################
###

def update_diplay():
    global fenetre, ascan

    fenetre.get_ascan()
    #fenetre.display_ascan(ascan)
    if isinstance(fenetre.mem_ascan_list,int) == False:
        fenetre.ascan_list-=fenetre.mem_ascan_list
        
    fenetre.ascan_list=fenetre.ascan_list*fenetre.coeff_gain
    

    fenetre.list_implot[0].set_data(fenetre.ascan_list.T)
    plt.show()
    plt.draw()

    fenetre.after(10, update_diplay)


def main():
    pass


if __name__ == '__main__':
    main()


fenetre = mon_ihm(None )
fenetre.title("demo display Bscan")
fenetre.after(10, update_diplay)

fenetre.mainloop()

