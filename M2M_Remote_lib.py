# -*- coding: utf8 -*-

from socket import *
from string import *

import time

import os
import array
import unittest
import struct
import inspect
import binascii
import win32com.client
import numpy
import numpy as np

################################################################################
########### Class definition which define available data in a gate #############

class Cgate:
    def __init__(self):
        self.salvo_of_gate = 0

        self.nb_echo_in_gate = 0
        self.is_gate_store_sum = 0
        self.is_gate_store_elem = 0
        self.is_gate_store_ad = 0
        self.nb_data_in_gate = 0
        self.is_gate_shot_by_mode = 0
        self.nb_data_peak=0
        # one gate have several results (as time, amp ...), index is the Salvo
        self.data_type_in_gate = []

        self.data_size_in_gate = []
        # name of the data (Example : Amplitude Gate 1
        self.data_description = []


##############################################################################
################# Class definition which define dac parameters ###############
class Cdac:
    def __init__(self):
        self.type = 0
        self.nb_of_points = 0
        # create list of DAC segments
        self.positions = []
        self.gains = []

        self.xls_line_gain = 0
        self.xls_col_gain = 0
        self.xls_line_pos = 0
        self.xls_col_pos = 0
        self.xls_line_nb_points = 0
        self.xls_col_nb_points = 0

    # method to add a point in a DAC curve
    def add_point(self, position, gain):
        self.gains.append(gain)
        self.positions.append(position)
        self.nb_of_points += 1


##############################################################################
############ Class definition which define shot parameters ###################
class Cshot:
    def __init__(self):
        self.nb_elements_trans = 0
        self.nb_elements_recep = 0
        self.shot_number = -1

        self.xls_elements_trans = 0
        # create list which store transmission element of the shot
        self.elements_trans = []

        self.xls_delay_trans = 0
        # create list which store reception element of the shot
        self.delay_trans = []

        self.xls_elements_recep = 0
        self.elements_recep = []
        self.xls_delay_recep = 0
        self.delay_recep = []

        # create DAC object of the shot. There can be a common DAC on a salvo but also a different DAC for each shot (selectable by user)
        self.digital_dac = Cdac()


##############################################################################
############# Class definition which define sequence parameters ##############
class Csequence:
    def __init__(self):
        self.nb_shots = 0
        # create list of the shots in the sequence
        self.shots = []
        self.num_shot = -1

    # method to add a shot in the list on the sequence object
    def add_shot(self):
        self.shots.append(Cshot())
        self.shots[self.nb_shots].num_shot = self.nb_shots
        self.nb_shots = +1


##############################################################################
############# Class definition which define salvo parameters  ################
class Csalvo:
    def __init__(self):

        # create the list of the sequences in the salvo
        self.sequences = []
        self.nb_sequences = 0

        self.total_shots = 0
        # create the sequence in the object salvo
        self.gate_dac = Cdac()
        self.num_sequence = 0

        self.nb_gates = 0
        self.gates = []

    def add_sequence(self):
        self.sequences.append(Csequence())
        self.sequences[self.nb_sequences].num_sequence = self.nb_sequences
        self.nb_sequences += 1

    def __print__(self):
        print ("nb_sequences :", self.nb_sequences)


####################################################################################
####### Class definition which define generic parameters with their specificity ####
####### This class is used on automatic GUI interface to simplify coding of example
class M2mParameter:
    def __init__(self, order_name, unit, num_order, min, max):
        # list of parameters which depends on channel (channel # must be transmitted as a parameter)
        By_Channel = [2, 3, 4, 5, 18, 4, 6, 14, 17]

        # list of parameters which depends on salvo (salvo # must be transmitted as a parameter)
        By_Salvo = [7, 9, 10, 11, 13, 15]

        # list of parameters which depends on reconstruction (reconstruction # must be transmitted as a parameter). Used in parallel mode (MX++)
        By_Reconstruction = [4, 6, 14, 17]

        # list of parameters which are "read only"
        ##Is_Not_Writable=[16,19]
        Is_Not_Writable = [5, 6, 12, 13, 14, 16, 19]

        # store characteristics of the parameter
        self.order_name = order_name
        self.unit = unit
        self.num_order = num_order

        self.min = min
        self.max = max

        # for parameters who depends on
        self.salvo_number = 0
        self.sequence_number = 0
        self.shot_number = 0
        self.channel_number = 0
        self.sequence_rec_number = 0
        self.signal_rec_index = 0
        self.is_multiple_reconstruction = 0

        self.actual_value = 0

        if num_order in By_Channel:
            self.by_channel = True
        else:
            self.by_channel = False

        if num_order in By_Salvo:
            self.by_salvo = True
        else:
            self.by_salvo = False

        if num_order in By_Reconstruction:
            self.by_reconstruction = True
        else:
            self.by_reconstruction = False

        if num_order in Is_Not_Writable:
            self.writable = False
        else:
            self.writable = True

        if num_order == 9 or num_order == 10:
            self.two_parameters = True
            self.return_size = 4 + 8
        elif num_order == 17 or num_order == 18:
            self.return_size = 8
        else:
            self.return_size = 8

        #        print self.num_order, self.order_name,self.by_channel, self.return_size,self.writable

    # standard method whitch get value from M2000 SW
    def Get_Value(self, socket):
        self.actual_value = M2K_Get_Parameter(socket, self)
        return self.actual_value

    # standard method whitch set value from SW
    def Set_Value(self, socket, value):
        retour = M2K_Set_Parameter(socket, self, value)

        #if int(retour[0])==0:
        self.actual_value = value
        return retour

##############################################################################
##### List of the generic parameters for displaying in the menu ##############

M2m_Name_Liste_Param = ["Voltage", "Sampling_Frequency", "Pulse_Width", "Transmission_Delay",
                        "Reception_Delay", "Transmission_Enabled", "Channel_By_Channel_Gain",
                        "Numerical_Gain", "PRF", "Digitilizing_Delay", "Digitilizing_Length", "Rectified",
                        "Average_sum", "Synchro_Display", "Reception_Enabled", "General_Gain", "PRF_Low_Limit",
                        "Reception_Element_Number", "Transmission_Element_Number", "PRF_High_Limit"]

##############################################################################
###### List of the different M2M devices in function of returned number ######
M2m_Connected_Types = ["PCI V1", "PCI V2", "Full // 64 Channels", "M2000 Compact System", "Pocket 8x32", "LW System",
                       "Pocket 16x64", "Eddy Current System", "LW System 64", "Pocket // 32", "Multix++ 128 Channels",
                       "MultiX++ 256 Channels", "Eddy Current System 128", "Wave Master","New 1","New 2","New 3","Panther parallel","Panther 1:4","Panther 1:2"]

##############################################################################
#### list of data_type in gate
M2m_Gate_Data_Types = ["short", "float", "int", "char", "double"]

##############################################################################
M2M_Specimen_Types =  ["Plane", "Cylinder", "Cone", "Sphere", "Elbow", "Nozzle","2D CAO","3D CAO", "Fastened plate", "Section Transition", "Blade Groove","Blade root", "TWP", "Weld", "EPR Cover"]

########################################################################################
####### Class used as "define" to enumerate the actions ################################
####### not all the actions are defined and not all are interfaced in the example ######
####### please refer to the documentation "ServerTcpIp_Dslxxxx #########################
Time_Out_Socket = 2

class M2mRemoteOrders:
    def __init__(self):
        self.LoadConfiguration = 100
        self.GetNameOfTheConfiguration = 110
        self.ShowReglage = 111
        self.LoginPreparator = 131
        self.LoginOperator = 143
        self.GetParameter = 114  # To use with M2mParameter
        self.GetMulti2000Version = 133
        self.GetHardwareConnectedType = 168
        self.SetParameter = 113  # To use with M2mParameter
        self.SetParameterAcceptance = 166  # To use with M2mParameter !!Prefer this!
        self.GetHardwareMaxNbChannels = 182
        self.IsMultipleReconstruction = 193
        self.IsAllDatasAcquired = 412

        self.ExitApplication = 186
        self.ExcuteFile = 199
        self.GoodBye = 109
        self.GetStatusOrError = 105

        self.GetNbSystemConnected = 1230  # Multi systems
        self.GetSystemProperty = 1231
        self.SetSystemProperty = 1232
        self.GetSystemState = 1257

        self.GetNbSalvos = 101
        self.GetNbSequences = 102
        self.GetNbShots = 103
        self.GetNbChannelsReception = 104
        self.GetNameOfTheConfiguration = 110
        self.GetNbChannelsTransmission = 1207

        self.GetDacState = 123
        self.GetDacNbPoints = 124
        self.GetDacPositions = 125
        self.GetDacGains = 126
        self.SetDacPositions = 129
        self.SetDacGains = 130
        self.GetDacSynchro = 138

        self.GetGateDacCommonGainAfter = 1275
        self.SetGateDacCommonGainAfter = 1276
        self.GetGateDacIndependantGainAfter = 1277
        self.SetGateDacIndependantGainAfter = 1278

        self.SetDataPositioningServerSendAlwaysAD = 1217

        # New after 1.3.8 TFM
        self.IsGateStoreTFM = 246
        self.GetTFMMode = 1241
        self.GetTFMDesc = 1273
        self.GetTFMImage =1274
        self.SetGateStoreMode =245

        self.SetReceptionDelay = 1258
        self.GetReceptionDelay = 1259

        self.SetDigitGainDelta = 1260
        self.GetProbeBalancing = 1261
        self.SetProbeBalancing = 1262
        self.SetDacNumCommon = 1229
        self.SetDacCurve = 1271

        self.GetCoeffPtToMicroSec = 1247
        self.GetDynamicAmplitude = 1255

        self.SaveAcquisition = 142
        self.SaveConfiguration = 116

        self.AddDacPoint = 162
        self.RemoveDacPoint = 163
        self.SetDacState = 164
        self.SetDacSynchro = 165
        self.SetDacSynchroValue = 169

        self.EndOfMulti2000Initialisation = 170
        self.GetSequencesBuildNb = 187 # salvo, sequence, shot => seq nnumber
        self.GetShotsBuildNb = 188 #  salvo, sequence, shot, rec seq => shot number

        self.GetStartGateMs = 211
        self.GetWidthGateMs = 212
        self.GetGateName = 237

        self.GetLinkedSalvoes = 243 # to know which parameter is linked between two salvoes.

        self.SetCurrentAscanDisplay = 242

        self.GetSelectedDacActions = 178
        self.SetSelectedDacActions = 179
        self.SetGateDacGainAfter = 1235
        self.GetDacGateGainAfter = 1236
        self.StopHardAndNoWrite = 32753
        self.WriteAndStartHard = 32754
        self.GetNbOctetReadyForFifo = 32724

        self.GetNbMechanicalPositions = 300


        self.SetReceptionElement = 1268
        self.GetReceptionElement = 1266
        self.GetTransmissionElement = 1267
        self.SetTransmissionElement = 1269


        self.GetIncrementalStep = 301
        self.GetScanningStep = 302

        self.SetIncrementalStep = 303
        self.SetScanningStep = 304

        self.GetIncrementalBegin = 305
        self.GetIncrementalEnd = 307

        self.GetScanningBegin = 306
        self.GetScanningEnd = 308

        self.RazEncoder = 310
        self.RazEncoderSync = 419
        self.GetCurrentValueCoder = 311
        self.GetNbCartoPositionAcqui = 312
        self.GetNbCodeursSupAcqui = 313
        self.GetIndiceDuringAcqui = 314

        self.SetResolutionCoder = 317
        self.SetOffsetCoder = 318
        self.SetModuloCoder = 331

        self.SetIncrementalBegin = 322
        self.SetScanningBegin = 323
        self.SetIncrementalEnd = 324
        self.SetScanningEnd = 325

        self.GetIncrementalAxis = 342
        self.GetScanningAxis = 338

        self.SetMovementSpeedTrajectory = 348

        self.GetImageFromView = 414
        self.GetDataFromView = 415
        self.ListViews = 416


        self.SetEncoderStorage = 357
        self.SetRobot = 356
        self.GetTransformerProperty = 355
        self.SetTransformerProperty = 354
        self.GetCursorProperties = 1218

        # new 1.3.8
        self.GetSalvoOffset = 358
        self.SetSalvoOffset = 359


        self.SetAcquiEndAuto=353
        self.SetScanningOrientation = 361

        self.StartAcquisition = 400
        self.StopAcquisition = 401
        self.PauseTransfert = 402
        self.RepriseTransfert = 403
        self.IsErrorToStartAcquisition = 409

        self.IsAcquisitionRunning = 411
        self.ResetAllDataAcquired = 413

        self.GetImageFromView = 414
        self.ListViews = 416

        self.PauseHardwareAcqui = 424
        self.RepriseHardwareAcqui = 425

        # new 1.3.8
        self.LoadAcqScreen = 432
        self.SetAcqScreen = 433

        self.LoadGate = 247

        self.ResetAcquisition = 434

        self.SetAnalogueGainDuringAcquisition = 422
        self.GetAscanInt = 1237
        self.GetAllAscansElementaryInt = 1240
        self.GetAllAscansElementary = 183

        self.GetAscan = 115
        self.GetAllAscans = 117

        self.GetNbGates = 200
        self.GetNbEchoInGate = 201
        self.IsGateStoreSum = 202
        self.IsGateStoreElem = 203
        self.IsGateStoreAD = 204
        self.GetNbDatasInGate = 205
        self.GetDataTypeInGate = 206
        self.GetDataSizeInGate = 207
        self.GetDataDescription = 208
        self.IsGateSynchroStart = 209

        self.GetCurrentAmplitudeGate = 213
        self.GetCurrentDistanceGate = 214
        self.GetCurrentADGate = 229
        self.GetHeightGatePcent = 215
        self.SetStartGateMs = 221
        self.SetWidthGateMs = 222
        self.SetHeightGatePcent = 223
        self.SetGateSynchroStart = 227

        self.IsGateShotByShotMode = 230
        self.SetGateShotByShotMode = 244

        self.GetDacState = 123
        self.GetInputs = 119
        self.GetInputsAvailable = 121
        self.GetInputsTension = 185
        self.SetQuietMode = 134

        self.GetBufferizedAlarmSoftState = 1246
        self.GetBufferizedAlarmSoftPosition = 1254

        self.GetDDFSegmentsNb = 1249
        self.SetDDFSegmentsDelays = 1252
        self.GetDDFSegmentsDelays = 1253
        self.SetDDFSegmentsWindow = 1250
        self.GetDDFSegmentsWindow = 1251


        #Civa
        self.ComputeCivaLaws = 4022
        self.GetBeamSteeringParam = 4018
        self.SetVelocity = 4024

        #self.GetConﬁgurationDirection = 128

        self.GetCylindricalDimension = 4004
        self.GetAnglesDeviationSetting = 1209
        self.GetDirectionDepthParam = 4020
        self.GetInnerRadiusIfPieceCylinder = 176
        self.GetMaterialVelocity = 127
        self.GetMinMaxAreaRange = 1208
        self.GetPlanarDimension = 4002
        self.GetProbePosition = 120
        self.GetSectorialScanningDepthParam = 4012
        self.GetSectorialScanningParam = 4010
        self.GetSectorialScanningSoundPathParam = 4014
        self.GetSinglePointFocusingParam = 4016
        self.GetSpecimenType = 4000
        self.GetThicknessIfPieceCylinder = 177
        self.GetTransmissionEqualsReception = 4008
        self.GetTypeFocalisation = 4006
        self.GetTypeOfWave = 158
        self.GetVirtualProbePosition = 1224
        self.GetWedgeSpeed = 149


        self.SetBeamSteeringParam = 4019
        self.SetCylindricalDimension = 4005
        self.SetDirectionDepthParam = 4021
        self.SetPlanarDimension = 4003
        self.SetSectorialScanningDepthParam = 4013
        self.SetSectorialScanningParam = 4011
        self.SetSectorialScanningSoundPathParam = 4015
        self.SetSinglePointFocusingParam = 4017
        self.SetSpecimenType = 4001
        self.SetTransmissionEqualsReception = 4009
        self.SetTypeFocalisation = 4007
        # new 1.3.8
        self.SetVelocity = 4024
        self.GetVelocity = 4023

        self.ReportOpenDialogBox  = 5000
        self.ReportGeneration = 5001
        self.ReportCloseDialogBox = 5002

        self.SetSocketTimeOut = 10001
        self.GetSocketTimeOut = 10002

        self.SynchroKeyWord = 0xFA5A

########################################################################################################
### remote action enumeration instantiation for use in the functions later as a common variable ########
M2mRemoteOrder = M2mRemoteOrders()

#########################################################################################################
##### class definition used as define for sub-action properties for each connected device ###############
##### See M2K_GetSystemProperty
class M2mSystemProperties:
    def __init__(self):
        self.SerialNumber = 0
        self.Name = 1
        self.IsHdAutorized = 2
        self.IndexFirstInput = 3
        self.IndexFirstOutput = 4
        self.IsDefaultDevice = 5
        self.IsMasterDevice = 6
        self.IsDeviceSynchronized = 7
        self.DeviceType = 8

##################################################
### class instantiation for global use ###########
M2mSystemProperties = M2mSystemProperties()

###################################################
### class used as define for dac actions ##########
class M2MDacActionSetClass:
    def __init__(self):
        self.GateDac = -4
        self.DigitalDacDetail = -3      # parameter Salvo id number, Seq id number, Shot id number, Rebuild sq id number, Rebuild Shot id number
        self.AnalogDacPerSalvo = -2     # parameter Salvo id number
        self.AnalogDacAllSalvoes = -1
        self.DigitalDacSalvo = 0        #add salvo number  (start from 0)

##################################################
### class instantiation for global use ###########
M2MDacActionSet = M2MDacActionSetClass()

##############################################################################
##### class for socket connection ############################################
class M2mSocket:
    '''demonstration class only
	  - coded for clarity, not efficiency
	  - used for remote and data_server
	'''

    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket(
                AF_INET, SOCK_STREAM)
        else:
            self.sock = sock

        #### secure mode helps to check coherence in exchanges. Implemented only after version 8.4 as an option
        self.M2000_Remote_Secure_Mode = 0
        self.time_out=Time_Out_Socket

    # connect using standard socket libraries, IP depends on PC where M2000 is installed and port is defined in M2000 SW in "remote" GUI
    # if the PC is the same between user SW and M2000 SW, IP must be set as 127.0.0.1 (dummy IP adress used for internal communications)
    def connect(self, host, port):
        print ("connect at :", host, " : ", port)
        retour = self.sock.connect((host, port))
        self.time_out=120
        return retour

    # send data of the message until end using standard socket libraries
    def M2mSend(self, msg):
        #print ("send:")
        #bytevalues=list(msg)
        #print(bytevalues)

        totalsent = 0
        while totalsent < len(msg):
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent


    def M2mSecureReceive(self, expected_size):
        """

        :rtype : int
        """
        retour = self.M2MReceive(2)
        tag = int(struct.unpack('>H', retour)[0])
        if  tag != M2mRemoteOrder.SynchroKeyWord:
            print ("M2M Secure Receive error: incorrect tag",str(tag))
            self.return_status =  -1
            return -1

        retour = self.M2MReceive(4)
        self.return_size = int(struct.unpack('>i', retour)[0])


        #print "return size : ",self.return_size

        #if self.return_size == 51:
        #    self.return_size=704700
        #    print "return size modified for GetDataFromView",self.return_size

        retour = self.M2MReceive(2)

        ##############################
        # STATUS_OK = 0
        # STATUS_ERR = -1
        # STATUS_ERR_PARAM_SIZE = -2
        # STATUS_TIME_OUT_READ = -100
        # STATUS_TIME_OUT_WRITE = -101
        self.return_status = int(struct.unpack('>h', retour)[0])
        self.return_size -= 2
        if self.return_size > 0:
            self.retour=self.M2MReceive(self.return_size)
        else:
            self.retour=""

        if expected_size >= 0:
            if self.return_size != expected_size:
                print ("Error: expetced size = ", expected_size, "received size = ", self.return_size)
                self.return_status =  -2

        return self.return_status

    # receive data from the socket using standard socket libraries
    # user must send size of incoming message.
    # SW will leave function when all data received
    # if user doesn't want to be blocked, a specific thread must be created and managed

    def M2MReceive(self, MSGLEN):

        time_out=time.perf_counter()+self.time_out
        chunks = []
        bytes_recd = 0
        while bytes_recd < MSGLEN:
            try:
                chunk = self.sock.recv(min(MSGLEN - bytes_recd, 2048))
                if chunk == '':
                    raise RuntimeError("socket connection broken")
                chunks.append(chunk)
                bytes_recd = bytes_recd + len(chunk)
            except:
                if time.perf_counter()>time_out:
                    return b''.join(chunks)
            if time.perf_counter()>time_out:
                return b''.join(chunks)
        #bytevalues=list(b''.join(chunks))
        #print ("receive:")
        #print(bytevalues)
        return b''.join(chunks)

    def M2MSendSingleShort(self,short_value):
        self.M2mSend(struct.pack(">h",short_value))

    def M2MSendSingleUnsignedShort(self,short_value):
        self.M2mSend(struct.pack(">H",short_value))

    def M2MSendSingleInt(self,int_value):
        self.M2mSend(struct.pack(">i",int_value))

    def close(self):
        self.sock.close()
        print ("Socket M2M closed")


##############################################################################
# This action do the same thing that user can do by "login in" on the start of the SW
def M2K_login_preparator(clientsocket):
    # M2mRemoteOrder is the list of orders numbers
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:
        clientsocket.M2MSendSingleUnsignedShort(M2mRemoteOrder.SynchroKeyWord)
        clientsocket.M2MSendSingleShort( M2mRemoteOrder.LoginPreparator)
        clientsocket.M2MSendSingleInt( int(0))
        clientsocket.M2mSecureReceive(0)
        # print "Secure status : ",clientsocket.return_status
    else:
        # create in the "a" variable a byte message with the order translated in binary big-indian standard
        a = struct.pack('>h', M2mRemoteOrder.LoginPreparator)

        print ("Ordre ", binascii.hexlify(a), " Hexa")

        # send the message
        clientsocket.M2mSend(a)

