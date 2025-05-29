import sys

import datetime as datetime

sys.path.append('/usr/lib/python3.13/dist-packages')
import os

os.environ['LD_LIBRARY_PATH'] = '/usr/lib/python3.13/dist-packages:' + os.environ.get('LD_LIBRARY_PATH', '')
print(os.environ['LD_LIBRARY_PATH'])
import mscl
import time
import struct
import resource
import queue
import datetime

# connection = mscl.Connection.Serial("COM5", 115200)
connection = mscl.Connection.Serial("/dev/ttyACM0", 115200 * 8)
node = mscl.InertialNode(connection)

# Get ahead of system startup
time.sleep(15)  # sleep 15 seconds
while True:
    try:
        connection = mscl.Connection.Serial("/dev/ttyACM0", 115200 * 8)
        node = mscl.InertialNode(connection)
        success = node.ping()
        print("Success: ", success)
        node.setToIdle()
        break
    except:
        continue

miptypes = [mscl.MipTypes.CLASS_GNSS, mscl.MipTypes.CLASS_AHRS_IMU, mscl.MipTypes.CLASS_ESTFILTER]
# print("Node supports GNSS: ", node.features().supportsCategory(miptypes[0]))
# print("Node features: ", node.features())
miptypefull = [enum for enum in dir(mscl.MipTypes) if 'A' <= enum[0] <= 'Z']
miptypeclassesfull = [enum for enum in dir(mscl.MipTypes) if enum.split("_")[0] == "CLASS"]
# print(miptypeclassesfull)
activeclasses = []
for mipclasses in miptypeclassesfull:
    classes = getattr(mscl.MipTypes, mipclasses)
    print("Node supports ", mipclasses, ": ", node.features().supportsCategory(classes))
    if node.features().supportsCategory(classes):
        activeclasses.append(classes)
# print("Active classes: ", activeclasses)

miptypedict = {}
for miptype in miptypefull:
    miptypedict[getattr(mscl.MipTypes, miptype)] = miptype
# print("miptypedict: ", miptypedict)

node.resume()
packetcounter = {}
for active in activeclasses:
    packetcounter[active] = 0

IMUchs = node.getActiveChannelFields(128)
ESTchs = node.getActiveChannelFields(130)
UNIFIEDsequence = 0
UNIFIEDfilecount = 0
blocksperfile = 60 * 5
# filestomake = 12
filestomake = -1
samplingrate = 1000
timetosample = 1


def recreate_UNIFIEDheader():
    global UNIFIEDheader, IMUchs, ESTchs, timetosample, samplingrate, UNIFIEDsequence
    UNIFIEDheader = b''
    UNIFIEDheader += (len(IMUchs) + len(ESTchs) - 2).to_bytes(2)
    UNIFIEDheader += (timetosample).to_bytes(2)
    UNIFIEDheader += (samplingrate).to_bytes(2)
    UNIFIEDheader += (UNIFIEDsequence).to_bytes(2)
    for ch in IMUchs:
        channelField = ch.channelField()
        if channelField == 32979:
            continue
        UNIFIEDheader += (channelField).to_bytes(2)
    for ch in ESTchs:
        channelField = ch.channelField()
        if channelField == 33491:
            continue
        UNIFIEDheader += (channelField).to_bytes(2)


recreate_UNIFIEDheader()

starttime = time.time()

print("UNIFIEDheader: ", UNIFIEDheader)
# UNIFIEDfilepath ="/media/ncpa/4183-EE9B/UNIFIEDdata/MSCL_samples_"+str(starttime)+".txt"
# UNIFIEDfilepath = "/media/ncpa/4183-EE9B/UNIFIEDdata/MSCL_samples_" + datetime.datetime.now().strftime(
#     "%m_%d_%Y_%H_%M") + ".txt"
currdate = datetime.datetime.now()
UNIFIEDfilepath = "/media/ncpa/4183-EE9B/UNIFIEDdata/MSCL_samples/" + currdate.strftime("%Y%m%d/%H%M00") +".bin"
UNIFIEDfile = open(UNIFIEDfilepath, "wb")
UNIFIEDfile.write(UNIFIEDheader)

