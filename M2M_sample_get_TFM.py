# -*- coding: utf8 -*-


import win32com.client
import tkinter
from math import *
from skimage import data, io, filters

from string import *

import time

import os
import sys
import array

import struct
import inspect
import binascii
import ctypes

import threading
import time
import csv
import os

import numpy

import matplotlib.pyplot as plt

from M2M_Remote_lib import *


##############################################################################
# needs Acquire 1.3.8 and later
##############################################################################


##############################################################################
class voyant():
    def __init__(self, parent, pos_x, pos_y, taille,couleur):
        self.parent = parent

        self.position_x = pos_x
        self.position_y = pos_y
        self.graphique=self.parent.create_oval(pos_x,pos_y,pos_x+taille,pos_y+taille, fill=couleur, outline='blue', width=1)

    def change_couleur(self, couleur):
        self.parent.itemconfig(self.graphique, fill=couleur)

##############################################################################

class mon_ihm(tkinter.Tk):
    def __init__(self,parent):
        tkinter.Tk.__init__(self,parent)
        self.m2m_system=M2k_system()
        #self.m2m_system.set_ip("100.100.100.11",4444)
        self.m2m_system.set_ip("127.0.0.1",4444)
        self.m2m_system.set_ip_data_server("127.0.0.1",4445)
        self.m2m_system.connect()

        if (self.m2m_system.get_TFM_Mode(0) == 0):
            print ("Error, current configuration must be in TFM on Salvo 1")
            exit(0)

        self.nb_of_cycles=0

        self.parent = parent

        self.tcharge=0
        self.tstart=0
        self.tstop=0
        self.waitstop=0

        self.initialize()

    def initialize(self):
        self.nb_click = 0
        self.grid

        self.champ_etape = tkinter.Label(self, text="Alarms")

        # On affiche le label dans la fenetre
        self.champ_etape.grid(row = 0, column = 0)
        row = 0

        self.Texte_Affiche_Etape = tkinter.StringVar()
        self.texte=tkinter.Label(self, textvariable=self.Texte_Affiche_Etape,fg='black')
        self.texte.grid(row = row, column = 3)
        row += 1
        self.Texte_Affiche_Temps = tkinter.StringVar()
        self.texte1=tkinter.Label(self, textvariable=self.Texte_Affiche_Temps,fg='black')
        self.texte1.grid(row = row, column = 3)
        row += 1
        self.bouton_raz_codeur = tkinter.Button(self,text="                                                     Raz Codeur                                                       ",command=self.action_raz)
        self.bouton_raz_codeur.grid(row = row, column = 3)
        row += 1
        self.bouton_raz_codeur = tkinter.Button(self,text="                                                     set image ref                                                      ",command=self.action_set_ref)
        self.bouton_raz_codeur.grid(row = row, column = 3)
        row += 1

        self.bouton_clique = tkinter.Button(self,text="                                                Start Acquisition                                                  ",command=self.action_start)
        self.bouton_clique.grid(row = row, column = 3)
        row += 1
        self.bouton_stop = tkinter.Button(self,text="                                                 Stop Acquisition                                                  ",command=self.action_stop)
        self.bouton_stop.grid(row = row, column = 3)
        row += 1
        self.bouton_sortir =tkinter.Button(self,text="                                                           End                                                               ",  command=self.destroy)
        self.bouton_sortir.grid(row = row, column = 3)
        row += 1
        self.zone_dessin = tkinter.Canvas(self, width=600, height=300)
        self.zone_dessin.grid(row=2, column =0 )  #Affiche le canevas

        self.x=100
        self.y=200
        self.ligne=self.zone_dessin.create_line(100,100,self.x,self.y,width=3,arrow=tkinter.LAST, fill="grey") #Dessine une ligne en diagonale

        self.x = 100
        self.y = 0

        self.start_time=0.0
        self.start_acqui = 0


        if self.m2m_system.connected == True:
            self.bt2 = voyant(self.zone_dessin,10,10,20,'Green')
        else:
             self.bt2 = voyant(self.zone_dessin,10,10,20,'Red')

        if self.m2m_system.get_TFM_Mode(0) ==0:
            print ("The Acquire configuration must use TFM")

        TFM = M2K_GetTFMImage(self.m2m_system.socket,0)
        self.Mem_TFM=TFM
        self.image = plt.imshow(TFM,cmap="rainbow", vmin=0, vmax=2E7)

        self.update_Acquire_Param()

        
        self.stacked_max_values = []

        plt.show(block=False)
        plt.draw()


    def update_Acquire_Param(self):
        # go in the menu of Acquire which used to set parameters (some parameters are only readable in this menu)
        # these functions are coded in "M2M_remote_lib"
        self.m2m_system.show_settings()

        self.nb_sequences=0
        # stop sequencer to accelerate data exchange. (not indispensable)
        M2K_StopHardAndNoWrite(self.m2m_system.socket)
        # read the scanning parameters (begin, end anc acquisition step)
        self.scanning_step = self.m2m_system.get_scanning_step()
        self.scanning_begin = self.m2m_system.get_scanning_begin()
        self.scanning_end = self.m2m_system.get_scanning_end()

        # get information about the configuration structure (parallel mode or not)
        self.IsMultipleReconstruction = M2K_IsMultipleReconstruction(self.m2m_system.socket)

        # Read number of Salvoes. in most of the cases, there are several salvos when there are several probes
        self.Nb_Salvos = M2K_GetNbSalvo(self.m2m_system.socket)
        if self.Nb_Salvos>1:
                print ("Error: demo program considers only one salvo")

        if self.IsMultipleReconstruction:
            print ("Error: demo program considers no multiple reconstructions")
        else:
            self.nb_sequences=M2K_GetNbSequences(self.m2m_system.socket, 0)
            print ("Sequences: ",self.nb_sequences)

        # get information about number of gates. In this application certainly always gate "1" (second one) will be used
        self.nb_gates=self.m2m_system.get_nb_gates(0)
        self.nb_shots=M2K_GetNbShots(self.m2m_system.socket, 0, 0)
        print ("nb shots",self.nb_shots)
        #self.nb_shots=1
        self.nb_mechanical_positions = self.m2m_system.get_nb_mechanical_positions()
        print ("nb_mechanical positions ",self.nb_mechanical_positions)

        self.inputs_available = self.m2m_system.get_inputs_available()
        print ("Imputs ",self.inputs_available)

        if self.nb_gates>1:
            print ("Error: demo considers one single gate")

        self.is_gate_store_TFM=self.m2m_system.get_is_Gate_Store_TFM(0)
        if self.is_gate_store_TFM != 1:
            print("Error, demo consider that gate must store TFM")
        else:
            print ("gate store TFM: ",self.is_gate_store_TFM)

        self.nb_echo_in_gate = self.m2m_system.get_nb_echo_in_gate(0, 0)
        if self.nb_echo_in_gate > 1:
            print ("Error,nb echoes in gate must be 1")

        self.is_gate_store_sum = self.m2m_system.is_gate_store_sum(0, 0)
        if self.is_gate_store_sum:
            print ("Error,gate must not store summ Ascan")

        self.is_gate_store_elem = self.m2m_system.is_gate_store_elem(0, 0)
        if self.is_gate_store_elem:
            print ("Error,gate must not store elementary Ascan")

        self.is_gate_store_AD = self.m2m_system.is_gate_store_AD(0, 0)
        print ("gate is store AD",self.is_gate_store_AD)
        if self.is_gate_store_AD :
            print ("Error: gate must not store Amplitude and Distance (TOF)")

        self.is_gate_shot_by_shot_mode = self.m2m_system.is_gate_shot_by_shot_mode(0,0)
        if self.is_gate_shot_by_shot_mode:
            print ("Error: gate must not be  shot_by_shot_mode ")

        # set flag to memorise parameters have been updated
        self.updated=True
        print ("Scanning begin: ", self.scanning_begin)
        print ("Scanning end: ", self.scanning_end)
        print ("Scanning step: ", self.scanning_step)
        print ("Nb Salvoes: ", self.Nb_Salvos)
        print ("Nb Sequences: ", self.nb_sequences)
        print ("Nb Gates: ", self.nb_gates)

        image_desc = M2K_GetTFMDesc(self.m2m_system.socket,0)

        self.image_horiz_step = image_desc[0][12]
        self.image_vert_step = image_desc[0][13]

        self.image_width = image_desc[1][0]
        self.image_heigth = image_desc[1][1]

        print ("image width (pixel) ", self.image_width , "x (mm) ",self.image_horiz_step, "Image Heigth (pixel) ", self.image_heigth," x (mm) ",self.image_vert_step)

        # restart sequencer. MANDATORY IF STOPPED BEFORE
        M2K_WriteAndStartHard(self.m2m_system.socket)

    def action_raz(self):
        for i in range(1,8):
            self.m2m_system.raz_encoder(i)

    def action_set_ref(self):
        TFM = M2K_GetTFMImage(self.m2m_system.socket,0)
        self.Mem_TFM=TFM

    def action_start(self):
        if self.m2m_system.connected != True:
            print ("Connect M2M system Before !!")
            return 0

        #######################################################
        # try to connect to the data server

        self.m2m_system.data_server_socket = M2mSocket()
        self.m2m_system.connect_data_server()

        #    m2m_system.data_server_socket.sock.setblocking(False)
        if self.m2m_system.data_server_connected != True:
            print ("Connect data_server M2M system Before !!")
            return 0

        if self.start_acqui == 0:
            # self.champ_label.update
            #self.m2m_system.raz_encoder(1)
            #self.m2m_system.raz_encoder(2)
            self.total_packets=0
            self.total_read_size=0
            self.nb_of_cycles+=1
            self.tstart=time.perf_counter()
            self.m2m_system.start_acqui()
            self.tstart=time.perf_counter()-fenetre.tstart
            print ("Temps start: ", self.tstart)
            self.start_time=time.perf_counter()
            self.start_acqui = 1
            self.demande_stop=False
            self.wait_for_acqui = True
            texte = ("Cycle(s) Acqui : " + str(self.nb_of_cycles))
            self.Texte_Affiche_Etape.set(texte)

        self.update()
        plt.ion()


    def action_stop(self):
        fenetre.demande_stop=True
        ##if self.start_acqui:
        #    self.m2m_system.stop_acqui()
        #    self.start_acqui = 0
        #    self.next_start_acqui=1e24