##############################################################################
def M2K_GoodBye(clientsocket):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack(">Hhi", M2mRemoteOrder.SynchroKeyWord,M2mRemoteOrder.GoodBye,int(0))
        clientsocket.M2mSend(a)
    else:
        a = struct.pack('>h', M2mRemoteOrder.GoodBye)
        clientsocket.M2mSend(a)


##############################################################################
# parameter is a class M2M_Parameter. This function manage the "standard ultrasound parameters" like gain, pulse...
# it have been concatenated in a single function to be able to manage from a single API function
##############################################################################

def M2K_Get_Parameter(clientsocket, parameter):
    global M2mRemoteOrder

    # doesn't manage parameters #17 and 18
    if parameter.num_order == 18:
        if parameter.channel_number <= 0:
            parameter.channel_number = 1

    if parameter.num_order == 17:
        if parameter.channel_number <= 0:
            parameter.channel_number = 1

    if parameter.num_order == 5:
        if parameter.channel_number <= 0:
            parameter.channel_number = 1

    #    if parameter.num_order == 4:
    #        print "Delay R"


    if clientsocket.M2000_Remote_Secure_Mode:


        param_size=2
        if parameter.by_channel:
            param_size+=8
        if parameter.by_salvo:
            param_size+=2
        if parameter.by_reconstruction and parameter.is_multiple_reconstruction:
            param_size+=4

        # create a packed binary data in variable 'a' containning the parameters with correct type and length (big indian, h = signed 16 bits short, H = 16 bits unsigned short)
        a = struct.pack('>HhiH', M2mRemoteOrder.SynchroKeyWord,M2mRemoteOrder.GetParameter, int(param_size),parameter.num_order)
        #print parameter.order_name, " Get Param Ordre ", binascii.hexlify(a), " Hexa"
        clientsocket.M2mSend(a)


        if parameter.by_channel:
            #  Salvo number (short), sequence number (short), shot number (short), channel number (short).
            a = struct.pack('>hhhh', parameter.salvo_number, parameter.sequence_number, parameter.shot_number,
                            parameter.channel_number)
            clientsocket.M2mSend(a)

        if parameter.by_reconstruction and parameter.is_multiple_reconstruction:
            a = struct.pack('>hh', parameter.sequence_rec_number,parameter.signal_rec_index)
            clientsocket.M2mSend(a)

        if parameter.by_salvo:
            # Salvo number (short).
            a = struct.pack('>h', parameter.salvo_number)
            clientsocket.M2mSend(a)

        if clientsocket.M2mSecureReceive(parameter.return_size) ==0:

            # the return size is not the same for each parameter. description have been set in the order list
            # The sw read and decodes the returned value in function of data type (int, long, float...)
            if parameter.return_size == 16:
                retour = struct.unpack('>qd', clientsocket.retour)
            elif parameter.return_size == 12:
                retour = struct.unpack('>id', clientsocket.retour)
                retour = float(retour[1])
            elif parameter.return_size == 8:
                retour = float(struct.unpack('>d', clientsocket.retour)[0])
            else:
                retour = 0

            if (parameter.num_order == 4 ):
                retour = float(retour) / 1000.0
        else:
            print ("M2K_Get_Parameter Communication Socket Error: ", clientsocket.return_status)
            retour = 0
        #retour=binascii.hexlify(retour)

    else:

        send_sequence_number = 0

        # create a packed binary data in variable 'a' containning the parameters with correct type and length (big indian, h = signed 16 bits short, H = 16 bits unsigned short)
        a = struct.pack('>hH', M2mRemoteOrder.GetParameter, parameter.num_order)
        #print parameter.order_name, " Get Param Ordre ", binascii.hexlify(a), " Hexa"
        clientsocket.M2mSend(a)

        if parameter.by_channel:
            #  Salvo number (short), sequence number (short), shot number (short), channel number (short).
            a = struct.pack('>hhhh', parameter.salvo_number, parameter.sequence_number, parameter.shot_number,
                            parameter.channel_number)
            clientsocket.M2mSend(a)

        if parameter.by_reconstruction and parameter.is_multiple_reconstruction:
            a = struct.pack('>hh', parameter.sequence_rec_number,parameter.signal_rec_index)
            clientsocket.M2mSend(a)

        if parameter.by_salvo:
            # Salvo number (short).
            a = struct.pack('>h', parameter.salvo_number)
            clientsocket.M2mSend(a)

        # the return size is not the same for each parameter. description have been set in the order list
        # The sw read and decodes the returned value in function of data type (int, long, float...)
        if parameter.return_size == 16:
            retour = clientsocket.M2MReceive(16)
            retour = struct.unpack('>qd', retour)[0]
        elif parameter.return_size == 12:
            retour = clientsocket.M2MReceive(12)
            retour = struct.unpack('>id', retour)
            retour = float(retour[1])
        elif parameter.return_size == 8:
            retour = clientsocket.M2MReceive(8)
            retour = float(struct.unpack('>d', retour)[0])
        else:
            retour = 0

        if (parameter.num_order == 4 ):
            retour = float(retour[0]) / 1000.0

        #retour=binascii.hexlify(retour)


    return retour


###########################################################################
# parameter is a class M2M_Parameter This function manage the "standard ultrasound parameters" like gain, pulse...
# it have been concatenated in a single function to be able to manage from a single API function
##############################################################################
def M2K_Set_Parameter(clientsocket, parameter, value):
    global M2mRemoteOrder



    # if the parameter is "read only", do not do anything
    if parameter.writable != True:
        return False


    if parameter.num_order == 3:
        print ("set transmission delay")

    if parameter.num_order == 18:
        if parameter.channel_number <= 0:
            parameter.channel_number = 1

    if parameter.num_order == 17:
        if parameter.channel_number <= 0:
            parameter.channel_number = 1

    if parameter.num_order == 5:
        if parameter.channel_number <= 0:
            parameter.channel_number = 1



    if clientsocket.M2000_Remote_Secure_Mode:

        param_size=2+8
        if parameter.by_channel:
            param_size+=8
        if parameter.by_salvo:
            param_size+=2
        if parameter.by_reconstruction and parameter.is_multiple_reconstruction:
            param_size+=4


        a = struct.pack('>HhiH', M2mRemoteOrder.SynchroKeyWord, M2mRemoteOrder.SetParameterAcceptance, int(param_size), parameter.num_order)
        #print parameter.order_name, " Set Param Ordre ", binascii.hexlify(a), " Hexa, value: ", value
        clientsocket.M2mSend(a)

        if parameter.by_channel:
            #  Salvo number (short), sequence number (short), shot number (short), channel number (short).
            a = struct.pack('>hhhh', parameter.salvo_number, parameter.sequence_number, parameter.shot_number,
                            parameter.channel_number)
            clientsocket.M2mSend(a)


        if parameter.by_reconstruction and parameter.is_multiple_reconstruction:
            a = struct.pack('>hh', parameter.sequence_rec_number,parameter.signal_rec_index)
            clientsocket.M2mSend(a)

        if parameter.by_salvo:
            # Salvo number (short).
            a = struct.pack('>h', parameter.salvo_number)
            clientsocket.M2mSend(a)

        a = struct.pack('>d', float(value))
        clientsocket.M2mSend(a)

        if clientsocket.M2mSecureReceive(2) == 0:
            retour = struct.unpack('>h', clientsocket.retour)
        else:
            print ("M2K_Set_Parameter Communication Socket Error: ", clientsocket.return_status)
            retour = 0
        #retour=binascii.hexlify(retour)

    else:
        a = struct.pack('>hH', M2mRemoteOrder.SetParameterAcceptance, parameter.num_order)
        #print parameter.order_name, " Set Param Ordre ", binascii.hexlify(a), " Hexa, value: ", value
        clientsocket.M2mSend(a)

        if parameter.by_channel:
            #  Salvo number (short), sequence number (short), shot number (short), channel number (short).
            a = struct.pack('>hhhh', parameter.salvo_number, parameter.sequence_number, parameter.shot_number,
                            parameter.channel_number)
            clientsocket.M2mSend(a)

        if parameter.by_reconstruction and parameter.is_multiple_reconstruction:
            a = struct.pack('>hh', parameter.sequence_rec_number,parameter.signal_rec_index)
            clientsocket.M2mSend(a)

        if parameter.by_salvo:
            # Salvo number (short).
            a = struct.pack('>h', 0)
            clientsocket.M2mSend(a)

        a = struct.pack('>d', float(value))
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)
        retour = struct.unpack('>h', retour)

        #retour=binascii.hexlify(retour)
    return retour


##############################################################################
# interrogates M2000 sw to know if the current setting is "multiple reconstruction" type
# this is the case for full parallel shot where device shot only one time and compute virtual electronic
# scanning by calculation.

def M2K_IsMultipleReconstruction(clientsocket):
    global M2mRemoteOrder

    return M2K_GetParameterNoParamShortReturn(clientsocket, M2mRemoteOrder.IsMultipleReconstruction)


###################################################################################################
###################################################################################################
###### Theses following generic functions used in M2MSystem class for simple actions ##############
###### the name indicate the sent type and number of parameters and return type ###################
###################################################################################################

def M2K_GetParameterNoParamShortReturn(clientsocket, parameter_number):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:
        #if (parameter_number==401):
        #    print "envoie stop"

        a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord, parameter_number, int(0))
        clientsocket.M2mSend(a)

        #if (parameter_number==401):
        #    print "stop envoyé; attente retour"

        if clientsocket.M2mSecureReceive(2) == 0:
            retour = int(struct.unpack('>h', clientsocket.retour)[0])
        #    if (parameter_number==401):
        #        print "Retour OK"

        else:
            print ("M2K_GetParameterNoParamShortReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0
    else:

        a = struct.pack('>h', parameter_number)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)

        retour = int(struct.unpack('>h', retour)[0])


    return retour

##############################################################################