counter = 0
datatypes = []
# Theres a few ValuesTypes we need to be concerned about.
# For this script, they seem to be 0, 1, 3, 8, and 10
# from https://lord-microstrain.github.io/MSCL/Documentation/MSCL%20API%20Documentation/index.html#File:Types.h:ValueType
# 0 is 4-byte float, 1 is 8-byte double, 3 is 2-byte unsigned int, 8 is Vector, 10 is Timestamp
packetcount = 0


def handle_datatype(dataPoint):
    storedas = dataPoint.storedAs()
    match storedas:
        case 0:  # 4byte float
            return struct.pack('f', dataPoint.as_float())
        case 1:  # 8bytee double
            return struct.pack('d', dataPoint.as_double())
        case 3:  # 16byte unsigned int
            return struct.pack('H', dataPoint.as_uint16())
        case 10:
            timestamp = dataPoint.as_Timestamp()
            return struct.pack('L', timestamp.nanoseconds())
        case 8:  # vector with ?? dimensions
            vector = dataPoint.as_Vector()
            returnval = b''
            for i in range(vector.size()):
                returnval += struct.pack('f', vector.as_floatAt(i))
            return returnval
        case _:
            print("Unknown case! ", storedas)


IMUbody = b''
ESTbody = b''
IMUqueue = queue.Queue()
ESTqueue = queue.Queue()
timewritten = False
UNIFIEDcounter = 0
while True:
    # break
    # get all the packets that have been collected, with a timeout of 500 milliseconds
    packets = node.getDataPackets(500)
    # packetcount += len(packets)
    packetcount += 1
    delta = time.time() - starttime
    for packet in packets:
        if UNIFIEDcounter % 10000 == 0 and packet.descriptorSet() == 128:
            free_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
            print("Rate of UNIFIEDcounter: ", UNIFIEDcounter / (time.time() - starttime), free_memory)


        if packet.descriptorSet() == 128:
            IMUqueue.put(packet)
        elif packet.descriptorSet() == 130:
            ESTqueue.put(packet)

        if IMUqueue.qsize() > 0 and ESTqueue.qsize() > 0:
            IMUpacket = IMUqueue.get()
            IMUpoints = IMUpacket.data()
            UNIFIEDcounter += 1
            for dataPoint in IMUpoints:
                if UNIFIEDcounter % (samplingrate * timetosample) == 1 and dataPoint.field() == 32979:
                    UNIFIEDfile.write(handle_datatype(dataPoint))
                if dataPoint.field() != 32979:
                    UNIFIEDfile.write(handle_datatype(dataPoint))
            ESTpacket = ESTqueue.get()
            ESTpoints = ESTpacket.data()
            for dataPoint in ESTpoints:
                if dataPoint.field() != 33491:
                    UNIFIEDfile.write(handle_datatype(dataPoint))
        else:
            continue  # only advance to latter portion if youve added a packet!

        if UNIFIEDcounter == samplingrate * timetosample * blocksperfile:
            UNIFIEDfile.close()
            UNIFIEDsequence = 0
            starttime = time.time()
            UNIFIEDfilecount += 1
            UNIFIEDcounter = 0
            if UNIFIEDfilecount < filestomake or filestomake == -1:  # if -1 always continue
                # UNIFIEDfilepath = "/media/ncpa/4183-EE9B/UNIFIEDdata/MSCL_samples_"+str(starttime)+".txt"
                # UNIFIEDfilepath = "/media/ncpa/4183-EE9B/UNIFIEDdata/MSCL_samples_" + datetime.datetime.now().strftime(
                #     "%m_%d_%Y_%H_%M") + ".txt"
                currdate = datetime.datetime.now()
                UNIFIEDfilepath = "/media/ncpa/4183-EE9B/UNIFIEDdata/MSCL_samples/" + currdate.strftime(
                    "%Y%m%d/%H%M00") + ".bin"
                UNIFIEDfile = open(UNIFIEDfilepath, "wb")
                recreate_UNIFIEDheader()
                UNIFIEDfile.write(UNIFIEDheader)
                print("UNIFIEDheader: ", UNIFIEDheader)
        elif UNIFIEDcounter % (samplingrate * timetosample) == 0:
            UNIFIEDsequence += 1
            recreate_UNIFIEDheader()
            UNIFIEDfile.write(UNIFIEDheader)
    if UNIFIEDfilecount >= filestomake and filestomake != -1:  # if -1 never disconnect
        connection.disconnect()
        print("Disconnected")
        break
UNIFIEDfile.close()