def check_presence():
    global fenetre, Fifo, Out_Excel, Verrou, Num_etape, Etapes, Counter_cycle,Counter_piece

    #codeur = fenetre.m2m_system.get_current_value_coder(1)
    #texte = "codeur:" + str(codeur)
    #fenetre.Texte_Affiche_Codeur.set(texte)
    if fenetre.start_acqui :
        time_acqui=time.perf_counter()-fenetre.start_time
        texte = "Time Acqui : " + '%10.2f' % (time_acqui)
        fenetre.Texte_Affiche_Temps.set(texte)

        fenetre.x = 30 * cos(2*pi*(time_acqui-15) / 60.0)+100
        fenetre.y = 30 * sin(2*pi*(time_acqui-15) / 60.0)+100
        fenetre.zone_dessin.coords(fenetre.ligne,100,100,fenetre.x,fenetre.y)
        #fenetre.zone_dessin.create_line(100,100,fenetre.x,fenetre.y,width=3,arrow=tkinter.LAST) #Dessine une ligne en diagonale
        fenetre.zone_dessin.update()
        fenetre.acqui_en_cours=fenetre.m2m_system.is_acquisition_running()

        if fenetre.wait_for_acqui == True:
            if time_acqui>15:
                # if acquisition have not started 15 seconds after --> stop
                print ("Time out, acquisition not started")
                fenetre.demande_stop=True
                fenetre.start_acqui=0
            else:
                print ("Acquisition started OK")
                if fenetre.acqui_en_cours == True:
                    fenetre.wait_for_acqui = False
        else:
            if fenetre.acqui_en_cours == True:
                #print "Acqui, demande_stop"+str(fenetre.demande_stop)
                M2M_Acqui(fenetre.m2m_system)
            else:
                print ("end acqui detected")
                fenetre.demande_stop=True
                fenetre.m2m_system.disconnect_data_server()

        if (fenetre.demande_stop == True):
            print ("Demande Stop Vue")
            if fenetre.acqui_en_cours:
                fenetre.m2m_system.disconnect_data_server()
                print ("stop acqui")
                fenetre.m2m_system.stop_acqui()
            #print "check if there is data to read"
            #M2M_Acqui(fenetre.m2m_system, fenetre, fenetre.gate_cscan)
            new_2D_image = numpy.vstack(fenetre.stacked_max_values)
            new_2D_image=numpy.rot90(new_2D_image)
            # Display the new 2D image
            plt.imshow(new_2D_image, cmap="rainbow", aspect="auto")
            plt.colorbar(label="Max Intensity")
            plt.title("Cscan 2D Image from Column Max Values")
            plt.xlabel("Column Index")
            plt.ylabel("Image Index")
            plt.show()
            
            max_curve = np.max(new_2D_image, axis=0)

            # Plot the 1D curve
            plt.figure(figsize=(10, 4))
            plt.plot(max_curve, color="blue", linewidth=2, label="Max Value per Column")
            plt.xlabel("Column Index")
            plt.ylabel("Max Intensity")
            plt.title("1D Curve: Maximum Value per Column")
            plt.legend()
            plt.grid()
            plt.show()
            fenetre.start_acqui = False
            fenetre.demande_stop=False
            fenetre.acqui_en_cours=False

    else:
        TFM = M2K_GetTFMImage(fenetre.m2m_system.socket,0)
        TFM=TFM-fenetre.Mem_TFM
        fenetre.image.set_array(TFM)
        #TFM_float=TFM.astype(float)
        #edges=filters.sobel(TFM_float)
        #io.imshow(edges)
        #io.show()
        plt.draw()
        plt.show(block=False)

        #fenetre.zone_dessin.update()



    #fenetre.action_start()

    fenetre.after(100,check_presence)