def M2K_GetParameterNoParamIntReturn(clientsocket, parameter_number):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:
        #if (parameter_number==401):
        #    print "envoie stop"

        a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord, parameter_number, int(0))
        clientsocket.M2mSend(a)

        #if (parameter_number==401):
        #    print "stop envoyé; attente retour"

        if clientsocket.M2mSecureReceive(4) == 0:
            retour = int(struct.unpack('>i', clientsocket.retour)[0])
        #    if (parameter_number==401):
        #        print "Retour OK"

        else:
            print ("M2K_GetParameterNoParamIntReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0
    else:

        a = struct.pack('>h', parameter_number)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(4)

        retour = int(struct.unpack('>i', retour)[0])


    return retour

##############################################################################

def M2K_GetParameterShortParamShortReturn(clientsocket, parameter_number, short_value):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhih', M2mRemoteOrder.SynchroKeyWord , parameter_number, int(2), short_value)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(2) == 0:
            retour = int(struct.unpack('>h', clientsocket.retour)[0])
        else:
            print ("M2K_GetParameterShortParamShortReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0
    else:
        a = struct.pack('>hh', parameter_number, short_value)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)

        retour = int(struct.unpack('>h', retour)[0])

    return retour

##############################################################################

def M2K_GetParameterShortParamDoubleReturn(clientsocket, parameter_number, short_value):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhih', M2mRemoteOrder.SynchroKeyWord , parameter_number, int(2), short_value)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(8) == 0:
            retour = float(struct.unpack('>d', clientsocket.retour)[0])
        else:
            print ("M2K_GetParameterShortParamDoubleReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0
    else:
        a = struct.pack('>hh', parameter_number, short_value)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(8)

        retour = float(struct.unpack('>d', retour)[0])

    return retour

##############################################################################

def M2K_SetParameterIntParamShortReturn(clientsocket, parameter_number, int_value):

    if clientsocket.M2000_Remote_Secure_Mode:
        sz = struct.pack('>Hhii',M2mRemoteOrder.SynchroKeyWord , parameter_number, int(4), int_value)
        clientsocket.M2mSend(sz)
        if clientsocket.M2mSecureReceive(2) ==0:
            retour = int(struct.unpack('>h', clientsocket.retour)[0])
        else:
            print ("M2K_SetParameterIntParamShortReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0
    else:
        a = struct.pack('>hi', parameter_number, int_value)
        clientsocket.M2mSend(a)
        retour = clientsocket.M2MReceive(2)

        retour = int(struct.unpack('>h', retour)[0])

    return retour

##############################################################################

def M2K_SetParameterNoParamNoReturn(clientsocket, parameter_number):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(0))
        clientsocket.M2mSend(a)
        clientsocket.M2mSecureReceive(0)
    else:
        a = struct.pack('>h', parameter_number)
        clientsocket.M2mSend(a)
##############################################################################

def M2K_SetParameterShortParamNoReturn(clientsocket, parameter_number, short_value):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhih', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(2), short_value)
        clientsocket.M2mSend(a)
        clientsocket.M2mSecureReceive(0)
    else:
        a = struct.pack('>hh', parameter_number, short_value)
        clientsocket.M2mSend(a)

##############################################################################

def M2K_SetParameterShortParamShortReturn(clientsocket, parameter_number, short_value):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhih', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(2), short_value)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(2) == 0:
            retour = int(struct.unpack('>h', clientsocket.retour)[0])
        else:
            print ("M2K_SetParameterShortParamShortReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_SetParameterShortParamShortReturn not managed unsecure mode")
        retour = 0

    return retour


##############################################################################

def M2K_SetParameterShortParamFloatParamNoReturn(clientsocket, parameter_number, short_value, float_value):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihf', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(2+4), short_value, float(float_value))
        clientsocket.M2mSend(a)
        clientsocket.M2mSecureReceive(0)
    else:

        a = struct.pack('>hhf', parameter_number, short_value, float(float_value))
        clientsocket.M2mSend(a)

##############################################################################

def M2K_SetParameterFloatParamNoReturn(clientsocket, parameter_number, float_value):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhif', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(4), float(float_value))
        clientsocket.M2mSend(a)
        clientsocket.M2mSecureReceive(0)
    else:
        a = struct.pack('>hf', parameter_number, float(float_value))
        clientsocket.M2mSend(a)


##############################################################################

def M2K_GetParameter2xShortParamShortReturn(clientsocket, parameter_number, short_value1, short_value2):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihh', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(2+2), short_value1, short_value2)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(2) == 0:
            retour = int(struct.unpack('>h', clientsocket.retour)[0])
        else:
            print ("M2K_GetParameter2xShortParamShortReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        a = struct.pack('>hhh', parameter_number, short_value1, short_value2)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)

        retour = int(struct.unpack('>h', retour)[0])

    return retour

##############################################################################

def M2K_GetParameter2xShortParamFloatReturn(clientsocket, parameter_number, short_value1, short_value2):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihh', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(2+2), short_value1, short_value2)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(4) == 0:
            retour = float(struct.unpack('>f', clientsocket.retour)[0])
        else:
            print ("M2K_GetParameter2xShortParamFloatReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        a = struct.pack('>hhh', parameter_number, short_value1, short_value2)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(4)

        retour = float(struct.unpack('>f', retour)[0])

    return retour

##############################################################################

def M2K_GetParameter2xShortParamShortReturn(clientsocket, parameter_number, short_value1, short_value2):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihh', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(2+2), short_value1, short_value2)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(2) == 0:
            retour = int(struct.unpack('>h', clientsocket.retour)[0])
        else:
            print ("M2K_GetParameter2xShortParamShortReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        a = struct.pack('>hhh', parameter_number, short_value1, short_value2)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)

        retour = int(struct.unpack('>h', retour)[0])

    return retour

##############################################################################

def M2K_GetParameter2xShortParam2xIntReturn(clientsocket, parameter_number, short_value1, short_value2):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihh', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(2+2), short_value1, short_value2)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(8) == 0:
            retour = struct.unpack('>ii', clientsocket.retour)
        else:
            print ("M2K_GetParameter2xShortParam2xIntReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_GetParameter2xShortParam2xIntReturn not managed in not seruce mode")
    return retour

##############################################################################

def M2K_GetParameter2xShort2xfloatParamShortReturn(clientsocket, parameter_number, short_value1, short_value2,float_value1,float_value2):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihhff', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(2+2+4+4), short_value1, short_value2,float(float_value1),float(float_value2))
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(2) == 0:
            retour = struct.unpack('>h', clientsocket.retour)
        else:
            print ("M2K_GetParameter2xShort2xfloatParamShortReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_GetParameter2xShort2xfloatParamShortReturn not managed in not seruce mode")
    return retour




##############################################################################

def M2K_SetParameter2xShortParamNoReturn(clientsocket, parameter_number, short_value1, short_value2):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihh', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(2+2), short_value1, short_value2)
        clientsocket.M2mSend(a)
        clientsocket.M2mSecureReceive(0)
    else:
        a = struct.pack('>hhh', parameter_number, short_value1, short_value2)
        clientsocket.M2mSend(a)

    return

##############################################################################

def M2K_SetParameter2xShortParamShortReturn(clientsocket, parameter_number, short_value1, short_value2):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihh', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(2+2), short_value1, short_value2)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(2) == 0:
            retour = int(struct.unpack('>h', clientsocket.retour)[0])
        else:
            print ("M2K_SetParameter2xShortParamShortReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0
    else:
        a = struct.pack('>hhh', parameter_number, short_value1, short_value2)
        clientsocket.M2mSend(a)
        retour = clientsocket.M2MReceive(2)
        retour = int(struct.unpack('>h', retour)[0])

    return

##############################################################################

def M2K_GetParameter3xShortParamShortReturn(clientsocket, parameter_number, short_value1, short_value2, short_value3):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihhh', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(2+2+2), short_value1, short_value2, short_value3)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(2) == 0:
            retour = int(struct.unpack('>h', clientsocket.retour)[0])
        else:
            print ("M2K_GetParameter3xShortParamShortReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        a = struct.pack('>hhhh', parameter_number, short_value1, short_value2, short_value3)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)

        retour = int(struct.unpack('>h', retour)[0])

    return retour


##############################################################################

def M2K_GetParameter4xShortParamShortReturn(clientsocket, parameter_number, short_value1, short_value2, short_value3, short_value4):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>HhihhhH', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(2+2+2+2), short_value1, short_value2, short_value3, short_value4)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(2) == 0:
            retour = int(struct.unpack('>h', clientsocket.retour)[0])
        else:
            print ("M2K_GetParameter4xShortParamShortReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        a = struct.pack('>hhhhh', parameter_number, short_value1, short_value2, short_value3, short_value4)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)

        retour = int(struct.unpack('>h', retour)[0])

    return retour


##############################################################################

def M2K_GetParameter5xShortParamShortReturn(clientsocket, parameter_number, short_value1, short_value2, short_value3,short_value4, short_value5):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihhhhh', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(2+2+2+2+2), short_value1, short_value2, short_value3,short_value4, short_value5)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(2) == 0:
            retour = int(struct.unpack('>h', clientsocket.retour)[0])
        else:
            print ("M2K_GetParameter5xShortParamShortReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        a = struct.pack('>hhhhhh', parameter_number, short_value1, short_value2, short_value3,short_value4, short_value5)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)

        retour = int(struct.unpack('>h', retour)[0])

    return retour

##############################################################################


def M2K_GetParameter3xShortParamLongReturn(clientsocket, parameter_number, short_value1, short_value2, short_value3):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihhh',M2mRemoteOrder.SynchroKeyWord , parameter_number, int(2+2+2), short_value1, short_value2, short_value3)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(8) == 0:
            retour = int(struct.unpack('>q', clientsocket.retour)[0])
        else:
            print ("M2K_GetParameter3xShortParamLongReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:

        a = struct.pack('>hhhh', parameter_number, short_value1, short_value2, short_value3)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(8)

        retour = int(struct.unpack('>q', retour)[0])

    return retour


##############################################################################

def M2K_GetParameterShortParamFloatReturn(clientsocket, parameter_number, short_value):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhih', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(2), short_value)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(4) == 0:
            retour = float(struct.unpack('>f',clientsocket.retour)[0])
        else:
            print ("M2K_GetParameterShortParamFloatReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:

        a = struct.pack('>hh', parameter_number, short_value)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(4)

        retour = float(struct.unpack('>f', retour)[0])

    return retour


##############################################################################

def M2K_GetParameterShortParam2xFloatReturn(clientsocket, parameter_number, short_value):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhih', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(2), short_value)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(8) == 0:
            retour = []
            offset = 0
            for i in range(0, 2):
                retour.append(float(struct.unpack('>f', clientsocket.retour[offset:offset+4])[0]))
                offset+=4

        else:
            print ("M2K_GetParameterShortParam2xFloatReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:

        a = struct.pack('>hh', parameter_number, short_value)
        clientsocket.M2mSend(a)

        retour=[]
        retours = clientsocket.M2MReceive(4)
        retour.append( float(struct.unpack('>f', retours)[0]))
        retours = clientsocket.M2MReceive(4)
        retour.append( float(struct.unpack('>f', retours)[0]))

    return retour

##############################################################################

def M2K_GetParameterFloatParamFloatReturn(clientsocket, parameter_number, float_value):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhif',M2mRemoteOrder.SynchroKeyWord , parameter_number, int(4), float_value)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(4) == 0:
            retour = float(struct.unpack('>f',clientsocket.retour)[0])
        else:
            print ("M2K_GetParameterFloatParamFloatReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:

        a = struct.pack('>hf', parameter_number, float(float_value))
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(4)

        retour = float(struct.unpack('>f', retour)[0])

    return retour

##############################################################################

def M2K_GetParameterShort4xFloatParamShortReturn(clientsocket, parameter_number, int_value, float_value1, float_value2, float_value3, float_value4):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihffff',M2mRemoteOrder.SynchroKeyWord , parameter_number, int(2+4+4+4+4), int_value, float_value1, float_value2, float_value3, float_value4)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(2) == 0:
            retour = float(struct.unpack('>h',clientsocket.retour)[0])
        else:
            print ("M2K_GetParameterShort4xFloatParamShortReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_GetParameterShort4xFloatParamShortReturn not managed unsecured mode")
        retour = 0

    return retour

##############################################################################

def M2K_GetParameterNoParamFloatReturn(clientsocket, parameter_number):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,parameter_number, int(0))
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(4) == 0:
            retour = float(struct.unpack('>f',clientsocket.retour)[0])
        else:
            print ("M2K_GetParameterNoParamFloatReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:

        a = struct.pack('>h', parameter_number)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(4)

        retour = float(struct.unpack('>f', retour)[0])

    return retour

##############################################################################

def M2K_GetParameterNoParamStringReturn(clientsocket,parameter_number):

    name=""
    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,parameter_number,int(0))
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(-1) == 0:
            stringsize=int(struct.unpack('>h',clientsocket.retour[0:2])[0])
            #return fist is length of string
            name = ""
            if stringsize > 0:
                name = clientsocket.retour[2:]
        else:
            print ("M2K_GetParameterNoParamStringReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0


    else:

        a = struct.pack('>h', parameter_number)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)
        retour = int(struct.unpack('>h', retour)[0])
        #return fist is length of string
        name = ""
        if retour > 0:
            name = clientsocket.M2MReceive(retour)

    return name

##############################################################################

def M2K_GetParameterStringParamStringReturn(clientsocket,parameter, string_name):

    name=""
    if clientsocket.M2000_Remote_Secure_Mode:
        u = bytes( string_name, "ascii" )
        a = struct.pack(">Hhih", M2mRemoteOrder.SynchroKeyWord ,parameter,int(2+len(u)),
                        len(u))  # transform the number in string format Big Indian
        #print "Ordre ", binascii.hexlify(a), " Hexa"
        clientsocket.M2mSend(a)  # send the message
        clientsocket.M2mSend(u)  # send the message

        time.sleep(0.1)


        if clientsocket.M2mSecureReceive(-1) == 0:
            stringsize=int(struct.unpack('>h',clientsocket.retour[0:2])[0])
            #return fist is length of string
            name = ""
            if stringsize > 0:
                name = clientsocket.retour[2:]
            return name
        else:
            print ("M2K_GetParameterStringParamStringReturn Communication Socket Error: ", clientsocket.return_status)
            return ""
    else:
        print ("M2K_GetParameterStringParamStringReturn Not implemented in non secure mode")

    return ""

##############################################################################

def M2K_GetParameter2xStringParamIntArrayReturn(clientsocket,parameter, string_name1,string_name2):

    name=""
    if clientsocket.M2000_Remote_Secure_Mode:


        u = bytes( string_name1, "ascii" )
        v = bytes( string_name2, "ascii" )

        a = struct.pack(">Hhih", M2mRemoteOrder.SynchroKeyWord ,parameter,int(4+len(u)+len(v)),
                        len(u))  # transform the number in string format Big Indian
        #print "Ordre ", binascii.hexlify(a), " Hexa"
        clientsocket.M2mSend(a)  # send the message

        clientsocket.M2mSend(u)  # send the message
        a = struct.pack(">h", len(v))  # transform the number in string format Big Indian
        clientsocket.M2mSend(a)  # send the message
        clientsocket.M2mSend(v)  # send the message

        time_out=time.time()+10
        ok=0
        while ok==0:

            if clientsocket.M2mSecureReceive(-1) == 0:
                stringsize=int(struct.unpack('>i',clientsocket.retour[0:4])[0])
                #print(stringsize)
                #return fist is length of array
                name = ""
                if stringsize > 0:
                    array = clientsocket.retour[4:]
                    ok = 1
                return array
            else:
                if time.time() > time_out:
                    print ("time out get array", clientsocket.return_status)
                    ok = 2
                    return ""
    else:
        print ("M2K_GetParameter2xStringParamStringReturn Not implemented in non secure mode")

    return ""



##############################################################################
##############################################################################

def M2K_GetParameter2xshortParamStringReturn(clientsocket,parameter_number,param1, param2):

    name=""
    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihh', M2mRemoteOrder.SynchroKeyWord ,parameter_number,int(4),param1,param2)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(-1) == 0:
            stringsize=int(struct.unpack('>h',clientsocket.retour[0:2])[0])
            #return fist is length of string
            name = ""
            if stringsize > 0:
                name = clientsocket.retour[2:]
        else:
            print ("M2K_GetParameter2xshortParamStringReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0


    else:

        a = struct.pack('>hhh', parameter_number,param1,param2)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)
        retour = int(struct.unpack('>h', retour)[0])
        #return fist is length of string
        name = ""
        if retour > 0:
            name = clientsocket.M2MReceive(retour)

    return name


##############################################################################
# send string parameter and read short status

def M2K_SetParameterStringParamShortReturn(clientsocket, parameter, string_name):


    if clientsocket.M2000_Remote_Secure_Mode:
        print (string_name)
        u = bytes( string_name, "ascii" )                    # transforme la chaine de caractere au format utf-8
        #u = string_name

        a = struct.pack(">Hhih", M2mRemoteOrder.SynchroKeyWord ,parameter,int(2+len(u)),
                        len(u))  # transform the number in string format Big Indian
        #print "Ordre ", binascii.hexlify(a), " Hexa"
        clientsocket.M2mSend(a)  # send the message
        clientsocket.M2mSend(u)  # send the message

        time.sleep(0.1)

        if clientsocket.M2mSecureReceive(2)==0:   # wait for return value (success or not)
            retour = int(struct.unpack('>h', clientsocket.retour)[0])
        else:
            print ("M2K_SetParameterStringParamShortReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        #u = unicode( config_name, "utf-8" )                    # transforme la chaine de caractere au format utf-8
        u = string_name
        #print "nom fichier ",binascii.hexlify(u), " en hexa / utf-8"
        a = struct.pack('>hH', parameter,
                        len(u))  # transform the number in string format Big Indian
        #print "Ordre ", binascii.hexlify(a), " Hexa"
        clientsocket.M2mSend(a)  # send the message
        clientsocket.M2mSend(u)  # send the message

        #time.sleep(0.1)

        retour = clientsocket.M2MReceive(2)  # wait for return value (success or not)

        retour=int(struct.unpack(">h",retour)[0])

        #print "retour ", binascii.hexlify(retour), " Hexa"

    return retour

def M2K_SetParameterShortStringParamShortStringReturn(clientsocket, parameter, short_param,string_name):

    if clientsocket.M2000_Remote_Secure_Mode:
        u = bytes( string_name, "ascii" )                    # transforme la chaine de caractere au format utf-8
        #u = string_name

        a = struct.pack(">Hhihh", M2mRemoteOrder.SynchroKeyWord ,parameter,int(2+2+len(u)),
                        short_param, len(u))  # transform the number in string format Big Indian
        #print "Ordre ", binascii.hexlify(a), " Hexa"
        clientsocket.M2mSend(a)  # send the message
        clientsocket.M2mSend(u)  # send the message

        time.sleep(0.1)

        if clientsocket.M2mSecureReceive(-1) == 0:
            short_return=int(struct.unpack('>h',clientsocket.retour[0:2])[0])
            stringsize=int(struct.unpack('>h',clientsocket.retour[2:4])[0])
            #return fist is length of string
            name = ""
            retour=short_return
            if stringsize > 0:
                string_ret = clientsocket.retour[4:]
                print(string_ret)

        else:
            print ("M2K_SetParameterShortStringParamShortStringReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print("SetParameterShortStringParamShortStringReturn not managed in unsecure mode")

    return retour


##############################################################################
# send 2xstring parameters+one short and read short status

def M2K_SetTransformerProperty(clientsocket, order_name, string_property, string_value, trajectory_index ):

    retour = 2
    if clientsocket.M2000_Remote_Secure_Mode:
        u = string_property
        v = string_value

        a = struct.pack(">Hhih", M2mRemoteOrder.SynchroKeyWord ,order_name,int(2+len(u)+2+len(v)+2),len(u))  # transform the number in string format Big Indian
        clientsocket.M2mSend(a)  # send the message
        clientsocket.M2mSend(u)  # send the message

        a = struct.pack(">h", len(v))  # transform the number in string format Big Indian
        clientsocket.M2mSend(a)  # send the message
        clientsocket.M2mSend(v)  # send the message

        a = struct.pack(">h", int(trajectory_index))  # transform the number in string format Big Indian
        clientsocket.M2mSend(a)  # send the message

        #time.sleep(0.1)

        if clientsocket.M2mSecureReceive(2)==0:   # wait for return value (success or not)
            retour = int(struct.unpack('>h', clientsocket.retour)[0])
        else:
            print ("M2K_SetTransformerProperty Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_SetTransformerProperty only managed in secure mode  by Demo SW")

    return retour


##############################################################################
# send open dialog box xstring parameters and read int status

def M2K_ReportOpenDialogBox(clientsocket, order_name, output_pdf_name, template_name, speciment_name, controler_name, pdf_path_name ):

    retour = 2
    if clientsocket.M2000_Remote_Secure_Mode:
        u = output_pdf_name
        v = template_name
        w = speciment_name
        x = controler_name
        y = pdf_path_name

        a = struct.pack(">Hhih", M2mRemoteOrder.SynchroKeyWord ,order_name,int(2+len(u)+2+len(v)+2+len(w)+2+len(x)+2+len(y)),len(u))  # transform the number in string format Big Indian
        clientsocket.M2mSend(a)  # send the message
        clientsocket.M2mSend(u)  # send the message

        a = struct.pack(">h", len(v))  # transform the number in string format Big Indian
        clientsocket.M2mSend(a)  # send the message
        clientsocket.M2mSend(v)  # send the message

        a = struct.pack(">h", len(w))  # transform the number in string format Big Indian
        clientsocket.M2mSend(a)  # send the message
        clientsocket.M2mSend(w)  # send the message

        a = struct.pack(">h", len(x))  # transform the number in string format Big Indian
        clientsocket.M2mSend(a)  # send the message
        clientsocket.M2mSend(x)  # send the message

        a = struct.pack(">h", len(y))  # transform the number in string format Big Indian
        clientsocket.M2mSend(a)  # send the message
        clientsocket.M2mSend(y)  # send the message

        #time.sleep(0.1)

        if clientsocket.M2mSecureReceive(4)==0:   # wait for return value (success or not)
            retour = int(struct.unpack('>i', clientsocket.retour)[0])
        else:
            print ("M2K_ReportOpenDialogBox Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_ReportOpenDialogBox only managed in secure mode  by Demo SW")

    return retour

##############################################################################

##############################################################################

#
def M2K_SetDacSynchroValueDigitalPerSequence(clientsocket, Salvo, Sequence, Shot, Begin, Threshold, Channel):

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihhhff',M2mRemoteOrder.SynchroKeyWord , M2mRemoteOrder.SetDacSynchroValue, int(2+2+2+8+8), Salvo, Sequence,Shot,Begin,Threshold)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(2) == 0:
            retour = float(struct.unpack('>h',clientsocket.retour)[0])
        else:
            print ("M2K_SetDacSynchroValueDigitalPerSequence Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_SetDacSynchroValueDigitalPerSequence not managed unsecured mode")
        retour = 0

    return retour



##############################################################################
def M2K_GetBufferizedAlarmSoftState(clientsocket):

    retour = 2
    if clientsocket.M2000_Remote_Secure_Mode:

        a = struct.pack(">Hhi", M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetBufferizedAlarmSoftState,0)  # transform the number in string format Big Indian
        clientsocket.M2mSend(a)  # send the message
        #time.sleep(0.1)

        if clientsocket.M2mSecureReceive(-1)==0:   # wait for return value (success or not)
            nb_alarms = int(struct.unpack('>h', clientsocket.retour[0:2])[0])
            retour=[]
            retour.append(nb_alarms)
            offset = 2
            for i in range(0,nb_alarms):
                retour.append( int(struct.unpack('>?', clientsocket.retour[offset:offset+1])[0]))
                offset+=1
        else:
            print ("M2K_GetBufferizedAlarmSoftState Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_GetBufferizedAlarmSoftState only managed in secure mode  by Demo SW")

    return retour

##############################################################################
def M2K_GetVpParamIntFloatArrayReturn(clientsocket,parameter_number, Salvo):

    retour = 2
    if clientsocket.M2000_Remote_Secure_Mode:

        a = struct.pack('>Hhii', M2mRemoteOrder.SynchroKeyWord , parameter_number, int(4), int(Salvo))
        clientsocket.M2mSend(a)  # send the message
        #time.sleep(0.1)

        if clientsocket.M2mSecureReceive(-1)==0:   # wait for return value (success or not)
            arraysize = int(struct.unpack('>i', clientsocket.retour[0:4])[0])
            print ("Arraysize :", arraysize)

            retour = numpy.arange(int(arraysize*2), dtype="float")
            retour=retour.reshape(int(arraysize),2)
            offset = 4
            for i in range(0,arraysize):
                retour[i,0]= struct.unpack('>f', clientsocket.retour[offset:offset+4])[0]
                offset+=4
                retour[i,1]= struct.unpack('>f', clientsocket.retour[offset:offset+4])[0]
                offset+=4
        else:
            print ("M2K_GetVpParamIntFloatArrayReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_GetVpParamIntFloatArrayReturn only managed in secure mode  by Demo SW")

    return retour

##############################################################################
def M2K_GetVpParamIntFloatArrayReturn(clientsocket,parameter_number, Salvo):

    retour = 2
    if clientsocket.M2000_Remote_Secure_Mode:

        a = struct.pack('>Hhii', M2mRemoteOrder.SynchroKeyWord , parameter_number, int(4), int(Salvo))
        clientsocket.M2mSend(a)  # send the message
        #time.sleep(0.1)

        if clientsocket.M2mSecureReceive(-1)==0:   # wait for return value (success or not)
            arraysize = int(struct.unpack('>i', clientsocket.retour[0:4])[0])
            print ("Arraysize :", arraysize)

            retour = np.arange(int(arraysize*2), dtype="float")
            retour=retour.reshape(int(arraysize),2)
            offset = 4

            for i in range(0,arraysize):
                retour[i,0]= struct.unpack('>f', clientsocket.retour[offset:offset+4])[0]
                offset+=4
                retour[i,1]= struct.unpack('>f', clientsocket.retour[offset:offset+4])[0]
                offset+=4

        else:
            print ("M2K_GetVpParamIntFloatArrayReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_GetVpParamIntFloatArrayReturn only managed in secure mode  by Demo SW")

    return retour

##############################################################################
def M2K_GetSalvoParamShortArrayReturn(clientsocket,parameter_number, Salvo):

    retour = 2
    if clientsocket.M2000_Remote_Secure_Mode:

        a = struct.pack('>Hhih', M2mRemoteOrder.SynchroKeyWord , parameter_number, int(2), Salvo)
        clientsocket.M2mSend(a)  # send the message
        #time.sleep(0.1)

        if clientsocket.M2mSecureReceive(-1)==0:   # wait for return value (success or not)
            arraysize = int(struct.unpack('>i', clientsocket.retour[0:4])[0])
            print ("Arraysize :", arraysize)
            retour=[]
            retour.append(arraysize)
            offset = 4
            for i in range(0,arraysize):
                retour.append( int(struct.unpack('>i', clientsocket.retour[offset:offset+4])[0]))
                offset+=4
        else:
            print ("Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_GetSalvoParamShortArrayReturn only managed in secure mode  by Demo SW")

    return retour

##############################################################################
def M2K_SetSalvoParamShortArrayReturn(clientsocket,parameter_number, Salvo, array):

    # first value of array is array size
    retour = 2
    if clientsocket.M2000_Remote_Secure_Mode:
        arraysize = array[0]
        a = struct.pack('>Hhihi', M2mRemoteOrder.SynchroKeyWord , parameter_number, int(6)+arraysize*4, Salvo, arraysize)
        clientsocket.M2mSend(a)  # send the message
        #time.sleep(0.1)
        for i in range(0,arraysize):
            a = struct.pack('>i', int(array[i+1]))
            clientsocket.M2mSend(a)  # send the message

        if clientsocket.M2mSecureReceive(6)==0:   # wait for return value (success or not)
            # status
            retour=[]
            retour.append( int(struct.unpack('>h', clientsocket.retour[0:2])[0]))
            # expected array size
            offset = 2
            retour.append( int(struct.unpack('>i', clientsocket.retour[offset:offset+4])[0]))
            if retour[0]!=0:
                print ("Array read status error ", retour[0])
                print ("Array read error, expected: ",retour[1], " sent: ", arraysize)

        else:
            print ("M2K_SetSalvoParamShortArrayReturn Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_GetSalvoParamShortArrayReturn only managed in secure mode  by Demo SW")

    return retour


##############################################################################
def M2K_GetTFMImage(clientsocket, Salvo):

    # first value of array is array size
    retour = 2
    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhih', M2mRemoteOrder.SynchroKeyWord , M2mRemoteOrder.GetTFMImage, int(2), Salvo)
        clientsocket.M2mSend(a)  # send the message
        #time.sleep(0.1)

        if clientsocket.M2mSecureReceive(-1)==0:   # wait for return value (success or not)
            # status
            retour=[]
            image_width = int(struct.unpack('>i', clientsocket.retour[0:4])[0])
            image_heigth = int(struct.unpack('>i', clientsocket.retour[4:8])[0])
            #print "image heigth", image_heigth, "image width", image_width
            # expected array size
            image_size=4*image_heigth*image_width

            #convert data stream to int32 array
            array=np.frombuffer(clientsocket.retour[8:image_size+8],dtype=np.dtype(">i"))
            retour = array.reshape(image_heigth,image_width)



        else:
            print ("GetTFMImage Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_GetTFMImage only managed in secure mode  by Demo SW")

    return retour


##############################################################################
def M2K_GetTFMDesc(clientsocket, Salvo):

    # first value of array is array size
    retour = 2

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhih', M2mRemoteOrder.SynchroKeyWord , M2mRemoteOrder.GetTFMDesc, int(2), Salvo)
        clientsocket.M2mSend(a)  # send the message
        #time.sleep(0.1)

        if clientsocket.M2mSecureReceive(48+4+4+4+4)==0:   # wait for return value (success or not)
            # status
            retour=[]
            #convert data stream to float array containing Zone edge position and step
            float_packet_size=48+4+4
            retour.append( np.fromstring(clientsocket.retour[0:float_packet_size],dtype=np.dtype(">f")))
            retour.append( np.fromstring(clientsocket.retour[float_packet_size:float_packet_size+8],dtype=np.dtype(">i")))

        else:
            print ("M2K_GetTFMDesc Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_GetTFMDesc only managed in secure mode  by Demo SW")

    return retour


##############################################################################
def M2K_GetBufferizedAlarmSoftPosition(clientsocket):

    retour = 2
    if clientsocket.M2000_Remote_Secure_Mode:

        a = struct.pack(">Hhi", M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetBufferizedAlarmSoftPosition,0)  # transform the number in string format Big Indian
        clientsocket.M2mSend(a)  # send the message
        #time.sleep(0.1)

        if clientsocket.M2mSecureReceive(-1)==0:   # wait for return value (success or not)
            nb_alarms = int(struct.unpack('>h', clientsocket.retour[0:2])[0])
            retour=[]
            retour.append(nb_alarms)
            offset = 2
            for i in range(0,nb_alarms):
                retour.append( int(struct.unpack('>?', clientsocket.retour[offset:offset+1])[0]))
                offset+=1
                retour.append( float(struct.unpack('>f', clientsocket.retour[offset:offset+4])[0]))
                offset+=4
                retour.append( float(struct.unpack('>f', clientsocket.retour[offset:offset+4])[0]))
                offset+=4
                retour.append( float(struct.unpack('>f', clientsocket.retour[offset:offset+4])[0]))
                offset+=4
                retour.append( float(struct.unpack('>f', clientsocket.retour[offset:offset+4])[0]))
                offset+=4

        else:
            print ("M2K_GetBufferizedAlarmSoftPosition Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_GetBufferizedAlarmSoftPosition only managed in secure mode  by Demo SW")

    return retour

##############################################################################

def M2K_GetDataFromView(clientsocket,view_name):

    retour = 2
    if clientsocket.M2000_Remote_Secure_Mode:

        u = view_name

        a = struct.pack(">Hhih", M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetDataFromView,int(2+len(u)),
                        len(u))  # transform the number in string format Big Indian
        #print "Ordre ", binascii.hexlify(a), " Hexa"
        clientsocket.M2mSend(a)  # send the message
        clientsocket.M2mSend(u)  # send the message

        if clientsocket.M2mSecureReceive(-1)==0:   # wait for return value (success or not)
            retour=[]
            print ("data size:", len(clientsocket.retour))
            offset = 0
            for i in range(1,6):
                retour.append( int(struct.unpack('>i', clientsocket.retour[offset:offset+4])[0]))
                offset += 4
            for i in range(1,5):
                retour.append( float(struct.unpack('>f', clientsocket.retour[offset:offset+4])[0]))
                offset += 4
            retour.append( int(struct.unpack('>i', clientsocket.retour[offset:offset+4])[0]))
            offset += 4

            for i in retour:
                print (i)
            nb_data = retour[9]
            print ("nb data:",nb_data)
            #print "type",type(retour[offset:nb_data*2+offset][0])

            retour.append(np.fromstring(clientsocket.retour[offset:offset+(nb_data*2)],dtype=np.dtype(">h")))
            print (retour[10])

            offset+=nb_data*2
            num_col=retour[2]
            num_lines=retour[3]
            data_array_zize=num_col*num_lines*2
            print ("data array size = ", data_array_zize)
            print ("number of columns = ",num_col)
            print ("number of lines = ",num_lines)

            data=np.fromstring(clientsocket.retour[offset:offset+(data_array_zize)],dtype=np.dtype(">h"))

            print ("shape",data.shape)

            rdata=data.reshape(num_col,num_lines)
            print ("shape r",rdata.shape)
            retour.append(rdata)


        else:
            print ("Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_GetDataFromView only managed in secure mode  by Demo SW")

    return retour


##############################################################################
def M2K_GetImageFromView(clientsocket,view_name,img_type):

    retour = 2
    if clientsocket.M2000_Remote_Secure_Mode:

        u = view_name
        u2 = img_type

        a = struct.pack(">Hhih", M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetImageFromView,int(4+len(u)+len(u2)),
                        len(u))  # transform the number in string format Big Indian
        #print "Ordre ", binascii.hexlify(a), " Hexa"
        clientsocket.M2mSend(a)  # send the message
        clientsocket.M2mSend(u)  # send the message

        a = struct.pack(">h",  len(u2))  # transform the number in string format Big Indian
        clientsocket.M2mSend(a)  # send the message
        clientsocket.M2mSend(u2)  # send the message

        if clientsocket.M2mSecureReceive(-1)==0:   # wait for return value (success or not)
            retour=[]
            offset = 0
            image_size=int(struct.unpack('>i', clientsocket.retour[offset:offset+4])[0])
            retour.append(image_size)
            offset += 4

            print ("image size:" ,image_size)

            retour.append(np.fromstring(clientsocket.retour[offset:image_size+offset],dtype="byte"))

        else:
            print ("M2K_GetImageFromView Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_GetImageFromView only managed in secure mode  by Demo SW")

    return retour

##############################################################################
def M2K_GetDDFSegmentsWindow(clientsocket, salvo ):

    retour = 2
    if clientsocket.M2000_Remote_Secure_Mode:

        a = struct.pack(">Hhih", M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetDDFSegmentsWindow,int(2),salvo)  # transform the number in string format Big Indian
        clientsocket.M2mSend(a)  # send the message
        #time.sleep(0.1)

        if clientsocket.M2mSecureReceive(-1)==0:   # wait for return value (success or not)
            retour=[]
            retour.append( float(struct.unpack('>f', clientsocket.retour[0:4])[0]))
            nb_segments = int(struct.unpack('>h', clientsocket.retour[4:6])[0])
            retour.append(nb_segments)
            for i in range(0,nb_segments):
                retour.append( float(struct.unpack('>f', clientsocket.retour[6+i*4:10+i*4])[0]))
        else:
            print ("M2K_GetDDFSegmentsWindow Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_GetDDFSegmentsWindow only managed in secure mode  by Demo SW")

    return retour
##############################################################################
def M2K_SetDDFSegmentsWindow(clientsocket, salvo, nb_segments,  start_position, segments_length ):

    retour = 2
    if clientsocket.M2000_Remote_Secure_Mode:

        a = struct.pack(">Hhihfh", M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.SetDDFSegmentsWindow,int(2+4+2+4*nb_segments),int(salvo),float(start_position),int(nb_segments))  # transform the number in string format Big Indian
        clientsocket.M2mSend(a)  # send the message
        #time.sleep(0.1)
        for i in range(0,nb_segments):
            a = struct.pack(">f",float(segments_length[i]))
            clientsocket.M2mSend(a)

        if clientsocket.M2mSecureReceive(2)==0:   # wait for return value (success or not)
            retour = int(struct.unpack('>h', clientsocket.retour)[0])
        else:
            print ("Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_SetDDFSegmentsWindow only managed in secure mode by Demo SW")

    return retour

##############################################################################
def M2K_GetDDFSegmentsDelays(clientsocket, salvo, segment ):

    retour = 2
    if clientsocket.M2000_Remote_Secure_Mode:

        a = struct.pack(">Hhihh", M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetDDFSegmentsDelays,int(2+2),int(salvo),int(segment))  # transform the number in string format Big Indian
        clientsocket.M2mSend(a)  # send the message
        #time.sleep(0.1)

        if clientsocket.M2mSecureReceive(-1)==0:   # wait for return value (success or not)
            retour=[]
            nb_delays = int(struct.unpack('>h', clientsocket.retour[0:2])[0])
            retour.append(nb_delays)
            for i in range(0,nb_delays):
                retour.append( float(struct.unpack('>f', clientsocket.retour[2+i*4:6+i*4])[0]))
        else:
            print ("Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_GetDDFSegmentsDelays only managed in secure mode by Demo SW")

    return retour

##############################################################################
def M2K_SetDDFSegmentsDelays(clientsocket, salvo, num_segment, nb_delays, segment_delays ):

    retour = 2
    if clientsocket.M2000_Remote_Secure_Mode:

        a = struct.pack(">Hhihhh", M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.SetDDFSegmentsDelays,int(2+2+2+4*nb_delays),int(salvo),int(num_segment),int(nb_delays))  # transform the number in string format Big Indian
        clientsocket.M2mSend(a)  # send the message
        #time.sleep(0.1)
        for i in range(0,nb_delays):
            a = struct.pack(">f",float(segment_delays[i]))
            clientsocket.M2mSend(a)

        if clientsocket.M2mSecureReceive(2)==0:   # wait for return value (success or not)
            retour = int(struct.unpack('>h', clientsocket.retour)[0])
        else:
            print ("Communication Socket Error: ", clientsocket.return_status)
            retour = 0

    else:
        print ("M2K_SetDDFDelaysSegments only managed in secure mode by Demo SW")

    return retour
##############################################################################
###### get the current amp in the gate when in the setting menu ##############
##############################################################################

def M2K_GetCurrentAmplitudeGate(clientsocket, salvo, gate_num, sequence_num, shot_num, echo_num):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihhhhh',M2mRemoteOrder.SynchroKeyWord , M2mRemoteOrder.GetCurrentAmplitudeGate, int(10),salvo, gate_num, sequence_num, shot_num,
                        echo_num)
        clientsocket.M2mSend(a)

        if clientsocket.M2mSecureReceive(6) == 0:
            gate_state = int(struct.unpack('>h', clientsocket.retour[0:2])[0])
            return float(struct.unpack('>f', clientsocket.retour[2:7])[0])
        else:
            print ("M2K_GetCurrentAmplitudeGate Communication Socket Error: ", clientsocket.return_status)
            return 0.0

    else:
        a = struct.pack('>hhhhhh', M2mRemoteOrder.GetCurrentAmplitudeGate, salvo, gate_num, sequence_num, shot_num,
                        echo_num)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)

        gate_state = int(struct.unpack('>h', retour)[0])

        retour = clientsocket.M2MReceive(4)

        return float(struct.unpack('>f', retour)[0])


##############################################################################
###### get the current TOF in the gate when in the setting menu ##############
##############################################################################

def M2K_GetCurrentDistanceGate(clientsocket, salvo, gate_num, sequence_num, shot_num, echo_num):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihhhhh', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetCurrentDistanceGate, int(10),salvo, gate_num, sequence_num, shot_num,
                        echo_num)
        clientsocket.M2mSend(a)

        if clientsocket.M2mSecureReceive(6) == 0:
            gate_state = int(struct.unpack('>h', clientsocket.retour[0:2])[0])
            return float(struct.unpack('>f', clientsocket.retour[2:7])[0])
        else:
            print ("M2K_GetCurrentDistanceGate Communication Socket Error: ", clientsocket.return_status)
            return 0.0

    else:

        a = struct.pack('>hhhhhh', M2mRemoteOrder.GetCurrentDistanceGate, salvo, gate_num, sequence_num, shot_num, echo_num)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)

        gate_state = int(struct.unpack('>h', retour)[0])

        retour = clientsocket.M2MReceive(4)

    return float(struct.unpack('>f', retour)[0])


##############################################################################
####### read the digital inputs of the device when available #################
##############################################################################

def M2K_GetInputs(clientsocket):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetInputs,int(0))
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(32) == 0:
            liste_inputs = []
            for i in range(0, 16):
                liste_inputs.append(int(struct.unpack('>h', clientsocket.retour[i*2:i*2+2])[0]))
        else:
            print ("Communication Socket Error: ", clientsocket.return_status)
            return []

    else:
        a = struct.pack('>h', M2mRemoteOrder.GetInputs)
        clientsocket.M2mSend(a)

        liste_inputs = []

        for i in range(0, 16):
            retour = clientsocket.M2MReceive(2)
            liste_inputs.append(int(struct.unpack('>h', retour)[0]))

    return liste_inputs


#############################################################################
####### read the analog inputs of the device when available #################
#############################################################################

def M2K_GetInputsTension(clientsocket):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetInputsTension,int(0))
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(64) == 0:
            liste_inputs = []
            for i in range(0, 16):
                liste_inputs.append(int(struct.unpack('>f', clientsocket.retour[i*4:i*4+4])[0]))
        else:
            print ("Communication Socket Error: ", clientsocket.return_status)
            return []

    else:

        a = struct.pack('>h', M2mRemoteOrder.GetInputsTension)
        clientsocket.M2mSend(a)

        liste_inputs = []

        for i in range(0, 16):
            retour = clientsocket.M2MReceive(4)
            liste_inputs.append(int(struct.unpack('>f', retour)[0]))

    return liste_inputs


##############################################################################
#### set the gain for a salvo when paused during acquisition only
#### This function is used in industrial applications when gain must
#### be changed during Cscan because of geometry part variation.
#### Acquisition must be started and in pause. If it is not the case, the action will fail.
##############################################################################

def M2K_AnalogueGainDuringAcquisition(clientsocket, salvo, gain):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihd', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.SetAnalogueGainDuringAcquisition,int(10),salvo, float( gain) )
        clientsocket.M2mSend(a)

        if clientsocket.M2mSecureReceive(2) == 0:
            retour = int(struct.unpack('>h', clientsocket.retour)[0])
        else:
            print ("M2K_AnalogueGainDuringAcquisition Communication Socket Error: ", clientsocket.return_status)
            retour = 0


    else:
        a = struct.pack('>hhd', M2mRemoteOrder.SetAnalogueGainDuringAcquisition,salvo, float( gain) )
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)
        retour = int(struct.unpack('>h', retour)[0])

    return retour
##############################################################################
# set the selected DAC for action (analog, gate...) ########################
##############################################################################
def M2K_SetSelectedDacActionDacGate(clientsocket, type_dac, salvo):
    global M2mRemoteOrder
    global M2MDacActionSet

    par = type_dac

    if (type_dac == M2MDacActionSet.GateDac ) or (type_dac == M2MDacActionSet.AnalogDacPerSalvo):
        M2K_SetParameter2xShortParamNoReturn(clientsocket,M2mRemoteOrder.SetSelectedDacActions, par, salvo)
    elif (type_dac == M2MDacActionSet.DigitalDacSalvo)or (type_dac==M2MDacActionSet.AnalogDacAllSalvoes):

        M2K_SetParameterShortParamNoReturn(clientsocket,M2mRemoteOrder.SetSelectedDacActions, salvo)

    else:
        print ("Error, SelectDacAction for this DAC is not managed yet, Sorry: ", par)


##############################################################################
#### set the gain for each segment of the DAC
### can be very useful for automatic calibration defined by user software
### it is necessary to ask to M2000 how many point are programmed (getdacgains).
### number of point can be easily increase or reduced by remote.
##############################################################################

def M2K_SetDacGains(clientsocket, liste_gains, nb_points):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.SetDacGains,int(nb_points*4))
        clientsocket.M2mSend(a)

        if nb_points > 0:
            for i in range(0, nb_points):
                value = liste_gains[i]
                a = struct.pack('>f', float(value))
                clientsocket.M2mSend(a)

        clientsocket.M2mSecureReceive(0)

    else:

        a = struct.pack('>h', M2mRemoteOrder.SetDacGains)
        clientsocket.M2mSend(a)

        if nb_points > 0:
            for i in range(0, nb_points):
                value = liste_gains[i]
                a = struct.pack('>f', float(value))
                clientsocket.M2mSend(a)


def M2K_SetDacCurve(clientsocket, cdac):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhii', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.SetDacCurve,int((cdac.nb_of_points*2+1)*4),cdac.nb_of_points)
        clientsocket.M2mSend(a)

        if cdac.nb_of_points > 0:
            for i in range(0, cdac.nb_of_points):
                a = struct.pack('>f', float(cdac.positions[i]))
                clientsocket.M2mSend(a)
            for i in range(0, cdac.nb_of_points):
                a = struct.pack('>f', float(cdac.gains[i]))
                clientsocket.M2mSend(a)
            retour = clientsocket.M2mSecureReceive(4+cdac.nb_of_points*8+4)

            if retour == 0:
                offset = 0
                cdac.nb_of_points = int(struct.unpack('>i', clientsocket.retour[offset:offset+4])[0])
                offset+=4
                for i in range(0, cdac.nb_of_points):
                    cdac.positions[i] = struct.unpack('>f', clientsocket.retour[offset:offset+4])[0]
                    offset+=4

                for i in range(0, cdac.nb_of_points):
                    cdac.gains[i] = struct.unpack('>f', clientsocket.retour[offset:offset+4])[0]
                    offset+=4

    else:
        print ("SetDacCurve not managed in non secured mode")


##############################################################################
#### get the gain for each segment of the DAC
### can be very useful for automatic calibration defined by user software
### to knows actual gain setting and correct after
##############################################################################

def M2K_GetDacGains(clientsocket):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:

        #bugs en attente de correction
        a = struct.pack('>Hhi',M2mRemoteOrder.SynchroKeyWord , M2mRemoteOrder.GetDacGains,int(0))
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(-1) == 0:
            nb_points = int(struct.unpack('>h', clientsocket.retour[0:2])[0])
            list_gains = []
            offset=2
            if nb_points > 0:
                for i in range(0, nb_points):
                    retour = float(struct.unpack('>f', clientsocket.retour[offset:offset+4])[0])
                    offset+=4
                    list_gains.append(retour)
        else:
            print ("Communication Socket Error: ", clientsocket.return_status)
            return []

    else:
        a = struct.pack('>h', M2mRemoteOrder.GetDacGains)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)

        nb_points = int(struct.unpack('>h', retour)[0])

        list_gains = []

        if nb_points > 0:
            for i in range(0, nb_points):
                retour = clientsocket.M2MReceive(4)

                retour = float(struct.unpack('>f', retour)[0])
                list_gains.append(retour)

    return list_gains


##############################################################################
#### get the position for each segment of the DAC
##############################################################################
def M2K_GetDacPositions(clientsocket):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:

        #bug à corriger

        a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetDacPositions,int(0))
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(-1) == 0:
            nb_points = int(struct.unpack('>h', clientsocket.retour[0:2])[0])
            list_gains = []
            offset=2
            if nb_points > 0:
                for i in range(0, nb_points):
                    retour = float(struct.unpack('>f', clientsocket.retour[offset:offset+4])[0])
                    offset+=4
                    list_gains.append(retour)
        else:
            print ("Communication Socket Error: ", clientsocket.return_status)
            return []

    else:
        a = struct.pack('>h', M2mRemoteOrder.GetDacPositions)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)

        nb_points = int(struct.unpack('>h', retour)[0])

        list_gains = []

        if nb_points > 0:
            for i in range(0, nb_points):
                retour = clientsocket.M2MReceive(4)

                retour = float(struct.unpack('>f', retour)[0])
                list_gains.append(retour)

    return list_gains


##############################################################################
#### set the gain for each segment of the DAC

def M2K_SetDacPositions(clientsocket, list_positions, nb_points):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.SetDacPositions, int(nb_points*4))
        clientsocket.M2mSend(a)

        if nb_points > 0:
            for i in range(0, nb_points):
                value = float(list_positions[i])
                a = struct.pack('>f', value)
                clientsocket.M2mSend(a)

        clientsocket.M2mSecureReceive(0)
    else:
        a = struct.pack('>h', M2mRemoteOrder.SetDacPositions)
        clientsocket.M2mSend(a)

        if nb_points > 0:
            for i in range(0, nb_points):
                value = float(list_positions[i])
                a = struct.pack('>f', value)
                clientsocket.M2mSend(a)


##############################################################################
# enable to increase number of points in the DAC curve remotely #############
# useful for remote automatic calibration
##############################################################################

def M2K_AddDacPoint(clientsocket):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.AddDacPoint, int(0))
        clientsocket.M2mSend(a)
    else:
        a = struct.pack('>h', M2mRemoteOrder.AddDacPoint)
        clientsocket.M2mSend(a)


##############################################################################
# ask for M2000 current encoder value
# This function is to be called if not in acquisition mode but in setting mode
##############################################################################

def M2K_GetCurrentValueCoder(clientsocket, num_coder):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhih', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetCurrentValueCoder, int(2), num_coder)
        clientsocket.M2mSend(a)

        if clientsocket.M2mSecureReceive(6) == 0:

            status = int(struct.unpack('>h', clientsocket.retour[0:2])[0])

            coder_value = float(struct.unpack('>f', clientsocket.retour[2:6])[0])
        else:
            print ("Communication Socket Error: ", clientsocket.return_status)
            coder_value = -1.0


    else:
        a = struct.pack('>hh', M2mRemoteOrder.GetCurrentValueCoder, num_coder)
        clientsocket.M2mSend(a)

        status = clientsocket.M2MReceive(2)
        status = int(struct.unpack('>h', status)[0])

        coder_value = clientsocket.M2MReceive(4)

        coder_value = float(struct.unpack('>f', coder_value)[0])

    return coder_value


##############################################################################
##############################################################################
# set selectdac action enable to choose which DAC will be used with DAC actions (Analog, Digital...)
##############################################################################
def M2K_SetSelectedDacActionDacDigitalDetail(clientsocket, salvo, sequ, shot, rebuild_seq, rebuild_shot):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:
        order = -3
        #if is_multiple:

        a = struct.pack('>Hhihhhhhh', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.SetSelectedDacActions, int(12), order, salvo, sequ, shot, rebuild_seq,
                        rebuild_shot)
        #else:
        #    a = struct.pack('>hhhhh',M2mRemoteOrder.SetSelectedDacAction,order, salvo, sequ, shot)

        clientsocket.M2mSend(a)
        clientsocket.M2mSecureReceive(0)
    else:

        order = -3
        #if is_multiple:

        a = struct.pack('>hhhhhhh', M2mRemoteOrder.SetSelectedDacActions, order, salvo, sequ, shot, rebuild_seq,
                        rebuild_shot)
        #else:
        #    a = struct.pack('>hhhhh',M2mRemoteOrder.SetSelectedDacActions,order, salvo, sequ, shot)

        clientsocket.M2mSend(a)


##############################################################################
# this function ask to M2000 SW the properties of connected HW
# The property parameter is in the list M2mSystemProperties
##############################################################################

def M2K_GetSystemProperty(clientsocket, device, property):
    global M2mRemoteOrder
    global M2mSystemProperties

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihh', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetSystemProperty, int(4), device, property)
        clientsocket.M2mSend(a)

        if clientsocket.M2mSecureReceive(-1) == 0:

            retour = int(struct.unpack('>h', clientsocket.retour[0:2])[0])
            if retour == 0:
                if property == M2mSystemProperties.SerialNumber or \
                                property == M2mSystemProperties.IndexFirstInput or \
                                property == M2mSystemProperties.IndexFirstOutput or \
                                property == M2mSystemProperties.DeviceType:
                    #int return

                    retour = int(struct.unpack('>i', clientsocket.retour[2:6])[0])
                    return retour
                elif property == M2mSystemProperties.Name:
                    #string
                    filesize = int(struct.unpack('>h', clientsocket.retour[2:4])[0])
                    #return fist is length of string
                    name = ""
                    if filesize > 0:
                        name = clientsocket.retour[4:]
                    return name

                else:
                    #short
                    retour = int(struct.unpack('>h', clientsocket.retour[2:4])[0])
                    return retour
        else:
            print ("Communication Socket Error: ", clientsocket.return_status)
            return 0

    else:
        a = struct.pack('>hhh', M2mRemoteOrder.GetSystemProperty, device, property)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)
        retour = int(struct.unpack('>h', retour)[0])

        if retour == 0:
            if property == M2mSystemProperties.SerialNumber or \
                            property == M2mSystemProperties.IndexFirstInput or \
                            property == M2mSystemProperties.IndexFirstOutput or \
                            property == M2mSystemProperties.DeviceType:
                #int return
                retour = clientsocket.M2MReceive(4)
                retour = int(struct.unpack('>i', retour)[0])
                return retour
            elif property == M2mSystemProperties.Name:
                #string
                retour = clientsocket.M2MReceive(2)
                retour = int(struct.unpack('>h', retour)[0])
                #return fist is length of string
                name = ""
                if retour > 0:
                    name = clientsocket.M2MReceive(retour)
                return name

            else:
                #short
                retour = clientsocket.M2MReceive(2)
                retour = int(struct.unpack('>h', retour)[0])
                return retour


##############################################################################
# the name of the configuration must be the subdirectory including the config.xml name.

def M2K_load_configuration(clientsocket, config_name):
    global M2mRemoteOrder

    return M2K_SetParameterStringParamShortReturn(clientsocket, M2mRemoteOrder.LoadConfiguration, config_name)

##############################################################################
# the name of the configuration must be the subdirectory including the config.xml name.

def M2K_save_acquisition(clientsocket, config_name):
    global M2mRemoteOrder

    return M2K_SetParameterStringParamShortReturn(clientsocket, M2mRemoteOrder.SaveAcquisition, config_name)


def M2K_save_configuration(clientsocket, config_name):
    global M2mRemoteOrder

    return M2K_SetParameterStringParamShortReturn(clientsocket, M2mRemoteOrder.SaveConfiguration, config_name)

##############################################################################
# get the name of the current configuration in M2000 SW
##############################################################################

def M2K_GetNameOfTheConfiguration(clientsocket):
    global M2mRemoteOrder

    return M2K_GetParameterNoParamStringReturn(clientsocket,M2mRemoteOrder.GetNameOfTheConfiguration)


##############################################################################
# get data description in the selected gate as a string
##############################################################################
def M2K_GetDataDescription(clientsocket, salvo, gate, data_num):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhihhh', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetDataDescription, int(6), salvo, gate, data_num)
        clientsocket.M2mSend(a)

        if clientsocket.M2mSecureReceive(-1) == 0:
            sizename = int(struct.unpack('>h', clientsocket.retour[0:2])[0])
            #return fist is length of string
            name = ""
            if sizename > 0:
                name = clientsocket.retour[2:]
        else:
            print ("Communication Socket Error: ", clientsocket.return_status)
            return ""

    else:
        a = struct.pack('>hhhh', M2mRemoteOrder.GetDataDescription, salvo, gate, data_num)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)
        retour = int(struct.unpack('>h', retour)[0])
        #return fist is length of string
        name = ""
        if retour > 0:
            name = clientsocket.M2MReceive(retour)

    return name