#--------------------------------------------------
def M2M_Acqui(m2m_system):

    #print "m2m_system.nb_mechanical_positions", str(m2m_system.nb_mechanical_positions)
    if fenetre.acqui_en_cours > 0:
        ##### Acquisition has started OK
        ##### print "M2000 Has started acquisition"
        ##### read synchronization tag
        #print "read tag"
        buffer = m2m_system.data_server_socket.M2MReceive(4)
        if buffer== "":
            #print "no data"
            return 0

        synchronization = int(struct.unpack('>i', buffer)[0])
        ##### If synchronization tag is correct
        if synchronization == 0x7EFDFCFB:
            ###### read number of packets to receive
            buffer = m2m_system.data_server_socket.M2MReceive(4)
            number_of_packets = int(struct.unpack('>i', buffer)[0])
            ###### loop on packets
            if number_of_packets>0:
                #print "packets:", number_of_packets
                for packet in range (0, number_of_packets):
                    fenetre.total_packets += 1
                    ###### read total size of all data
                    buffer = m2m_system.data_server_socket.M2MReceive(4)
                    total_packet_size = int(struct.unpack('>i', buffer)[0])
                    fenetre.total_read_size+=total_packet_size
                    if total_packet_size>0:
                        #print "packet to read",total_packet_size
                        ### loop for each salvo, sequence...
                        for salvo in range(fenetre.Nb_Salvos):
                            for seq in range (0,fenetre.nb_sequences):
                                for shot in range(0, fenetre.nb_shots):
                                    #### read the synchronization tag
                                    buffer = m2m_system.data_server_socket.M2MReceive(4)
                                    synchronization = int(struct.unpack('>i', buffer)[0])
                                    if synchronization == 0x7BFDFCFB:
                                        ####read mechanical position
                                        for meca in range (0,fenetre.nb_mechanical_positions):
                                            buffer = m2m_system.data_server_socket.M2MReceive(4)
                                            position = float(struct.unpack('<f', buffer)[0])
                                            #print "position ", position
                                        #endfor meca positions

                                        if fenetre.inputs_available:
                                            inputs_data = m2m_system.data_server_socket.M2MReceive(16)
                                            #print "inputs"
                                        #endif

                                        ####loop on each gate, echo (in case of multi peak gate)...
                                        for gate in range (0,fenetre.nb_gates):
                                            if (fenetre.is_gate_store_TFM) and (seq==(fenetre.nb_sequences-1)) and (shot == (fenetre.nb_shots-1)):
                                                buffer = m2m_system.data_server_socket.M2MReceive(4)
                                                image_size = int(struct.unpack('>i', buffer)[0])
                                                if image_size==2080242939:
                                                    print ("error: image size = TAG")

                                                elif image_size>0:
                                                    #print ("image size",image_size)
                                                    buffer=m2m_system.data_server_socket.M2MReceive(image_size)
                                                    image_TFM = numpy.frombuffer(buffer[0:image_size],dtype=numpy.dtype("<i"))
                                                    image_TFM = image_TFM.reshape(fenetre.image_heigth,fenetre.image_width)
                                                    image_TFM = image_TFM -fenetre.Mem_TFM
                                                    max_per_column = numpy.max(image_TFM, axis=1)
                                                    fenetre.stacked_max_values.append(max_per_column)    
                                                    fenetre.image.set_array(image_TFM)
                                                    plt.draw()

                                                    #print image
                                                else:
                                                    print ("Error image size =< 0",image_size)

                                            #endfor echoes

                                        #endfor gates
                                    else:
                                        print ("Mechanical Synchronization tag incorrect: STOP")
                                        fenetre.demande_stop = True
                                    #endif
                                #endfor shots
                            #endfor sequences
                        #endfor packets
                    else:
                        print ("data size = 0")
                        fenetre.demande_stop = True
                    sys.stdout.write("Packets read: %6d Amount read: %3.3f Mbytes\r"% (fenetre.total_packets,fenetre.total_read_size/1024.0/1024.0))
                    sys.stdout.flush()

                    #endif
            else:
                print ("No packets to read !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!: ",number_of_packets)
                #fenetre.demande_stop = True
            #endif
        else:
            print ("Frame Synchronization tag incorrect: STOP")
            fenetre.demande_stop = True
        #endif


################################################################################################


fenetre = mon_ihm(None)
fenetre.title("M2M get TFM Application")



#    fenetre.willdispatch
# On demarre la boucle tkinter qui s'interompt quand on ferme la fenetre

fenetre.after(50,check_presence)

fenetre.mainloop()