##############################################################################

def M2K_GetMulti2000Version(clientsocket):
    global M2mRemoteOrder

    return M2K_GetParameterNoParamStringReturn(clientsocket,M2mRemoteOrder.GetMulti2000Version)


##############################################################################
# Get the current Ascan in the Setting menu.
# For acquisition, need to use Data Server and not Remote server
# This code is writen for readability and not for efficiency
##############################################################################

def M2K_Get_Ascan(clientsocket, salvo, sequence, shot, channel):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:

        a = struct.pack('>Hhihhhh', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetAscan, int(8), salvo, sequence, shot, channel)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(-1) == 0:
            nb_data = int(struct.unpack('>h', clientsocket.retour[0:2])[0])
            #return first is length of ascan

            if nb_data > 0:
                ascan=np.fromstring(clientsocket.retour[2:nb_data*2+2],dtype="int16")
            else:
                print ("no data")
                ascan = np.zeros(nb_data,dtype="int16")
        else:
            print ("Error com Ascan")
            ascan = np.szeros(2048,dtype="int16")

    else:
        a = struct.pack('>hhhhh', M2mRemoteOrder.GetAscanInt, salvo, sequence, shot, channel)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(2)
        retour = int(struct.unpack('>h', retour)[0])

        #return first is length of ascan

        if retour > 0:
            ascan=np.fromstring(clientsocket.M2MReceive(2*retour),dtype="int16")

        # is equivalent to:
        #    if retour > 0:
        #        ascan = zeros(retour, int)
        #        for i in range(0, retour):
        #            point = clientsocket.M2MReceive(2)
        #            # beware, Ascan is not in big indian but little indian for efficiency improvement
        #            ascan[i] = int(struct.unpack('<h', point)[0])

    return ascan


##############################################################################
# Get the current Ascan in the Setting menu.
# For acquisition, need to use Data Server and not Remote server
# This code is writen for readability and not for efficiency
##############################################################################

def M2K_Get_Ascan_Int(clientsocket, salvo, sequence, shot, channel):
    global M2mRemoteOrder

    if clientsocket.M2000_Remote_Secure_Mode:

        a = struct.pack('>Hhihhhh', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetAscanInt, int(8), salvo, sequence, shot, channel)
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(-1) == 0:
            nb_data = int(struct.unpack('>i', clientsocket.retour[0:4])[0])
            #return first is length of ascan

            if nb_data > 0:
                ascan=np.fromstring(clientsocket.retour[4:nb_data*2+4],dtype="int16")
            else:
                print ("no data")
                ascan = np.zeros(nb_data,dtype="int16")
        else:
            print ("Error com Ascan")
            ascan = np.zeros(2048,dtype="int16")

    else:
        a = struct.pack('>hhhhh', M2mRemoteOrder.GetAscanInt, salvo, sequence, shot, channel)
        clientsocket.M2mSend(a)

        retour = clientsocket.M2MReceive(4)
        retour = int(struct.unpack('>i', retour)[0])

        #return first is length of ascan

        if retour > 0:
            ascan=np.fromstring(clientsocket.M2MReceive(2*retour),dtype="int16")

        # is equivalent to:
        #    if retour > 0:
        #        ascan = zeros(retour, int)
        #        for i in range(0, retour):
        #            point = clientsocket.M2MReceive(2)
        #            # beware, Ascan is not in big indian but little indian for efficiency improvement
        #            ascan[i] = int(struct.unpack('<h', point)[0])

    return ascan


##############################################################################
# Get all the the current elementary Ascans in the Setting menu.
# For acquisition, need to use Data Server and not Remote server
# This code is writen for readability and not for efficiency
##############################################################################

def M2K_GetAllAscansElementaryInt(clientsocket):
    global M2mRemoteOrder

    ascan_list=[]
    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetAllAscansElementaryInt, int(0))
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(-1) == 0:
            nb_ascan =  int(struct.unpack('>i', clientsocket.retour[0:4])[0])
            pt_read = 4
            if nb_ascan >0:

                nb_data = int(struct.unpack('>i', clientsocket.retour[pt_read+2:pt_read+6])[0])

                ascan_list=np.zeros((nb_ascan,nb_data),dtype=np.int32)

                for i in range (0,nb_ascan):
                    channel = int(struct.unpack('>h', clientsocket.retour[pt_read:pt_read+2])[0])
                    pt_read=pt_read+2
                    nb_data = int(struct.unpack('>i', clientsocket.retour[pt_read:pt_read+4])[0])

                    #return first is length of ascan
                    pt_read=pt_read+4
                    if nb_data > 0:
                        ascan_list[i]=np.fromstring(clientsocket.retour[pt_read:pt_read+nb_data*4],dtype="int")
                        #ascan_list.append(ascan)
                        pt_read=pt_read+nb_data*4

    else:
        print ("ascan elementaires non gérés en mode non sécurisé")

    return ascan_list


def M2K_Get_All_Ascans(clientsocket):
    global M2mRemoteOrder

    ascan_list=[]
    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetAllAscans, int(0))
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(-1) == 0:
            nb_ascan =  int(struct.unpack('>h', clientsocket.retour[0:2])[0])
            pt_read = 2
            if nb_ascan >0:

                nb_data = int(struct.unpack('>h', clientsocket.retour[pt_read:pt_read+2])[0])

                ascan_list=np.zeros((nb_ascan,nb_data),dtype=np.int16)
                pt_read+=2
                for i in range (0,nb_ascan):
                    ascan_list[i]=np.fromstring(clientsocket.retour[pt_read:pt_read+nb_data*2],dtype="int16")
                    #ascan_list.append(ascan)
                    pt_read=pt_read+nb_data*2+2

    else:
        print ("Get all ascan non gérés en mode non sécurisé")

    return ascan_list

def M2K_Get_All_Ascans_big_indian(clientsocket):
    global M2mRemoteOrder

    ascan_list=[]
    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetAllAscans, int(0))
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(-1) == 0:
            nb_ascan =  int(struct.unpack('>h', clientsocket.retour[0:2])[0])
            pt_read = 2
            if nb_ascan >0:

                nb_data = int(struct.unpack('>h', clientsocket.retour[pt_read:pt_read+2])[0])

                ascan_list=np.zeros((nb_ascan,nb_data),dtype=np.int16)
                pt_read+=2
                for i in range (0,nb_ascan):
                    ascan_list[i]=np.fromstring(clientsocket.retour[pt_read:pt_read+nb_data*2],dtype=">i2")
                    #ascan_list.append(ascan)
                    pt_read=pt_read+nb_data*2+2

    else:
        print ("Get all ascan non gérés en mode non sécurisé")

    return ascan_list


def M2K_GetAllAscansElementary(clientsocket):
    global M2mRemoteOrder

    ascan_list=[]
    if clientsocket.M2000_Remote_Secure_Mode:
        a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetAllAscansElementary, int(0))
        clientsocket.M2mSend(a)
        if clientsocket.M2mSecureReceive(-1) == 0:
            nb_ascan =  int(struct.unpack('>h', clientsocket.retour[0:2])[0])
            pt_read = 2
            if nb_ascan >0:

                nb_data = int(struct.unpack('>h', clientsocket.retour[pt_read+2:pt_read+4])[0])

                ascan_list=np.zeros((nb_ascan,nb_data),dtype="int16")

                for i in range (0,nb_ascan):
                    channel = int(struct.unpack('>h', clientsocket.retour[pt_read:pt_read+2])[0])
                    pt_read=pt_read+2
                    nb_data = int(struct.unpack('>h', clientsocket.retour[pt_read:pt_read+2])[0])
                    #return first is length of ascan
                    pt_read=pt_read+2
                    if nb_data > 0:
                        ascan_list[i]=np.fromstring(clientsocket.retour[pt_read:pt_read+nb_data*2],dtype="int16")
                        #ascan_list.append(ascan)
                        pt_read=pt_read+nb_data*2

    else:
        print ("ascan elementaires non gérés en mode non sécurisé")

    return ascan_list

##############################################################################
# this function stops the electronic sequencer and put priority for executing
# remote actions the paramters aren't sent to electronics before restart.
# It is useful when have a lot of actions to do to
# accelerate process. To restart, use M2K_WriteAndStartHard()
##############################################################################

def M2K_StopHardAndNoWrite(clientsocket):
    global M2mRemoteOrder

    return M2K_GetParameterNoParamShortReturn(clientsocket, M2mRemoteOrder.StopHardAndNoWrite)


#####################################################################################################
# Send orders sent before since M2K_StopHardAndNoWrite to electronics and restart the HW sequencer
#####################################################################################################


def M2K_WriteAndStartHard(clientsocket):
    global M2mRemoteOrder

    return M2K_GetParameterNoParamShortReturn(clientsocket, M2mRemoteOrder.WriteAndStartHard)



##############################################################################
##############################################################################

def M2K_GetNbSalvo(clientsocket):
    global M2mRemoteOrder

    return M2K_GetParameterNoParamShortReturn(clientsocket, M2mRemoteOrder.GetNbSalvos)


##############################################################################
##############################################################################

def M2K_GetNbSequences(clientsocket, salvo):
    global M2mRemoteOrder

    return M2K_GetParameterShortParamShortReturn(clientsocket, M2mRemoteOrder.GetNbSequences, salvo)


##############################################################################
##############################################################################

def M2K_GetNbShots(clientsocket, salvo, sequence):
    global M2mRemoteOrder

    return M2K_GetParameter2xShortParamShortReturn(clientsocket, M2mRemoteOrder.GetNbShots, salvo, sequence)

##############################################################################
##############################################################################

def M2k_GetNbSequencesRecons(clientsocket, salvo, sequence, shot):
    global M2mRemoteOrder

    return M2K_GetParameter3xShortParamShortReturn(clientsocket, M2mRemoteOrder.GetSequencesBuildNb, salvo, sequence,shot)

##############################################################################
##############################################################################

def M2k_GetNbShotsRecons(clientsocket, salvo, sequence, shot, sequ_recons):
    global M2mRemoteOrder

    return M2K_GetParameter4xShortParamShortReturn(clientsocket, M2mRemoteOrder.GetShotsBuildNb, salvo, sequence,shot, sequ_recons)


##############################################################################
##############################################################################

def M2K_GetNbChannelsTransmission(clientsocket, salvo, sequence, shot):
    global M2mRemoteOrder

    return M2K_GetParameter3xShortParamShortReturn(clientsocket, M2mRemoteOrder.GetNbChannelsTransmission, salvo,
                                                   sequence, shot)

def M2K_GetNbChannelsTransmissionMultiple(clientsocket, salvo, sequence, shot, Sequence_rec, shot_rec):
    global M2mRemoteOrder

    return M2K_GetParameter5xShortParamShortReturn(clientsocket, M2mRemoteOrder.GetNbChannelsTransmission, salvo,
        sequence, shot, Sequence_rec, shot_rec)


##############################################################################
##############################################################################
##############################################################################

def M2K_GetNbChannelsReception(clientsocket, salvo, sequence, shot):
    global M2mRemoteOrder

    return M2K_GetParameter3xShortParamShortReturn(clientsocket, M2mRemoteOrder.GetNbChannelsReception, salvo, sequence,
                                                   shot)


def M2K_GetNbChannelsReceptionMultiple(clientsocket, salvo, sequence, shot,sequence_recons,shot_recons):
    global M2mRemoteOrder

    return M2K_GetParameter5xShortParamShortReturn(clientsocket, M2mRemoteOrder.GetNbChannelsReception, salvo, sequence,
                                                   shot,sequence_recons,shot_recons)



##############################################################################

##############################################################################


#declare parameter list of standard Parameter objects for automatic GUI


def M2m_init_parameter_list():
    global M2mRemoteOrder
    global M2mSystemProperties

    M2mParameterList = []
    # create object list of parameter in list
    # order_name, unit, num_order, min, max):
    order = 0
    M2mParameterList.append(M2mParameter("Voltage", "V", order, 10, 200));
    order += 1
    M2mParameterList.append(M2mParameter("Sampling Freq", "MHz", order, 10, 100));
    order += 1
    M2mParameterList.append(M2mParameter("Pulse Width", "ns", order, 20, 600));
    order += 1
    M2mParameterList.append(M2mParameter("Transmission Delay", "µs", order, 0, 1000));
    order += 1
    M2mParameterList.append(M2mParameter("Reception Delay", "µs", order, 0, 1000));
    order += 1
    M2mParameterList.append(M2mParameter("Transmission Enabled", "", order, 0, 1));
    order += 1
    M2mParameterList.append(M2mParameter("channel by channel Gain", "dB", order, 0, 80));
    order = order + 1
    M2mParameterList.append(M2mParameter("Num Gain", "dB", order, 0, 80));
    order = order + 1
    M2mParameterList.append(M2mParameter("PRF", "Hz", order, 10, 30000));
    order += 1
    M2mParameterList.append(M2mParameter("Digitizing Delay", "µs", order, 0, 1300000));
    order += 1
    M2mParameterList.append(M2mParameter("Digitizing Lengh", "µs", order, 0, 1300000));
    order += 1
    M2mParameterList.append(M2mParameter("Rectified", "", order, 0, 1));
    order += 1
    M2mParameterList.append(M2mParameter("Average Sum", "", order, 0, 1));
    order += 1
    M2mParameterList.append(M2mParameter("Synchro Display", "", order, 0, 1));
    order += 1
    M2mParameterList.append(M2mParameter("Reception Enabled", "", order, 0, 1));
    order += 1
    M2mParameterList.append(M2mParameter("General Gain", "dB", order, 0, 80));
    order += 1
    M2mParameterList.append(M2mParameter("PRF Low Limit", "Hz", order, 0, 1));
    order += 1
    M2mParameterList.append(M2mParameter("Reception element Number", "", order, 0, 128));
    order += 1
    M2mParameterList.append(M2mParameter("Transmission element Number", "", order, 0, 128));
    order += 1
    M2mParameterList.append(M2mParameter("PRF High Limit", "Hz", order, 0, 30000));
    order += 1

    return M2mParameterList

#############################################################################################################
##//////////////////////////////////////////////\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
##                                Main M2K class
##\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\/////////////////////////////////////////////////////////////
#############################################################################################################


class M2k_system:
    def __init__(self):
        try:
            temps = time.perf_counter()
        except:
            time.perf_counter=time.clock


        #print ("time.clock(): "+str(time.clock()))
        print ("time.perf_counter(): ",time.perf_counter())

        self.ParameterList = M2m_init_parameter_list()

        self.socket = M2mSocket()

        self.data_server_socket = M2mSocket()
        self.data_pos_server_socket = M2mSocket()


        self.connected = 0


        self.updated = 0
        self.data_server_connected = 0
        self.data_pos_server_connected = 0


        self.nb_system_connected = 0
        self.type_system_connected = 0
        self.IsMultipleReconstruction = 0
        self.nb_salvo = 0
        self.nb_sequences = []
        self.nb_gates = []
        self.nb_shots = []
        self.nb_elements_transmission_for_shot = []
        self.nb_elements_reception_for_shot = []
        self.inputs_available = 0
        self.nb_mechanical_positions = 0
        self.nb_carto_position_acqui=0
        self.nb_codeurs_sup_acqui=0


        self.scanning_end = 0
        self.scanning_step = 0
        self.scanning_begin = 0

        self.ListSystemsSN = []
        self.ListSystemsName = []
        self.ListSystemsIsHDAutorized = []
        self.ListSystemsFirstInput = []
        self.ListSystemsFirstOutput = []
        self.ListSystemsIsDefaultDevice = []
        self.ListSystemsIsMasterDevice = []
        self.ListSystemsIsDeviceSynchronized = []
        self.ListSystemsDeviceType = []
        self.NameOfTheConfiguration = ""
        self.Multi2000Version = ""
        self.excel = 0
        self.xls = 0
        self.xls_open = 0
        self.xls_line = 1
        self.xls_col = 1
        self.ws = 0
        self.M2000_invisible = 0
        self.nb_parameters = 20
        self.verbose = 0
        self.text_status = ""
        self.error_status = 0

    ###########################################################################################
    ### get information about error status
    #        0: Ok.
    #        1: No conﬁguration loaded.
    #        2: No active UT setting.
    #        3: acquisition in process.
    #        4: adjustment in process.
    ###########################################################################################

    def get_status_error(self):
        global M2mRemoteOrder

        if self.socket.M2000_Remote_Secure_Mode:
            a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetStatusOrError,int(0))
            self.socket.M2mSend(a)  # send the message

            if self.socket.M2mSecureReceive(-1) == 0:   # wait for return value (success or not)

                self.error_status = int(struct.unpack('>h',self.socket.retour[0:2])[0])
                stringsize=int(struct.unpack('>h',self.socket.retour[2:4])[0])
                #return fist is length of string
                self.text_status = ""
                if stringsize > 0:
                    self.text_status = self.socket.retour[4:]

        else:
            a = struct.pack('>h', M2mRemoteOrder.GetStatusOrError)
            self.socket.M2mSend(a)

            retour = self.socket.M2MReceive(2)
            self.error_status = int(struct.unpack('>h', retour)[0])

            retour = self.socket.M2MReceive(2)
            retour = int(struct.unpack('>h', retour)[0])
            #return fist is length of string
            self.text_status = ""
            if retour > 0:
                self.text_status = self.socket.M2MReceive(retour)

        return self.text_status

    def set_ip_data_server(self, ip_address, port):
        if self.connected:
            self.disconnect()

        self.IP_Address = str.split(ip_address, ".")
        for i in range(0, 4):
            self.IP_Address[i] = int(self.IP_Address[i])
        self.port_data_server = port

    def set_ip_data_pos_server(self, ip_address, port):
        if self.connected:
            self.disconnect()

        self.IP_Address = str.split(ip_address, ".")
        for i in range(0, 4):
            self.IP_Address[i] = int(self.IP_Address[i])
        self.port_data_pos_server = port


    def set_ip(self, ip_address, port):
        if self.connected:
            self.disconnect()

        self.IP_Address = str.split(ip_address, ".")
        for i in range(0, 4):
            self.IP_Address[i] = int(self.IP_Address[i])
        self.port = port

    def connect(self):

        address_ip = str(self.IP_Address[0]) + "." + str(self.IP_Address[1]) + "." + str(
            self.IP_Address[2]) + "." + str(self.IP_Address[3])
        try:
            self.connected = self.socket.connect(address_ip, self.port)
            self.socket.sock.setblocking(True)
        except:
            print ("Impossible to connect to: ", address_ip, ":", self.port)
            print ("Check adress and if remote server connexion enabled in M2000 Software")
            self.connected = False
        else:
            self.connected = True
            self.updated = 0

        print ("Remote Connected: ", self.connected)
        if self.connected:
            if self.get_EndOfMulti2000Initialisation() == 0:
                print ("Error: M2M SW not ready")
                return

            self.set_socket_time_out(30000)



    def connect_data_server(self):
        if self.data_server_connected != 0:
            print ("Already connected to data server")
            return

        address_ip = str(self.IP_Address[0]) + "." + str(self.IP_Address[1]) + "." + str(
            self.IP_Address[2]) + "." + str(self.IP_Address[3])
        try:
            self.data_server_connected = self.data_server_socket.connect(address_ip, self.port_data_server)
            self.data_server_socket.sock.setblocking(False)
        except:
            print ("Impossible to connect to: ", address_ip, ":", self.port_data_server, "Error:", str(self.data_server_socket.error))
            print ("Check adress and if data server connexion enabled in M2000 Software")
            self.data_server_connected = False
        else:
            self.data_server_connected = True

        print ("Data Server Connected: ", self.data_server_connected)

    def connect_data_pos_server(self):
        if self.data_pos_server_connected != 0:
            print ("Already connected to data positionning server")
            return

        address_ip = str(self.IP_Address[0]) + "." + str(self.IP_Address[1]) + "." + str(
            self.IP_Address[2]) + "." + str(self.IP_Address[3])
        try:
            self.data_pos_port_server_connected = self.data_pos_server_socket.connect(address_ip, self.port_data_pos_server)
            self.data_pos_server_socket.sock.setblocking(False)
        except:
            print ("Impossible to connect to: ", address_ip, ":", self.port_data_pos_server, "Error:", str(self.data_pos_server_socket.error))
            print ("Check adress and if data server connexion enabled in M2000 Software")
            self.data_pos_server_connected = False
        else:
            self.data_pos_server_connected = True

        print ("Data positionning Server Connected: ", self.data_pos_server_connected)


    def disconnect(self):
        if self.connected != 0:
            M2K_GoodBye(self.socket)
            self.socket.close()
        else:
            print ("Connect to M2M before")

        self.connected = 0
        self.nb_system_connected = 0
        self.updated = 0
        self.disconnect_data_server()
        #after disconnect, you have to recreate a new socket object : m2m_system.socket = M2mSocket()

    def disconnect_data_server(self):
        if self.data_server_connected != 0:
            self.data_server_socket.close()
        else:
            print ("Connect to data_ server M2M before")

        self.data_server_connected = 0
        #after disconnect, you have to recreate a new socket object : m2m_system.data_server_socket = M2mSocket()

    def raz_encoder(self, num_encoder):

        M2K_SetParameterShortParamNoReturn(self.socket, M2mRemoteOrder.RazEncoder, num_encoder)

    def raz_encoder_sync(self, num_encoder):

        M2K_SetParameterShortParamShortReturn(self.socket, M2mRemoteOrder.RazEncoderSync, num_encoder)


    ###################################################################################
    # quiet mode is unvisible mode of M2M SW
    # when used in unvisible mode and parameters modified,
    # problem can occur if switch off visible mode because of unrefreshed parameters.
    def set_quiet_mode(self, on_off):
        M2K_SetParameterShortParamNoReturn(self.socket, M2mRemoteOrder.SetQuietMode, on_off)
        self.M2000_invisible = on_off

    ##################################################################################
    #### secure mode is implemented only after version 8.4 . It helps to check dialog coherence sending frame size
    def get_EndOfMulti2000Initialisation(self):
        a = self.socket.M2000_Remote_Secure_Mode
        # This function is never in secure mode
        self.socket.M2000_Remote_Secure_Mode = 0
        b = M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.EndOfMulti2000Initialisation )
        if b == 2:
            self.socket.M2000_Remote_Secure_Mode = True

        print ("Secure Mode : ",self.socket.M2000_Remote_Secure_Mode)
        return b

    def exit_application(self):
        M2K_SetParameterNoParamNoReturn(self.socket, M2mRemoteOrder.ExitApplication)

    def execute_file(self,filename):
        return M2K_SetParameterStringParamShortReturn(self.socket,M2mRemoteOrder.ExcuteFile,filename)


    ##################################################################################
    # only avalable if in secure mode
    def set_socket_time_out(self, time_out_ms):

        if self.socket.M2000_Remote_Secure_Mode:
            M2K_SetParameterIntParamShortReturn(self.socket, M2mRemoteOrder.SetSocketTimeOut,time_out_ms)
            print ("Time out (ms) : ",time_out_ms)


    ###################################################################################
    # Switch M2000 SW in setting menu
    # it can be necessary because some actions are only working in this mode.
    def show_settings(self):
        return M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.ShowReglage)

    ###################################################################################
    # change displayed Ascan
    def set_current_ascan_display(self, salvo,sequence,shot,channel):
        return M2K_GetParameter4xShortParamShortReturn(self.socket, M2mRemoteOrder.SetCurrentAscanDisplay,salvo,sequence,shot,channel)


    ###################################################################################
    # Switch to acquisition menu and start M20000 acquisition
    def start_acqui(self):
        return M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.StartAcquisition)

    def reset_acqui(self):
        return M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.ResetAcquisition)


    ###################################################################################
    # stops Acquisition process in M2000 SW. Data aren't save automatically and muse be
    def stop_acqui(self):
        return M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.StopAcquisition)

    ###################################################################################
    # Pause Acquisition data transfer process in M2000 SW. HW is not paused
    def acqui_pause_data_transfer(self):
        return M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.PauseTransfert)

    def acqui_pause_hardware_acqui(self):
        return M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.PauseHardwareAcqui)

    ###################################################################################
    # Restart Acquisition data transfer process in M2000 SW. HW is not paused
    def acqui_restart_data_transfer(self):
        return M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.RepriseTransfert)

    def acqui_restart_hardware_acqui(self):
        return M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.RepriseHardwareAcqui)

    def set_data_positioning_server_send_always_ad(self,salvo,status):
        M2K_SetParameter2xShortParamNoReturn( self.socket,M2mRemoteOrder.SetDataPositioningServerSendAlwaysAD,salvo,status)

    ###################################################################################
    # Set the End Auto on/off in trajectory
    def set_acqui_end_auto(self, value):
        return M2K_GetParameterShortParamShortReturn(self.socket, M2mRemoteOrder.SetAcquiEndAuto, value)

    ###################################################################################
    # Set the scanning trajectory along or accross

    def set_scanning_Orientation(self,scanning_orientation):
        return M2K_GetParameterShortParamShortReturn(self.socket, M2mRemoteOrder.SetScanningOrientation, scanning_orientation)

    ###################################################################################
    # get information of offset for each virtual probe

    def get_virtual_probe_position (self,salvo):
        return M2K_GetVpParamIntFloatArrayReturn(self.socket,M2mRemoteOrder.GetVirtualProbePosition, salvo)

    ###################################################################################
    # TFM informations

    def get_TFM_Mode(self, salvo):
        return M2K_GetParameterShortParamShortReturn(self.socket, M2mRemoteOrder.GetTFMMode, salvo)

    def get_is_Gate_Store_TFM(self, salvo):
        return M2K_GetParameterShortParamShortReturn(self.socket, M2mRemoteOrder.IsGateStoreTFM, salvo)

    ###################################################################################
    # next functions set trajectory parameters

    def set_encoder_storage(self, encoder_index, enable):
        return M2K_SetParameter2xShortParamShortReturn(self.socket, M2mRemoteOrder.SetEncoderStorage, encoder_index,enable)

    def set_robot(self,filename):
        return M2K_SetParameterStringParamShortReturn(self.socket, M2mRemoteOrder.SetRobot, filename)

    def set_transformer_property( self, string_property, string_value, trajectory_index ):
        M2K_SetTransformerProperty(self.socket,M2mRemoteOrder.SetTransformerProperty, string_property, string_value, trajectory_index )

    def get_transformer_property(self, string_property):
        return M2K_GetParameterStringParamStringReturn( self.socket, M2mRemoteOrder.GetTransformerProperty, string_property)

    def get_dynamic_amplitude(self):
        return M2K_GetParameterNoParamFloatReturn(self.socket, M2mRemoteOrder.GetDynamicAmplitude)

    def get_scanning_step(self):
        return M2K_GetParameterNoParamFloatReturn(self.socket, M2mRemoteOrder.GetScanningStep)

    def get_incremental_step(self):
        return M2K_GetParameterNoParamFloatReturn(self.socket, M2mRemoteOrder.GetIncrementalStep)

    def get_incremental_begin(self):
        return M2K_GetParameterNoParamFloatReturn(self.socket, M2mRemoteOrder.GetIncrementalBegin)

    def get_incremental_end(self):
        return M2K_GetParameterNoParamFloatReturn(self.socket, M2mRemoteOrder.GetIncrementalEnd)

    def get_scanning_begin(self):
        return M2K_GetParameterNoParamFloatReturn(self.socket, M2mRemoteOrder.GetScanningBegin)

    def get_salvo_offset(self,salvo):
        return M2K_GetParameterShortParam2xFloatReturn(self.socket, M2mRemoteOrder.GetSalvoOffset,salvo)

    def get_scanning_end(self):
        return M2K_GetParameterNoParamFloatReturn(self.socket, M2mRemoteOrder.GetScanningEnd)

    def get_incremental_axis(self):
        return M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.GetIncrementalAxis)

    def get_scanning_axis(self):
        return M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.GetScanningAxis)

    def set_resolution_encoder(self,encoder,value):
        M2K_SetParameterShortParamFloatParamNoReturn(self.socket,M2mRemoteOrder.SetResolutionCoder,encoder,value)

    def set_modulo_encoder(self,encoder,value):
        M2K_SetParameterShortParamFloatParamNoReturn(self.socket,M2mRemoteOrder.SetModuloCoder,encoder,value)

    def set_offset_encoder(self,encoder,value):
        M2K_SetParameterShortParamFloatParamNoReturn(self.socket,M2mRemoteOrder.SetOffsetCoder,encoder,value)

    def set_incremental_step(self,value):
        return M2K_GetParameterFloatParamFloatReturn(self.socket,M2mRemoteOrder.SetIncrementalStep,value)

    def set_scanning_step(self,value):
        return M2K_GetParameterFloatParamFloatReturn(self.socket,M2mRemoteOrder.SetScanningStep,value)

    def set_incremental_begin(self,value):
        return M2K_SetParameterFloatParamNoReturn(self.socket,M2mRemoteOrder.SetIncrementalBegin,value)

    def set_scanning_begin(self,value):
        M2K_SetParameterFloatParamNoReturn(self.socket,M2mRemoteOrder.SetScanningBegin,value)

    def set_incremental_end(self,value):
        M2K_SetParameterFloatParamNoReturn(self.socket,M2mRemoteOrder.SetIncrementalEnd,value)

    def set_scanning_end(self,value):
        M2K_SetParameterFloatParamNoReturn(self.socket,M2mRemoteOrder.SetScanningEnd,value)

    def set_movement_speed_trajectory(self, trajectory_index, speed):
        M2K_SetParameterShortParamFloatParamNoReturn(self.socket,M2mRemoteOrder.SetMovementSpeedTrajectory, int(trajectory_index),float(speed))

    def set_dac_num_common(self, common):
        M2K_SetParameterShortParamNoReturn(self.socket,M2mRemoteOrder.SetDacNumCommon,common)

    def set_dac_state(self, value):
        M2K_SetParameterShortParamNoReturn(self.socket,M2mRemoteOrder.SetDacState,value)

    def get_gate_dac_common_gain_after(self):
        return M2K_GetParameterNoParamShortReturn(self.socket,M2mRemoteOrder.GetGateDacCommonGainAfter)

    def set_gate_dac_common_gain_after(self,common):
        M2K_SetParameterShortParamNoReturn(self.socket,M2mRemoteOrder.SetGateDacCommonGainAfter,common)

    def is_error_to_start_acquisition(self):
        return M2K_GetParameterNoParamShortReturn(self.socket,M2mRemoteOrder.IsErrorToStartAcquisition)

    def get_material_velocity(self,salvo):
        return float(M2K_GetParameterShortParamDoubleReturn(self.socket,M2mRemoteOrder.GetMaterialVelocity,salvo))

    def get_nb_octet_ready_for_Fifo(self, Fifo_type, device_serial  ):

        #   Fifo AD : 0
        #   Fifo Data 1
        #   Fifo Desc 2

        # per devioe :
        # FifoIn : 3,
        # Fifo HW 4

        return M2K_GetParameter2xShortParam2xIntReturn( self.socket, M2mRemoteOrder.GetNbOctetReadyForFifo, Fifo_type, device_serial)


    def get_coeff_pt_to_microSec(self,salvo):
        return M2K_GetParameterShortParamDoubleReturn(self.socket, M2mRemoteOrder.GetCoeffPtToMicroSec, salvo)


    def message_error_to_start_acquisition(self,error_number):
        error_messages=["Unknown error","PRF too low","Speed too fast","data ﬂow too high: USB reading ﬂow","data ﬂow too high: writing ﬂow","no gate deﬁned","Hard gate and subtraction","Elementary Ascan too long for acquisition","Width equal to 0 of at least one gate"]
        string_error=""
        error_bit=1
        # scan all error messages
        for i in range(0,len(error_messages)):
            #test if bit is active
            if(error_number & error_bit):
                string_error=string_error+", "+ error_messages[i]
            #shift error bit
            error_bit=error_bit<<1

        return string_error


    ###########################################################################################
    # get encoder value. Doesn't work during acquisition
    def get_current_value_coder(self, num_coder):
        return M2K_GetCurrentValueCoder(self.socket, num_coder)

    ###########################################################################################
    # next functions are necessary for acquisition to know how many data to retrieve
    def get_inputs_available(self):
        return M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.GetInputsAvailable)

    def get_nb_mechanical_positions(self):
        return M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.GetNbMechanicalPositions)

    def get_nb_carto_position_acqui(self):
        return M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.GetNbCartoPositionAcqui)

    def get_nb_codeurs_sup_acqui(self):
        return M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.GetNbCodeursSupAcqui)

    ############################################################################################
    # #Civa

    def get_specimen_type(self,salvo):
        return M2K_GetParameterShortParamShortReturn(self.socket,M2mRemoteOrder.GetSpecimenType,salvo )

    def set_cylindrical_dimension(self,salvo,outer_diam,length,thickness,angular_sector):
        return M2K_GetParameterShort4xFloatParamShortReturn(self.socket,M2mRemoteOrder.SetCylindricalDimension, salvo,outer_diam,length,thickness,angular_sector)

    def compute_civa_laws(self,salvo):
        return M2K_SetParameter2xShortParamShortReturn(self.socket,M2mRemoteOrder.ComputeCivaLaws,salvo,0)

    def set_velocity(self,salvo,velocity_type,longitudinal_value,transversal_value):
        M2K_GetParameter2xShort2xfloatParamShortReturn(self.socket,M2mRemoteOrder.SetVelocity,salvo,velocity_type,longitudinal_value,transversal_value)


    ############################################################################################
    # to know if acquisition have started or not, is finished or not
    def is_acquisition_running(self):
        return M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.IsAcquisitionRunning)

    ############################################################################################
    # get status information about DAC
    # applies in function of selecteddacaction... on analog, digital...
    def is_dac_active(self):
        return M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.GetDacState)

    def get_hardware_connected_type(self):
        self.connected_type = M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.GetHardwareConnectedType)
        return self.connected_type

    def get_hardware_max_nb_channels(self):
        self.hardware_max_nb_channels = M2K_GetParameterNoParamShortReturn(self.socket,
                                                                           M2mRemoteOrder.GetHardwareMaxNbChannels)
        if self.connected_type == 4:
            self.nb_channels_total = self.hardware_max_nb_channels * 8
        elif self.connected_type == 3:
            self.nb_channels_total = 64
        elif self.connected_type == 5:
            self.nb_channels_total = 32
        else:
            self.nb_channels_total = self.hardware_max_nb_channels

        return self.hardware_max_nb_channels

    ###############################################################################################
    # nb of gates on the setting (depends on salvo)
    def get_nb_gates(self, salvo):
        return M2K_GetParameterShortParamShortReturn(self.socket, M2mRemoteOrder.GetNbGates, salvo)

    def get_start_gate_ms(self,salvo,gate):
        #work only if the gate start is common on the salvo
        return M2K_GetParameter2xShortParamFloatReturn(self.socket, M2mRemoteOrder.GetStartGateMs, salvo,gate)

    def get_width_gate_ms(self,salvo,gate):
        #work only if the gate start is common on the salvo
        return M2K_GetParameter2xShortParamFloatReturn(self.socket, M2mRemoteOrder.GetWidthGateMs, salvo,gate)


    def get_heigth_gate_pcent(self,salvo,gate):
        #work only if the gate start is common on the salvo
        return M2K_GetParameter2xShortParamFloatReturn(self.socket, M2mRemoteOrder.GetHeightGatePcent, salvo,gate)



    def get_gate_name(self,salvo,gate_num):
        return M2K_GetParameter2xshortParamStringReturn(self.socket, M2mRemoteOrder.GetGateName ,salvo, gate_num)

    ###############################################################################################
    # multiple peaks gate have several results to read.
    def get_nb_echo_in_gate(self, salvo, gate):
        return M2K_GetParameter2xShortParamShortReturn(self.socket, M2mRemoteOrder.GetNbEchoInGate, salvo, gate)

    ###############################################################################################
    # Get information if the gate store the summation (only SW gate, selected by user in the setting menu)
    def is_gate_store_sum(self, salvo, gate):
        return M2K_GetParameter2xShortParamShortReturn(self.socket, M2mRemoteOrder.IsGateStoreSum, salvo, gate)

    ###############################################################################################
    # Get information if the gate store the elementary channels (only SW gate, selected by user in the setting menu)
    def is_gate_store_elem(self, salvo, gate):
        return M2K_GetParameter2xShortParamShortReturn(self.socket, M2mRemoteOrder.IsGateStoreElem, salvo, gate)

    def is_gate_store_AD(self, salvo, gate):
        return M2K_GetParameter2xShortParamShortReturn(self.socket, M2mRemoteOrder.IsGateStoreAD, salvo, gate)

    def get_nb_datas_in_gate(self, salvo, gate):
        return M2K_GetParameter2xShortParamShortReturn(self.socket, M2mRemoteOrder.GetNbDatasInGate, salvo, gate)

    def is_gate_shot_by_shot_mode(self,salvo,gate):
        return M2K_GetParameter2xShortParamShortReturn(self.socket, M2mRemoteOrder.IsGateShotByShotMode, salvo, gate)

    def get_data_type_in_gate(self, salvo, gate, num_data):
        return M2K_GetParameter3xShortParamShortReturn(self.socket, M2mRemoteOrder.GetDataTypeInGate, salvo, gate,
                                                       num_data)

    def get_data_size_in_gate(self, salvo, gate, num_data):
        return M2K_GetParameter3xShortParamLongReturn(self.socket, M2mRemoteOrder.GetDataSizeInGate, salvo, gate,
                                                      num_data)

    ###############################################################################################

    def get_list_view(self):
        return M2K_GetParameterNoParamStringReturn(self.socket, M2mRemoteOrder.ListViews)

    def get_image_from_view(self,view_name,view_type):
        return M2K_GetParameter2xStringParamIntArrayReturn(self.socket, M2mRemoteOrder.GetImageFromView, view_name,view_type)

    def get_cursor_properties(self):
        return M2K_GetParameterNoParamStringReturn(self.socket,M2mRemoteOrder.GetCursorProperties)

    def get_list_views(self):
        return M2K_GetParameterNoParamStringReturn(self.socket,M2mRemoteOrder.ListViews)

    def report_open_dialog_box(self, output_pdf_name, template_name, speciment_name, controler_name, pdf_path_name ):
        return M2K_ReportOpenDialogBox(self.socket, M2mRemoteOrder.ReportOpenDialogBox, output_pdf_name, template_name, speciment_name, controler_name, pdf_path_name )


    def close_dialog_box(self):
        return M2K_GetParameterNoParamIntReturn(self.socket, M2mRemoteOrder.ReportCloseDialogBox )

    def report_generation(self):
        return M2K_GetParameterNoParamIntReturn(self.socket, M2mRemoteOrder.ReportGeneration )

    def get_nb_system_connected(self):
        return M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.GetNbSystemConnected)

    ###############################################################################################
    ##DDF Section

    def get_DDF_segments_nb(self,salvo):
        return M2K_GetParameterShortParamShortReturn(self.socket, M2mRemoteOrder.GetDDFSegmentsNb, salvo)

    ##############################################################################
    def get_current_ad_gate(self):

        if self.socket.M2000_Remote_Secure_Mode == True:
            a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetCurrentADGate,int(0))
            self.socket.M2mSend(a)
            quantity_of_data=0
            for salvo in range(0, self.Nb_Salvos):
                for seq in range(0, self.digital_salvoes[salvo].nb_sequences):
                    for shot in range(0, self.digital_salvoes[salvo].sequences[seq].nb_shots):
                        for gate in range (0,self.digital_salvoes[salvo].nb_gates):
                            quantity_of_data+=4*self.digital_salvoes[salvo].gates[gate].nb_echo_in_gate

            offset=0
            retour = self.socket.M2mSecureReceive(quantity_of_data)
            self.nb_gate_results=int(quantity_of_data/4)
            self.gate_amplitudes=[]
            self.gate_TOF=[]

            if self.updated == True:
                for i in range(0,self.nb_gate_results ):
                    self.gate_amplitudes.append( int(struct.unpack('<h', self.socket.retour[offset:offset+2])[0]))
                    offset+=2
                    self.gate_TOF.append( int(struct.unpack('<h', self.socket.retour[offset:offset+2])[0]))
                    offset+=2
            else:
                print ("please Update configuration before use get_current_as_gate")
        else:
            print ("get_current_as_gate not managed in unsecured mode")

    ##############################################################################
    #### get the information on connected system and device communication
    ##############################################################################

    def Get_System_State(self):
        global M2mRemoteOrder

        if self.socket.M2000_Remote_Secure_Mode:

            a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.GetSystemState,int(0))
            self.socket.M2mSend(a)
            retour=self.socket.M2mSecureReceive(-1)

            if retour == 0 or retour == -1: #bug on Acquire side
                self.number_of_systems = int(struct.unpack('>h', self.socket.retour[0:2])[0])
                offset=2

                self.system_state_SN=[]
                self.system_state_STATUS=[]

                if self.number_of_systems > 0:
                    for i in range(0, self.number_of_systems):
                        self.system_state_SN.append( int(struct.unpack('>i', self.socket.retour[offset:offset+4])[0]))
                        offset+=4
                        self.system_state_STATUS.append(int(struct.unpack('>i', self.socket.retour[offset:offset+4])[0]))
                        offset+=4
            else:
                print ("Communication Socket Error: ", self.socket.return_status)
                return 0

        else:
            a = struct.pack('>h', M2mRemoteOrder.GetSystemState)
            self.socket.M2mSend(a)

            retour = self.socket.M2MReceive(2)

            self.number_of_systems =  int(struct.unpack('>h', retour)[0])

            retour = self.socket.M2MReceive(2)

            self.system_state_SN=[]
            self.system_state_STATUS=[]

            if self.number_of_systems > 0:
                for i in range(0, self.number_of_systems):
                    retour = self.socket.M2MReceive(4)
                    self.system_state_SN.append(int(struct.unpack('>i', retour)[0]))

                    retour = self.socket.M2MReceive(4)
                    self.system_state_STATUS.append(int(struct.unpack('>i', retour)[0]))

        return


    ##############################################################################
    #### get the information on acquisition and device connection
    ##############################################################################

    def Get_Is_All_Datas_Acquired(self):
        global M2mRemoteOrder

        if self.socket.M2000_Remote_Secure_Mode:

            #bug à corriger

            a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.IsAllDatasAcquired,int(0))
            self.socket.M2mSend(a)


            if self.socket.M2mSecureReceive(-1) == 0:
                self.All_data_Acquired = int(struct.unpack('>h', self.socket.retour[0:2])[0])
                offset=2
                self.number_of_systems = int(struct.unpack('>h', self.socket.retour[offset:offset+2])[0])
                offset+=2
                self.is_all_datas_SN=[]
                self.is_all_datas_INF=[]

                if self.number_of_systems > 0:
                    for i in range(0, self.number_of_systems):
                        self.is_all_datas_INF.append( int(struct.unpack('>h', self.socket.retour[offset:offset+2])[0]))
                        offset+=2
                        self.is_all_datas_SN.append(int(struct.unpack('>h', self.socket.retour[offset:offset+2])[0]))
                        offset+=2
            else:
                print ("Communication Socket Error: ", self.socket.return_status)
                return 0

        else:
            a = struct.pack('>h', M2mRemoteOrder.IsAllDatasAcquired)
            self.socket.M2mSend(a)

            retour = self.socket.M2MReceive(2)

            self.All_data_Acquired =  int(struct.unpack('>h', retour)[0])

            retour = self.socket.M2MReceive(2)

            self.number_of_systems =  int(struct.unpack('>h', retour)[0])
            self.is_all_datas_SN=[]
            self.is_all_datas_INF=[]

            if self.number_of_systems > 0:
                for i in range(0, self.number_of_systems):
                    retour = self.socket.M2MReceive(2)
                    self.is_all_datas_INF.append(int(struct.unpack('>h', retour)[0]))

                    retour = self.socket.M2MReceive(2)
                    self.is_all_datas_SN.append(int(struct.unpack('>h', retour)[0]))

        return


    def SetReceptionElement(self,Salvo,Array):
        return M2K_SetSalvoParamShortArrayReturn(self.socket,M2mRemoteOrder.SetReceptionElement, Salvo, Array)

    def GetReceptionElement(self,Salvo):
        return M2K_GetSalvoParamShortArrayReturn(self.socket,M2mRemoteOrder.GetReceptionElement, Salvo)

    def SetTransmissionnElement(self,Salvo,Array):
        return M2K_SetSalvoParamShortArrayReturn(self.socket,M2mRemoteOrder.SetTransmissionElement, Salvo, Array)

    def GetTransmissionElement(self,Salvo):
        return M2K_GetSalvoParamShortArrayReturn(self.socket,M2mRemoteOrder.GetTransmissionElement, Salvo)


    ##############################################################################
    #### get the information on acquisition and device connection
    ##############################################################################

    def Set_Digit_Gain_Delta(self,Salvo,ArraySize,DeltaGainPerSignalArray):
        global M2mRemoteOrder

        if self.socket.M2000_Remote_Secure_Mode:
            data_size=(ArraySize)*8+2+4
            a = struct.pack('>Hhihi', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.SetDigitGainDelta, int(data_size), Salvo, int(ArraySize))
            self.socket.M2mSend(a)

            a=bytes()

            for i in range(0,ArraySize):
                a = a + struct.pack('>d', DeltaGainPerSignalArray[i])

            self.socket.M2mSend(a)


            if self.socket.M2mSecureReceive(6) == 0:
                status = int(struct.unpack('>h', self.socket.retour[0:2])[0])
                offset=2
                array_length = int(struct.unpack('>i', self.socket.retour[offset:offset+4])[0])

                if status == -1:
                    print ("Set_Digit_Gain_Delta Error")
                elif status == -2:
                    print ("Set_Digit_Gain_Delta Error: bad array length")

                if array_length != ArraySize:
                    print ("Error, Array size for Gain not expected: Waiting for ", array_length," Sent: ", ArraySize)
            else:
                print ("Communication Socket Error: ", self.socket.return_status)
                return 0

        else:
            a = struct.pack('>hi', M2mRemoteOrder.SetDigitGainDelta,ArraySize)
            self.socket.M2mSend(a)
            for i in range(0,ArraySize):
                a = a + struct.pack('>f', DeltaGainPerSignalArray[i])

            self.socket.M2mSend(a)

            retour = self.socket.M2MReceive(2)

            status =  int(struct.unpack('>h', retour)[0])

            if status == -1:
                print ("Set_Digit_Gain_Delta Error")
            elif status == -2:
                print ("Set_Digit_Gain_Delta Error: bad array length")

            retour = self.socket.M2MReceive(2)

            array_length =  int(struct.unpack('>h', retour)[0])


        return


    def Set_Gate_Dac_Independant_Gain_After(self,ArraySize,DeltaGainPerSignalArray):
        global M2mRemoteOrder
        status = 0
        if self.socket.M2000_Remote_Secure_Mode:
            data_size=(ArraySize)*4
            a = struct.pack('>Hhi', M2mRemoteOrder.SynchroKeyWord ,M2mRemoteOrder.SetGateDacIndependantGainAfter, int(data_size))
            self.socket.M2mSend(a)

            a=bytes()

            for i in range(0,ArraySize):
                a = a + struct.pack('>f', DeltaGainPerSignalArray[i])

            self.socket.M2mSend(a)


        if self.socket.M2mSecureReceive(2) == 0:
            status = int(struct.unpack('>h', self.socket.retour)[0])

            if status == -1:
                print ("Set_Gate_Dac_Independant_Gain_After Error")
            elif status == -2:
                print ("Set_Gate_Dac_Independant_Gain_After Error: bad array length")

        else:
            print("Set_Gate_Dac_Independant_Gain_After not managed in unsecured mode")

        return status



    ###############################################################################################
    # function wrote to export all read settings in an excel file as demo
    def export_to_excel(self):
        if self.xls_open:
            self.xls.Close()
            self.xls_open = False

        print ("export")
        try:
            self.excel = win32com.client.gencache.EnsureDispatch('Excel.Application')
        except:
            print ("Cannot open Excel...")

        else:
            self.xls = self.excel.Workbooks.Add()
            self.xls_open = True
            self.xls_line = 1
            self.ws = self.xls.ActiveSheet
            self.ws.Name = "Settings"
            self.excel.Visible = True

            self.updated = False
            print ("Excel File Openned, Please Update Now")

    #############################################################################################
    # example which read the excel file and modify the DAC in function of modified values inside

    def update_excel_dac_par(self, cdac, type_par, salvo, seq, shot):
        global M2MDacActionSet

        if type_par == "GAIN":
            xls_line = cdac.xls_line_gain
            xls_col = cdac.xls_col_gain
        else:
            xls_line = cdac.xls_line_pos
            xls_col = cdac.xls_col_pos

        if xls_line:
            update_par = self.ws.Cells(xls_line, 1).Value
            update_par = str(update_par).upper()
            ###########################################################
            # User must put an "X" on the column if data is to update
            if update_par[0] == 'X':
                print ("Update DAC: ", cdac.type, "  Gain, line / col", xls_line, xls_col)
                liste_val = []

                offset = xls_col

                for i in range(0, cdac.nb_of_points):
                    value = str(self.ws.Cells(xls_line, offset + i).Value)
                    value.replace(",", ".")
                    liste_val.append(float(value))
                print (liste_val)
                if cdac.type == "GATE":
                    M2K_SetSelectedDacActionDacGate(self.socket, M2MDacActionSet.DacGate, salvo)
                else:
                    M2K_SetSelectedDacActionDacDigitalDetail(self.socket, salvo, seq, shot, 0, 0)
                #time.sleep(0.05)
                if type_par == "GAIN":
                    M2K_SetDacGains(self.socket, liste_val, cdac.nb_of_points)
                else:
                    M2K_SetDacPositions(self.socket, liste_val, cdac.nb_of_points)
                #time.sleep(0.05)

                self.ws.Cells(xls_line, 1).Value = "U"

    ##########################################################################################
    # an example to show how to modify the number of points in the DAC curve in function of Escal file
    def update_excel_dac_nb_of_points(self, cdac, salvo, seq, shot):
        global M2MDacActionSet

        if cdac.xls_line_nb_points:
            update_par = self.ws.Cells(cdac.xls_line_nb_points, 1)
            update_par = str(update_par).upper()

            ###########################################################
            # User must put an "X" on the column if data is to update
            if update_par[0] == 'X':
                print ("Update DAC  nb points, line/col ", cdac.xls_line_nb_points, cdac.xls_col_nb_points)
                offset = cdac.xls_col_nb_points

                nb_points = self.ws.Cells(cdac.xls_line_nb_points, offset)
                nb_points = int(nb_points)
                print (nb_points, cdac.nb_of_points)
                if nb_points > cdac.nb_of_points:
                    if cdac.type == "GATE":
                        M2K_SetSelectedDacActionDacGate(self.socket, M2MDacActionSet.GateDac, salvo)
                    else:
                        M2K_SetSelectedDacActionDacDigitalDetail(self.socket, salvo, seq, shot, 0, 0)
                    #time.sleep(0.05)
                    for i in range(cdac.nb_of_points, nb_points):
                        M2K_AddDacPoint(self.socket)
                    #time.sleep(0.05)
                    cdac.nb_of_points = nb_points
                    self.ws.Cells(cdac.xls_line_nb_points, 1).Value = "U"
                #time.sleep(0.05)

    #######################################################################################
    # example to read parameters from Excel file and update in the setting
    def import_from_excel(self):
        if self.xls_open != True:
            print ("Excel File must be openned")
            return
        if self.updated != True:
            print ("Please Update before Import")
            return


        # read parameters from excel file who have been exported before
        # stops the sequencer to accelerate operation
        M2K_StopHardAndNoWrite(self.socket)

        print ("Import from Excel")
        if self.xls_open:
            if self.updated:
                #self.digital_salvoes[salvo].gate_dac.xls_line_gain
                #self.digital_salvoes[salvo].sequences[seq].shots[shot].nb_elements_trans
                for salvo in range(0, self.Nb_Salvos):
                    self.update_excel_dac_nb_of_points(self.digital_salvoes[salvo].gate_dac, salvo, 0, 0)
                    self.update_excel_dac_par(self.digital_salvoes[salvo].gate_dac, "GAIN", salvo, 0, 0)
                    self.update_excel_dac_par(self.digital_salvoes[salvo].gate_dac, "POS", salvo, 0, 0)

                    for seq in range(0, self.nb_sequences[salvo]):
                        for shot in range(0, self.digital_salvoes[salvo].sequences[seq].nb_shots):
                            self.update_excel_dac_nb_of_points(
                                self.digital_salvoes[salvo].sequences[seq].shots[shot].digital_dac, salvo, seq, shot)
                            self.update_excel_dac_par(
                                self.digital_salvoes[salvo].sequences[seq].shots[shot].digital_dac, "GAIN", salvo, seq,
                                shot)
                            self.update_excel_dac_par(
                                self.digital_salvoes[salvo].sequences[seq].shots[shot].digital_dac, "POS", salvo, seq,
                                shot)

        M2K_WriteAndStartHard(self.socket)
        print ("Import Finished...Wait until all parameters updated in M2000 (can take long time)")

    #####################################################################################################
    # example which read an amplitude correction matrix in an excel file and correct DAC curve
    # for each aperture / each depth, the DAC gain will be corrected in function of values in the Excel file
    def correct_set_from_excel(self):
        #if self.xls_correct_open:
        #    self.xls_correct.close()
        if self.xls_open != True:
            print ("Excel File must be openned")
            return
        if self.updated != True:
            print ("Please Update before Import")
            return

        print ("Start Correct Set")
        try:
            self.excel_correct = win32com.client.gencache.EnsureDispatch('Excel.Application')
        except:
            print ("Cannot open Excel...")

        else:
            ####### The name of the matric must be "c:\\M2M_correct.xlsx"
            self.xls_correct = self.excel_correct.Workbooks.Open("c:\\M2M_correct.xlsx")
            self.xls_correct_open = True

            self.ws_correct = self.xls_correct.ActiveSheet
            self.ws_correct.Name = "Correct"
            self.excel_correct.Visible = True
            cpt_lines = 2

            for salvo in range(0, self.Nb_Salvos):
                shot = 0
                for seq in range(0, self.nb_sequences[salvo]):
                    cdac = self.digital_salvoes[salvo].sequences[seq].shots[shot].digital_dac
                    for point in range(0, cdac.nb_of_points):
                        correction = self.ws_correct.Cells(cpt_lines, point + 2).Value
                        if type(correction) == float:
                            if correction != 0:
                                cdac.gains[point] += correction
                                self.ws.Cells(cdac.xls_line_gain, cdac.xls_col_gain + point).Value = cdac.gains[point]
                                self.ws.Cells(cdac.xls_line_gain, 1).Value = "X"
                    cpt_lines = cpt_lines + 1


    #######################################################
    # method which do the same thing than "login"
    def log_prep(self):
        if self.connected:
            M2K_login_preparator(self.socket)
        else:
            print ("Connect to M2M before")
        self.updated = 0

    def load_config(self, config_name):
        if self.connected:
            M2K_load_configuration(self.socket, config_name)
            self.updated = 0
        else:
            print ("Connect to M2M before")

    def load_gate(self, salvo, config_name):
        if self.connected:
            return M2K_SetParameterShortStringParamShortStringReturn(self.socket, M2mRemoteOrder.LoadGate, salvo, config_name)

            self.updated = 0
        else:
            print ("Connect to M2M before")


    def __del__(self):
        if self.connected:
            M2K_GoodBye(self.socket)
            self.socket.close()
        self.connected = 0


    ###################################################################################################
    # example which force delay laws values for emit and receive in function of a text file.
    # the delay laws are copied for all sequences at the same values
    # the example manage to have several shots for each sequence
    def force_delay(self):

        # Force a delay law for emition and reception on a single shot of all sequences from a file

        if self.connected == 0:
            print ("You must Connect and update parameters to M2M before")
            return False

        if self.updated == 0:
            print ("You must Update parameters from M2M before")
            return False

        print ("Forced start")

        # Delay laws are loaded from text file
        M2K_StopHardAndNoWrite(self.socket)

        transmit_delay = []
        transmit_delay.append(0)
        reception_delay = []
        reception_delay.append(0)

        try:
            fichier_laws = open("focal_laws_emit.csv")

        except:
            print ("Cannot read focal_laws_emit.csv")
            print ("This file must include number of sequences, number of laws, shot destination number and laws on the same line in this order")
            print ("Separators must be ; decimal can be. or ,")
        else:
            contenu = fichier_laws.read()
            newcont = contenu.replace(',', '.')
            splitted = newcont.split(";")
            nb_sequences_emit_file = int(splitted[0])
            print ("Number of sesquences in file emit: ", nb_sequences_emit_file)
            nb_laws_emit_file = int(splitted[1])
            print ("Laws in file emition: ", nb_laws_emit_file)
            shot_emit_dest_file = int(splitted[2])
            print ("shot destination for emit in file: ", shot_emit_dest_file)
            if len(splitted) != (nb_laws_emit_file + 3):
                print ("WARTNING : Number of delay incoherent with header in emit file")

            numbers = []
            for i in range(0, nb_laws_emit_file):
                numbers.append(float(splitted[i + 3]))
                print ("Focal law emit in file number , value: ", i + 1, numbers[i])
                transmit_delay.append(numbers[i])
            fichier_laws.close()

        try:
            fichier_laws = open("focal_laws_recept.csv")

        except:
            print ("Cannot read focal_laws_recept.csv")
            print ("This file must include number of sequences, number of laws, shot destination number and laws on the same line in this order")
            print ("Separators must be ; decimal can be. or ,")
        else:
            contenu = fichier_laws.read()
            newcont = contenu.replace(',', '.')
            splitted = newcont.split(";")
            nb_sequences_recept_file = int(splitted[0])
            print ("Number of sesquences in file recept: ", nb_sequences_recept_file)
            nb_laws_recept_file = int(splitted[1])
            print ("Laws in file reception: ", nb_laws_recept_file)
            shot_recept_dest_file = int(splitted[2])
            print ("shot destination for recept in file: ", shot_recept_dest_file)

            if len(splitted) != (nb_laws_recept_file + 3):
                print ("WARNING: Number of delay incoherent with header in recept file")

            numbers = []
            for i in range(0, nb_laws_recept_file):
                numbers.append(float(splitted[i + 3]))
                print ("Focal law recept in file number , value: ", i + 1, numbers[i])
                reception_delay.append(numbers[i])
            fichier_laws.close()

        if (self.digital_salvoes[0].sequences[0].shots[0].nb_elements_trans != nb_laws_emit_file):
            print ("WARNING: The number of element in the file emint doesn't match with setting")
        if (self.digital_salvoes[0].sequences[0].shots[0].nb_elements_trans != nb_laws_emit_file):
            print ("WARNING: The number of element in the file recept doesn't match with setting")

        if (self.nb_sequences[0] != nb_sequences_recept_file):
            print ("WARNING: The number of sequences in the file recept doesn't match with setting")
        if (self.nb_sequences[0] != nb_sequences_emit_file):
            print ("WARNING: The number of sequences in the file emit doesn't match with setting")

        for sequence in range(0, nb_sequences_recept_file):
            for element in range(1, self.digital_salvoes[0].sequences[0].shots[0].nb_elements_recep + 1):
                self.ParameterList[4].salvo_number = 0
                self.ParameterList[4].sequence_number = sequence
                self.ParameterList[4].shot_number = shot_recept_dest_file
                self.ParameterList[4].channel_number = element
                self.ParameterList[4].Set_Value(self.socket, reception_delay[element] / 1000.0)
                #self.ParameterList[4].Set_Value(self.socket, element / 100.0 )
                print ("delay: Réception ", self.ParameterList[
                    4].actual_value, " Seq :", sequence, " element : ", element)

        for sequence in range(0, nb_sequences_emit_file):
            for element in range(1, self.digital_salvoes[0].sequences[0].shots[0].nb_elements_trans + 1):
                self.ParameterList[3].salvo_number = 0
                self.ParameterList[3].sequence_number = sequence
                self.ParameterList[3].shot_number = shot_recept_dest_file
                self.ParameterList[3].channel_number = element
                self.ParameterList[3].Set_Value(self.socket, transmit_delay[element] / 1000.0)
                #self.ParameterList[3].Set_Value(self.socket, element / 100.0)
                print ("delay: Transmission ", self.ParameterList[
                    3].actual_value, " Seq :", sequence, " element : ", element)

        M2K_WriteAndStartHard(self.socket)

        print ("Forced Finished...")

    #################################################################################################
    # utility function used in the export function to excel as a "print"
    def append_xls_line(self, value, dir):
        if self.xls_open:
            self.ws.Cells(self.xls_line, self.xls_col).Value = value

        if dir == 'R':
            self.xls_col += 1
        if dir == 'D':
            self.xls_line += 1
            self.xls_col = 2

    ################################################################################################################
    ##### This function ask for M2000 software a lot of parameters to retrieve as deep as possible all #############
    ##### data structure of the setting to use in functions later. It is able to copy settings in an ###############
    ##### Excel file if already opened or print if verbose activated ###############################################
    ##### Some of them can be absolutely necessary to interface with Data_server and know the data structure #######
    ##### to read from the server (nb of salvo, sequences, shots, gates, inputs... #################################
    ################################################################################################################

    def update_all_parameters(self, with_focal_laws, with_dac_curves):
        global M2MDacActionSet, M2m_Connected_Types

        if self.connected != True:
            print ("You must Connect parameters to M2M before")
            return False

        #some parameters are only accessible if in setting menu
        self.show_settings()

        # stop sequencer to accelerate data exchange.
        M2K_StopHardAndNoWrite(self.socket)

        #----------------------------------------------------------
        self.xls_col = 2
        self.xls_line = 1
        #---------------------------------------------------------- GET CHARACTERISTICS FROM ELECTRONICS and SOFTWARE

        self.nb_system_connected = M2K_GetParameterNoParamShortReturn(self.socket, M2mRemoteOrder.GetNbSystemConnected)
        if self.verbose:
            print ("Nb system connected: ", self.nb_system_connected)
        self.append_xls_line("Nb system connected: ", "R")
        self.append_xls_line(self.nb_system_connected, "D")
        self.append_xls_line("System type : ", "R")
        self.append_xls_line(M2m_Connected_Types[self.get_hardware_connected_type() - 2], "D")
        self.append_xls_line("Nb channels aperture max : ", "R")
        self.append_xls_line(self.get_hardware_max_nb_channels(), "D")

        self.NameOfTheConfiguration = M2K_GetNameOfTheConfiguration(self.socket)
        self.Multi2000Version = M2K_GetMulti2000Version(self.socket)
        if self.verbose:
            print ("Name of the current configuration name: ", self.NameOfTheConfiguration)
            print ("Multi 2000 Version : ", self.Multi2000Version)

        self.append_xls_line("Name of the current configuration name: ", "R")
        self.append_xls_line(self.NameOfTheConfiguration, "D")
        self.append_xls_line("Multi2000 Software Version name: ", "R")
        self.append_xls_line(self.Multi2000Version, "D")

        ############ initialise as empty the arrays if the function is used several times ########
        self.ListSystemsProperty = []
        self.ListSystemsIsHDAutorized = []
        self.ListSystemsName = []
        self.ListSystemsFirstInput = []
        self.ListSystemsFirstOutput = []
        self.ListSystemsIsDefaultDevice = []
        self.ListSystemsIsMasterDevice = []
        self.ListSystemsIsDeviceSynchronized = []
        self.ListSystemsDeviceType = []

        for i in range(0, self.nb_system_connected):
            self.ListSystemsSN.append(M2K_GetSystemProperty(self.socket, i, M2mSystemProperties.SerialNumber))
            if self.verbose:
                print ("Serial Number System # ", i, " : ", self.ListSystemsSN[i])
            self.append_xls_line("Serial Number System # ", "R")
            self.append_xls_line(i, "R")
            self.append_xls_line(self.ListSystemsSN[i], "D")

            self.ListSystemsName.append(M2K_GetSystemProperty(self.socket, i, M2mSystemProperties.Name))
            if self.verbose:
                print ("       Name of System # ", i, " : ", self.ListSystemsName[i])
            self.append_xls_line("Name of System # ", "R")
            self.append_xls_line(i, "R")
            self.append_xls_line(self.ListSystemsName[i], "D")

            self.ListSystemsIsHDAutorized.append(
                M2K_GetSystemProperty(self.socket, i, M2mSystemProperties.IsHdAutorized))
            if self.verbose:
                print ("HD Autorized   System # ", i, " : ", self.ListSystemsIsHDAutorized[0])

            self.ListSystemsFirstInput.append(
                M2K_GetSystemProperty(self.socket, i, M2mSystemProperties.IndexFirstInput))
            if self.verbose:
                print ("First Input of System # ", i, " : ", self.ListSystemsFirstInput[0])

            self.ListSystemsFirstOutput.append(
                M2K_GetSystemProperty(self.socket, i, M2mSystemProperties.IndexFirstOutput))
            if self.verbose:
                print ("FirstOutput of System # ", i, " : ", self.ListSystemsFirstOutput[0])

            self.ListSystemsIsDefaultDevice.append(
                M2K_GetSystemProperty(self.socket, i, M2mSystemProperties.IsDefaultDevice))
            if self.verbose:
                print ("Is Defaut Dev. System # ", i, " : ", self.ListSystemsIsDefaultDevice[0])

            self.ListSystemsIsMasterDevice.append(
                M2K_GetSystemProperty(self.socket, i, M2mSystemProperties.IsMasterDevice))
            if self.verbose:
                print ("Is Master Dev. System # ", i, " : ", self.ListSystemsIsMasterDevice[0])

            self.ListSystemsIsDeviceSynchronized.append(
                M2K_GetSystemProperty(self.socket, i, M2mSystemProperties.IsDeviceSynchronized))
            if self.verbose:
                print ("Is Synch. Dev. System # ", i, " : ", self.ListSystemsIsDeviceSynchronized[0])

            self.ListSystemsDeviceType.append(M2K_GetSystemProperty(self.socket, i, M2mSystemProperties.DeviceType))
            if self.verbose:
                print ("Device Type    System # ", i, " : ", self.ListSystemsDeviceType)

        #---------------------------- GET standard parameters (gain, pulse, prf...)
        ################# static parameters of the configuration ################

        self.inputs_available = self.get_inputs_available()
        self.append_xls_line("Imputs Available", "R")
        self.append_xls_line(self.inputs_available, "R")

        self.nb_mechanical_positions = self.get_nb_mechanical_positions()
        self.append_xls_line("nb mechanical positions", "R")
        self.append_xls_line(self.nb_mechanical_positions, "R")

        self.nb_carto_position_acqui = self.get_nb_carto_position_acqui()
        self.append_xls_line("nb carto positions acqui", "R")
        self.append_xls_line(self.nb_carto_position_acqui , "R")

        self.nb_codeurs_sup_acqui = self.get_nb_codeurs_sup_acqui()
        self.append_xls_line("nb codeurs sup acqui", "R")
        self.append_xls_line(self.nb_codeurs_sup_acqui , "D")

        # Bug in version less than 8.1
        if self.nb_mechanical_positions < (self.nb_carto_position_acqui+self.nb_codeurs_sup_acqui):
            self.nb_mechanical_positions = (self.nb_carto_position_acqui+self.nb_codeurs_sup_acqui)


        self.append_xls_line("Nb mechanical positions", "R")
        self.append_xls_line(self.nb_mechanical_positions, "D")

        self.scanning_step = self.get_scanning_step()
        self.append_xls_line("Scanning step", "R")
        self.append_xls_line(self.scanning_step, "D")

        self.scanning_begin = self.get_scanning_begin()
        self.append_xls_line("Scanning begin", "R")
        self.append_xls_line(self.scanning_begin, "D")

        self.scanning_end = self.get_scanning_end()
        self.append_xls_line("Scanning end", "R")
        self.append_xls_line(self.scanning_end, "D")

        #---------------------------- Get if Multiple Reconstruction for devices able to
        # multiple reconstruction consist to create several virtual sequences in reception with the same data
        # already acquired.
        self.IsMultipleReconstruction = M2K_IsMultipleReconstruction(self.socket)
        if self.verbose:
            print ("Reconstruction Multiple: ", self.IsMultipleReconstruction)
        self.append_xls_line("Reconstruction Multiple: ", "R")
        self.append_xls_line(self.IsMultipleReconstruction, "D")

        ################ standard ultrasonic parameters
        # read the parameters in the list
        for i in range(0, self.nb_parameters):
            self.ParameterList[i].is_multiple_reconstruction=self.IsMultipleReconstruction
            self.ParameterList[i].salvo_number = 0
            self.ParameterList[i].sequence_number = 0
            self.ParameterList[i].shot_number = 0
            self.ParameterList[i].channel_number = 0
            self.ParameterList[i].Get_Value(self.socket)
            if i == 1:
                self.sampling_frequency=float(self.ParameterList[i].actual_value)

            self.append_xls_line(self.ParameterList[i].order_name, "R")
            self.append_xls_line(self.ParameterList[i].unit, "R")
            self.append_xls_line(self.ParameterList[i].actual_value, "D")


        #---------------------------- Get SALVOes Characteristics and SETTINGS

        self.Nb_Salvos = M2K_GetNbSalvo(self.socket)
        if self.verbose:
            print ("Nb Salvo(es): ", self.Nb_Salvos)
        self.append_xls_line("Nb Salvo(es): ", "R")
        self.append_xls_line(self.Nb_Salvos, "D")

        self.append_xls_line("SEQ per Salvo(es)", "R")
        self.append_xls_line("SALVO", "R")

        self.append_xls_line("Value(s)", "D")

        self.digital_salvoes = []
        self.nb_gates = []
        self.nb_sequences = []
        self.nb_shots = []

        for salvo in range(0, self.Nb_Salvos):
            self.digital_salvoes.append(Csalvo())
            nb_sequences=M2K_GetNbSequences(self.socket, salvo)
            nb_sequences_recons=M2k_GetNbSequencesRecons(self.socket, salvo,0,0)
            if (nb_sequences_recons > 1 and nb_sequences>1):
                print ("Error: Cannot manage sequences and sequences_req > 1")
                print ("Only managed several sequences and several shots")
                print ("Or reconstruction multiple with one shot and several builds")
            elif nb_sequences>1:
                self.nb_sequences.append(nb_sequences)
            else:
                self.nb_sequences.append(nb_sequences_recons)

            self.nb_gates.append(self.get_nb_gates(salvo))
            self.digital_salvoes[salvo].nb_gates = self.get_nb_gates(salvo)

            if self.verbose:
                print ("NB Sequence(s): ", self.nb_sequences[salvo])
            self.append_xls_line("NB Sequence(s): ", "R")
            self.append_xls_line(salvo, "R")
            self.append_xls_line(self.nb_sequences[salvo], "D")

            #########################################################
            self.digital_salvoes[salvo].total_shots = 0
            self.append_xls_line("NB Shot(s) per seq: ", "R")
            self.append_xls_line(salvo, "R")
            if self.IsMultipleReconstruction:
                for seq in range(0, self.nb_sequences[salvo]):
                    self.digital_salvoes[salvo].add_sequence()
                    self.nb_shots.append(M2k_GetNbShotsRecons(self.socket, salvo, 0, 0,seq))
                    self.digital_salvoes[salvo].total_shots += self.nb_shots[salvo]
                    if self.verbose:
                        print ("NB Shot(s): ", self.nb_shots[salvo])
                    self.append_xls_line(self.nb_shots[salvo], "R")
                #endfor seq
            else:
                for seq in range(0, self.nb_sequences[salvo]):
                    self.digital_salvoes[salvo].add_sequence()
                    self.nb_shots.append(M2K_GetNbShots(self.socket, salvo, seq))
                    self.digital_salvoes[salvo].total_shots += self.nb_shots[salvo]
                    if self.verbose:
                        print ("NB Shot(s): ", self.nb_shots[salvo])
                    self.append_xls_line(self.nb_shots[salvo], "R")
                #endfor seq

            self.append_xls_line("End", "D")
            self.append_xls_line("NB Shot(s) total: ", "R")
            self.append_xls_line(salvo, "R")
            self.append_xls_line(self.digital_salvoes[salvo].total_shots , "D")

            #########################################################
            #### Gates information needed for data acquisition
            #########################################################
            if self.verbose:
                print ("Nb Gate(s): ", self.nb_gates[salvo])
            self.append_xls_line("NB gates(s): ", "R")
            self.append_xls_line(salvo, "R")
            #self.append_xls_line(self.nb_gates[salvo], "D")
            self.append_xls_line(self.digital_salvoes[salvo].nb_gates, "D")

            self.append_xls_line("Salvo", "R")
            self.append_xls_line("Gate", "R")
            self.append_xls_line("nb echo in gate", "R")
            self.append_xls_line("is gate store num", "R")
            self.append_xls_line("is gate store element", "R")
            self.append_xls_line("is gate store ad", "R")
            self.append_xls_line("gate is shot by shot", "R")
            self.append_xls_line("nb data in gate", "R")
            self.append_xls_line("num data in gate", "R")
            self.append_xls_line("data type in gate", "R")
            self.append_xls_line("data size in gate", "R")
            self.append_xls_line("data description", "D")

            for gate in range(0, self.digital_salvoes[salvo].nb_gates):
                self.digital_salvoes[salvo].gates.append(Cgate())
                self.digital_salvoes[salvo].gates[gate].salvo_of_gate = salvo
                self.digital_salvoes[salvo].gates[gate].nb_echo_in_gate = self.get_nb_echo_in_gate(salvo, gate)
                self.digital_salvoes[salvo].gates[gate].is_gate_store_sum = self.is_gate_store_sum(salvo, gate)
                self.digital_salvoes[salvo].gates[gate].is_gate_store_elem = self.is_gate_store_elem(salvo, gate)
                self.digital_salvoes[salvo].gates[gate].is_gate_store_AD = self.is_gate_store_AD(salvo, gate)
                self.digital_salvoes[salvo].gates[gate].is_gate_shot_by_shot_mode = self.is_gate_shot_by_shot_mode(salvo,gate)
                if self.digital_salvoes[salvo].gates[gate].is_gate_shot_by_shot_mode:
                    self.digital_salvoes[salvo].gates[gate].nb_data_peak=self.digital_salvoes[salvo].total_shots
                else:
                    self.digital_salvoes[salvo].gates[gate].nb_data_peak=1
                #endif

                self.digital_salvoes[salvo].gates[gate].nb_datas_in_gate = self.get_nb_datas_in_gate(salvo, gate)
                for num_data in range(0, self.digital_salvoes[salvo].gates[gate].nb_datas_in_gate):
                    self.digital_salvoes[salvo].gates[gate].data_type_in_gate.append(
                        self.get_data_type_in_gate(salvo, gate, num_data))
                    self.digital_salvoes[salvo].gates[gate].data_size_in_gate.append(
                        self.get_data_size_in_gate(salvo, gate, num_data))
                    self.digital_salvoes[salvo].gates[gate].data_description.append(
                        M2K_GetDataDescription(self.socket, salvo, gate, num_data))
                    self.append_xls_line(salvo, "R")
                    self.append_xls_line(gate, "R")
                    self.append_xls_line(self.digital_salvoes[salvo].gates[gate].nb_echo_in_gate, "R")
                    self.append_xls_line(self.digital_salvoes[salvo].gates[gate].is_gate_store_sum, "R")
                    self.append_xls_line(self.digital_salvoes[salvo].gates[gate].is_gate_store_elem, "R")
                    self.append_xls_line(self.digital_salvoes[salvo].gates[gate].is_gate_store_AD, "R")
                    self.append_xls_line(self.digital_salvoes[salvo].gates[gate].is_gate_shot_by_shot_mode, "R")
                    self.append_xls_line(self.digital_salvoes[salvo].gates[gate].nb_datas_in_gate, "R")
                    self.append_xls_line(num_data, "R")
                    self.append_xls_line(self.digital_salvoes[salvo].gates[gate].data_type_in_gate[num_data], "R")
                    self.append_xls_line(self.digital_salvoes[salvo].gates[gate].data_size_in_gate[num_data], "R")
                    self.append_xls_line(self.digital_salvoes[salvo].gates[gate].data_description[num_data], "D")
                #endfor num_data
            #endfor gate
            #---------------------------- GET NB Of Channels per Aperture
            self.append_xls_line("Channel per apperture", "R")
            self.append_xls_line("SALVO", "R")
            self.append_xls_line("SEQ", "R")

            self.append_xls_line("# Channels", "D")


            if self.IsMultipleReconstruction:
                nb_seq = self.nb_sequences[salvo]
                for seq in range(0, nb_seq):
                    self.append_xls_line("nb Transmit Channels: ", "R")
                    self.append_xls_line(salvo, "R")
                    self.append_xls_line(seq, "R")
                    for shot in range(0, self.nb_shots[seq]):
                        self.digital_salvoes[salvo].sequences[seq].add_shot()
                        self.digital_salvoes[salvo].sequences[seq].shots[
                            shot].nb_elements_trans = M2K_GetNbChannelsTransmissionMultiple(self.socket, salvo, 0, 0,seq,0)
                        self.append_xls_line(self.digital_salvoes[salvo].sequences[seq].shots[shot].nb_elements_trans, "R")
                    self.append_xls_line("End", "D")
                #endfor seq
            else:
                nb_seq = self.nb_sequences[salvo]

                for seq in range(0, nb_seq):
                    self.append_xls_line("nb Transmit Channels: ", "R")
                    self.append_xls_line(salvo, "R")
                    self.append_xls_line(seq, "R")
                    for shot in range(0, self.nb_shots[seq]):
                        self.digital_salvoes[salvo].sequences[seq].add_shot()
                        self.digital_salvoes[salvo].sequences[seq].shots[
                            shot].nb_elements_trans = M2K_GetNbChannelsTransmission(self.socket, salvo, seq, 0)
                        self.append_xls_line(self.digital_salvoes[salvo].sequences[seq].shots[shot].nb_elements_trans, "R")
                    self.append_xls_line("End", "D")
                #endfor seq

            for seq in range(0, nb_seq):
                self.append_xls_line("nb Recep Channels: ", "R")
                self.append_xls_line(salvo, "R")
                self.append_xls_line(seq, "R")
                if self.IsMultipleReconstruction == 0:
                    for shot in range(0, self.nb_shots[seq]):
                        self.digital_salvoes[salvo].sequences[seq].shots[
                            shot].nb_elements_recep = M2K_GetNbChannelsReception(self.socket, salvo, seq, 0)
                        self.append_xls_line(self.digital_salvoes[salvo].sequences[seq].shots[shot].nb_elements_recep, "R")
                else:
                    for shot in range(0, self.nb_shots[seq]):
                        self.digital_salvoes[salvo].sequences[seq].shots[
                            shot].nb_elements_recep = M2K_GetNbChannelsReceptionMultiple(self.socket, salvo, 0, 0,seq,0)
                        self.append_xls_line(self.digital_salvoes[salvo].sequences[seq].shots[shot].nb_elements_recep, "R")

                self.append_xls_line("End", "D")

            #endfor seq

            #---------------------------- GET NB Of Delay per Aperture per channel
            if with_focal_laws:
                self.append_xls_line("DELAY LAWS", "R")
                self.append_xls_line("SALVO", "R")
                self.append_xls_line("SEQ", "R")
                self.append_xls_line("SHOT", "R")

                self.append_xls_line("DELAY PARAMETER", "D")

                for seq in range(0, nb_seq):
                    for shot in range(0, self.nb_shots[seq]):
                        self.append_xls_line("Delay Trans:", "R")
                        self.append_xls_line(salvo, "R")
                        self.append_xls_line(seq, "R")
                        self.append_xls_line(shot, "R")

                        for element in range(1,
                                             self.digital_salvoes[salvo].sequences[seq].shots[shot].nb_elements_trans + 1):
                            self.ParameterList[3].salvo_number = salvo
                            self.ParameterList[3].sequence_number = seq
                            self.ParameterList[3].shot_number = shot
                            self.ParameterList[3].channel_number = element
                            self.ParameterList[3].Get_Value(self.socket)
                            self.digital_salvoes[salvo].sequences[seq].shots[shot].delay_trans.append(
                                self.ParameterList[3].actual_value)
                            self.append_xls_line(self.ParameterList[3].actual_value, "R")
                        #endfor element
                        if self.verbose:
                            print ("Delay: Transmission ", self.digital_salvoes[salvo].sequences[seq].shots[
                                shot].elements_trans)
                        self.append_xls_line("End", "D")

                        self.append_xls_line("Delay Recep:", "R")
                        self.append_xls_line(salvo, "R")
                        self.append_xls_line(seq, "R")
                        self.append_xls_line(shot, "R")
                        for element in range(1,
                                             self.digital_salvoes[salvo].sequences[seq].shots[shot].nb_elements_recep + 1):
                            self.ParameterList[4].salvo_number = salvo
                            self.ParameterList[4].sequence_number = seq
                            self.ParameterList[4].shot_number = shot
                            self.ParameterList[4].channel_number = element
                            self.ParameterList[4].Get_Value(self.socket)
                            self.digital_salvoes[salvo].sequences[seq].shots[shot].delay_recep.append(
                                self.ParameterList[4].actual_value)
                            self.append_xls_line(self.ParameterList[4].actual_value, "R")
                        #endfor element
                        if self.verbose:
                            print ("Delay: Reception ", self.ParameterList[4].actual_value)
                        self.append_xls_line("End", "D")
                    #endfor shot
                #endfor seq
            #endif read delay laws
            #---------------------------- GET DAC SETTINGS for GATE DAC
            if with_dac_curves:
                M2K_SetSelectedDacActionDacGate(self.socket, M2MDacActionSet.GateDac, salvo)
                if self.is_dac_active():

                    self.append_xls_line("GATE DAC", "R")
                    self.append_xls_line("SALVO", "R")
                    self.append_xls_line("DAC PARAMETER", "D")

                    gains_list = M2K_GetDacGains(self.socket)
                    self.append_xls_line("GATE DAC NB Points", "R")
                    self.append_xls_line(salvo, "R")

                    self.digital_salvoes[salvo].gate_dac.type = "GATE"
                    self.digital_salvoes[salvo].gate_dac.xls_line_nb_points = self.xls_line
                    self.digital_salvoes[salvo].gate_dac.xls_col_nb_points = self.xls_col
                    self.append_xls_line(len(gains_list), "D")

                    self.append_xls_line("Gains GATE (dB)", "R")
                    self.append_xls_line(salvo, "R")

                    self.digital_salvoes[salvo].gate_dac.xls_line_gain = self.xls_line
                    self.digital_salvoes[salvo].gate_dac.xls_col_gain = self.xls_col
                    for gain in range(0, len(gains_list)):
                        if self.verbose:
                            print ("DAC GATE: gain [", gain + 1, "]: ", gains_list[gain], " dB")
                        self.append_xls_line(gains_list[gain], "R")
                    #endfor gain

                    self.append_xls_line("End", "D")
                    self.append_xls_line("Pos GATE (µS)", "R")
                    self.append_xls_line(salvo, "R")
                    positions_list = M2K_GetDacPositions(self.socket)
                    self.digital_salvoes[salvo].gate_dac.xls_line_pos = self.xls_line
                    self.digital_salvoes[salvo].gate_dac.xls_col_pos = self.xls_col
                    for gain in range(0, len(positions_list)):
                        if self.verbose:
                            print ("DAC GATE: pos [", gain + 1, "]: ", positions_list[gain], " µS")
                        self.append_xls_line(positions_list[gain], "R")

                    self.append_xls_line("End", "D")

                    for gain in range(0, len(positions_list)):
                        self.digital_salvoes[salvo].gate_dac.add_point(positions_list[gain], gains_list[gain])
                    #endfor gain
                #endif dac_active
                #---------------------------- GET DAC PER APERTURE
                self.append_xls_line("GATE DIGITAL", "R")
                self.append_xls_line("SALVO", "R")
                self.append_xls_line("SEQ", "R")
                self.append_xls_line("SHOT", "R")

                self.append_xls_line("DAC PARAMETER", "D")

                for seq in range(0, nb_seq):
                    for shot in range(0, self.nb_shots[seq]):
                        M2K_SetSelectedDacActionDacDigitalDetail(self.socket, salvo, seq, shot, 0, 0)
                        if self.is_dac_active():
                            self.digital_salvoes[salvo].sequences[seq].shots[shot].digital_dac.type = "DIGITAL"
                            gains_list = M2K_GetDacGains(self.socket)
                            self.append_xls_line("GATE DIGITAL NB Points", "R")

                            self.append_xls_line(salvo, "R")
                            self.append_xls_line(seq, "R")
                            self.append_xls_line(shot, "R")
                            self.digital_salvoes[salvo].sequences[seq].shots[
                                shot].digital_dac.xls_line_nb_points = self.xls_line
                            self.digital_salvoes[salvo].sequences[seq].shots[
                                shot].digital_dac.xls_col_nb_points = self.xls_col
                            self.append_xls_line(len(gains_list), "D")

                            self.append_xls_line("Gains DIGITAL (dB)", "R")
                            self.append_xls_line(salvo, "R")
                            self.append_xls_line(seq, "R")
                            self.append_xls_line(shot, "R")
                            self.digital_salvoes[salvo].sequences[seq].shots[shot].digital_dac.xls_line_gain = self.xls_line
                            self.digital_salvoes[salvo].sequences[seq].shots[shot].digital_dac.xls_col_gain = self.xls_col

                            for gain in range(0, len(gains_list)):
                                if self.verbose:
                                    print ("DAC DIGITAL: gain [", gain + 1, "]: ", gains_list[gain], " dB")
                                self.append_xls_line(gains_list[gain], "R")
                            #endfor gain

                            self.append_xls_line("End", "D")
                            self.append_xls_line("Pos DIGITAL (µS)", "R")
                            self.append_xls_line(salvo, "R")
                            self.append_xls_line(seq, "R")
                            self.append_xls_line(shot, "R")
                            positions_list = M2K_GetDacPositions(self.socket)
                            self.digital_salvoes[salvo].sequences[seq].shots[shot].digital_dac.xls_line_pos = self.xls_line
                            self.digital_salvoes[salvo].sequences[seq].shots[shot].digital_dac.xls_col_pos = self.xls_col

                            for gain in range(0, len(positions_list)):
                                if self.verbose:
                                    print ("DAC DIGITAL: pos [", gain + 1, "]: ", positions_list[gain], " µS")
                                self.append_xls_line(positions_list[gain], "R")
                            #endfor gain

                            self.append_xls_line("End", "D")

                            for gain in range(0, len(positions_list)):
                                self.digital_salvoes[salvo].sequences[seq].shots[shot].digital_dac.add_point(
                                   positions_list[gain], gains_list[gain])
                            #endfor gain
                        #endif dac_active
                    #endfor shot
                #endfor seq
            #endif with DAC curve read
        #endfor salvo
        M2K_WriteAndStartHard(self.socket)
        print (self.get_status_error())
        self.updated = True

