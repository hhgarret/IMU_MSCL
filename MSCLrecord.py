# This is a script designed to continuously record data from an IMU, intended for use
# on a float owned by USM
# There are two primary generators of data in the IMU, the raw IMU sensors and the computed Est Filter data
# Currently being record by the IMU are the following:
# CH_FIELD_SENSOR_SCALED_MAG_VEC, CH_FIELD_SENSOR_SCALED_AMBIENT_PRESSURE, CH_FIELD_SENSOR_SCALED_ACCEL_VEC,
# CH_FIELD_SENSOR_ORIENTATION_QUATERNION, CH_FIELD_SENSOR_SCALED_GYRO_VEC, CH_FIELD_SENSOR_TEMPERATURE_STATISTICS,
# CH_FIELD_SENSOR_DELTA_THETA_VEC, CH_FIELD_SENSOR_DELTA_VELOCITY_VEC, and CH_FIELD_SENSOR_ODOMETER_DATA
# From the Est Filter:
# CH_FIELD_ESTFILTER_ECEF_POS, CH_FIELD_ESTFILTER_ECEF_VEL, CH_FIELD_ESTFILTER_COMPENSATED_ACCEL,
# CH_FIELD_ESTFILTER_ESTIMATED_ORIENT_QUATERNION, CH_FIELD_ESTFILTER_ESTIMATED_GRAVITY_VECTOR,
# CH_FIELD_ESTFILTER_ESTIMATED_LINEAR_ACCEL, CH_FIELD_ESTFILTER_ESTIMATED_ACCEL_BIAS,
# CH_FIELD_ESTFILTER_ESTIMATED_ANGULAR_RATE, CH_FIELD_ESTFILTER_ESTIMATED_GYRO_BIAS,
# and CH_FIELD_ESTFILTER_ECEF_VEL_UNCERT

# Active channels of type:  128 ,  CLASS_AHRS_IMU
# # of active channels:  10
# Channel Field:  32979  =  CH_FIELD_SENSOR_SHARED_GPS_TIMESTAMP
# Channel Field:  32774  =  CH_FIELD_SENSOR_SCALED_MAG_VEC
# Channel Field:  32791  =  CH_FIELD_SENSOR_SCALED_AMBIENT_PRESSURE
# Channel Field:  32772  =  CH_FIELD_SENSOR_SCALED_ACCEL_VEC
# Channel Field:  32778  =  CH_FIELD_SENSOR_ORIENTATION_QUATERNION
# Channel Field:  32773  =  CH_FIELD_SENSOR_SCALED_GYRO_VEC
# Channel Field:  32788  =  CH_FIELD_SENSOR_TEMPERATURE_STATISTICS
# Channel Field:  32775  =  CH_FIELD_SENSOR_DELTA_THETA_VEC
# Channel Field:  32776  =  CH_FIELD_SENSOR_DELTA_VELOCITY_VEC
# Channel Field:  32832  =  CH_FIELD_SENSOR_ODOMETER_DATA
# Sample Rate:  1kHz
#
# Active channels of type:  130 ,  CLASS_ESTFILTER
# # of active channels:  11
# Channel Field:  33491  =  CH_FIELD_ESTFILTER_SHARED_GPS_TIMESTAMP
# Channel Field:  33344  =  CH_FIELD_ESTFILTER_ECEF_POS
# Channel Field:  33345  =  CH_FIELD_ESTFILTER_ECEF_VEL
# Channel Field:  33308  =  CH_FIELD_ESTFILTER_COMPENSATED_ACCEL
# Channel Field:  33283  =  CH_FIELD_ESTFILTER_ESTIMATED_ORIENT_QUATERNION
# Channel Field:  33299  =  CH_FIELD_ESTFILTER_ESTIMATED_GRAVITY_VECTOR
# Channel Field:  33293  =  CH_FIELD_ESTFILTER_ESTIMATED_LINEAR_ACCEL
# Channel Field:  33287  =  CH_FIELD_ESTFILTER_ESTIMATED_ACCEL_BIAS
# Channel Field:  33294  =  CH_FIELD_ESTFILTER_ESTIMATED_ANGULAR_RATE
# Channel Field:  33286  =  CH_FIELD_ESTFILTER_ESTIMATED_GYRO_BIAS
# Channel Field:  33335  =  CH_FIELD_ESTFILTER_ECEF_VEL_UNCERT
# Sample Rate:  1kHz
#
# Active channels of type:  145 ,  CLASS_GNSS1
# # of active channels:  4
# Channel Field:  37331  =  CH_FIELD_GNSS_1_SHARED_GPS_TIMESTAMP
# Channel Field:  37124  =  CH_FIELD_GNSS_1_ECEF_POSITION
# Channel Field:  37131  =  CH_FIELD_GNSS_1_FIX_INFO
# Channel Field:  37152  =  CH_FIELD_GNSS_1_SATELLITE_STATUS
# Sample Rate:  1Hz

# FOR ALL
import time
import struct
import queue
import datetime
import sys
import os

# FOR LINUX
# sys.path.append('/usr/lib/python3.13/dist-packages')
# os.environ['LD_LIBRARY_PATH'] = '/usr/lib/python3.13/dist-packages:' + os.environ.get('LD_LIBRARY_PATH', '')
# print(os.environ['LD_LIBRARY_PATH'])
# import mscl
# import resource

# FOR WINDOWS
from python_mscl import mscl

# Establish a connection to the device
connection = mscl.Connection.Serial("COM5", 115200*8)
# connection = mscl.Connection.Serial("/dev/ttyACM0", 115200 * 8)
node = mscl.InertialNode(connection)
success = node.ping()
print("Success: ", success)
node.setToIdle()

# Get ahead of system startup, add a window of safety
# time.sleep(15)  # sleep 15 seconds
# while True:
#     try:
#         # connection = mscl.Connection.Serial("/dev/ttyACM0", 115200 * 8)
#         connection = mscl.Connection.Serial("COM5", 115200*8)
#         node = mscl.InertialNode(connection)
#         success = node.ping()
#         print("Success: ", success)
#         node.setToIdle()
#         break
#     except:
#         continue


# Vestigial code in order to more easily recognize channels later, as well as some debugging information printed
# Not strictly neccessarry, but hopefully might help develop a sense of how the library can work
miptypes = [mscl.MipTypes.CLASS_GNSS, mscl.MipTypes.CLASS_AHRS_IMU, mscl.MipTypes.CLASS_ESTFILTER]
# print("Node supports GNSS: ", node.features().supportsCategory(miptypes[0]))
# print("Node features: ", node.features())
miptypefull = [enum for enum in dir(mscl.MipTypes) if 'A' <= enum[0] <= 'Z']
miptypeclassesfull = [enum for enum in dir(mscl.MipTypes) if enum.split("_")[0] == "CLASS"]
# print(miptypeclassesfull)
activeclasses = []
for mipclasses in miptypeclassesfull:
    classes = getattr(mscl.MipTypes, mipclasses)
    # print("Node supports ", mipclasses, ": ", node.features().supportsCategory(classes))
    if node.features().supportsCategory(classes):
        activeclasses.append(classes)
# print("Active classes: ", activeclasses)

miptypedict = {}
for miptype in miptypefull:
    miptypedict[getattr(mscl.MipTypes, miptype)] = miptype
# print("miptypedict: ", miptypedict)

# for miptype in miptypes:
#     try:
#         chs = node.getActiveChannelFields(miptype)
#         print("Active channels of type: ", miptype, ", ", chs)
#         for ch in chs:
#             print("Channel Field: ", ch.channelField(), " = ", miptypedict[ch.channelField()])
#             print("Sample Rate: ", ch.sampleRate().prettyStr())
#     except mscl.Error_MipCmdFailed as e:
#         print("Failed at type: ", miptype)

# for active in activeclasses:
#     # if active not in [128, 130]:
#     #     continue
#     chs = node.getActiveChannelFields(active)
#     print("Active channels of type: ", active, ", ", miptypedict[active])
#     print("# of active channels: ", len(chs))
#     for ch in chs:
#         print("Channel Field: ", ch.channelField(), " = ", miptypedict[ch.channelField()])
#         print("Sample Rate: ", ch.sampleRate().prettyStr())
#     print()


# Start the device back up
node.resume()

# Header initialization information
IMUchs = node.getActiveChannelFields(128) # 128 is the channel field id for the raw IMU data
ESTchs = node.getActiveChannelFields(130) # 130 is the channel field id for the EST filter
UNIFIEDsequence = 0
UNIFIEDfilecount = 0
blocksperfile = 60 * 5
filestomake = -1  # -1 indicates to keep going perpetually
samplingrate = 1000
timetosample = 1
# latestsvcount = 0 # svcount is in the newer versions of this code


# As the function name says, it recreates the header if any of the information in it needs to change
def recreate_UNIFIEDheader():
    global UNIFIEDheader, IMUchs, ESTchs, timetosample, samplingrate, UNIFIEDsequence # , latestsvcount # svcount is in the newer versions of this code
    UNIFIEDheader = b''
    UNIFIEDheader += (len(IMUchs) + len(ESTchs) - 2).to_bytes(2)
    UNIFIEDheader += (timetosample).to_bytes(2)
    UNIFIEDheader += (samplingrate).to_bytes(2)
    UNIFIEDheader += (UNIFIEDsequence).to_bytes(2)
    # UNIFIEDheader += (latestsvcount).to_bytes(2) #svcount is in the newer versions of this code
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

# Create and open the first file
starttime = time.time()
print("UNIFIEDheader: ", UNIFIEDheader)
# basepath = "/media/ncpa/4183-EE9B/UNIFIEDdata/MSCL_samples/" # base path for linux
basepath = "./UNIFIEDdata/MSCL_samples/" # base path for testing on windows
UNIFIEDfilepath = basepath + datetime.datetime.now().strftime("%Y%m%d/%H%M00") + ".bin"
os.mkdir(basepath+datetime.datetime.now().strftime("%Y%m%d"))  # If the directory for the current y/m/d doesnt exist, create it
UNIFIEDfile = open(UNIFIEDfilepath, "wb")
UNIFIEDfile.write(UNIFIEDheader)
packetcount = 0
counter = 0


def handle_datatype(dataPoint):
    # Takes a datapoint and converts it to the binary necessary. For current channels, its only floats and doubles
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
            # print("Unsure how to handle case 8, datapoint: ", dataPoint.as_Vector())
            vector = dataPoint.as_Vector()
            returnval = b''
            for i in range(vector.size()):
                # IMUfile.write(struct.pack('f', vector.as_floatAt(i)))
                returnval += struct.pack('f', vector.as_floatAt(i))
            return returnval
        case _:
            print("Unknown case! ", storedas)


# Create queues to hold packets so that they can be written together
IMUqueue = queue.Queue()
ESTqueue = queue.Queue()
UNIFIEDcounter = 0
while True:
    # break
    # get all the packets that have been collected, with a timeout of 500 milliseconds
    packets = node.getDataPackets(500)
    # packetcount += len(packets)
    packetcount += 1
    delta = time.time() - starttime

    for packet in packets:
        # Add the appropriate packets to their queues
        if packet.descriptorSet() == 128:  # 128 is the packet descriptor code for raw IMU data
            IMUqueue.put(packet)
        elif packet.descriptorSet() == 130:  # 130 is packet descriptor code for EST data
            ESTqueue.put(packet)
        # elif packet.descriptorSet() == 145: # svcount is in the newer versions of this code
        #     # print("GPS data:")
        #     for dataPoint in packet.data():
        #         if dataPoint.field() == 37152: # Satellite status information, extraneous
        #             continue
        #         if dataPoint.channelName() == "gnss1_gnssFixSvCount": # The only channel we care about from gnss
        #             latestsvcount = dataPoint.as_uint16()
                # print(dataPoint.field(), dataPoint.channelName(), miptypedict[dataPoint.field()], dataPoint.as_float())

        # If both queues have a packet inside of them, pop one from both and write to the file
        if IMUqueue.qsize() > 0 and ESTqueue.qsize() > 0:
            IMUpacket = IMUqueue.get()
            IMUpoints = IMUpacket.data()
            UNIFIEDcounter += 1
            for dataPoint in IMUpoints: # For each piece of information in the packet, write to the file in order
                if UNIFIEDcounter % (
                        samplingrate * timetosample) == 1 and dataPoint.field() == 32979:  # If its the first piece of data in a block, write time info
                    UNIFIEDfile.write(handle_datatype(dataPoint))
                if dataPoint.field() != 32979:  # 32979 is the field code for a timestamp in the raw data
                    UNIFIEDfile.write(handle_datatype(dataPoint))
            ESTpacket = ESTqueue.get()
            ESTpoints = ESTpacket.data()
            for dataPoint in ESTpoints: # Repeat for EST
                if dataPoint.field() != 33491:  # 33491 is the field code for a timestamp in the est data
                    UNIFIEDfile.write(handle_datatype(dataPoint))
        else:
            continue  # only advance to latter portion if youve added a packet!

        # If enough packets have been written to the file, end the file and create a new file
        if UNIFIEDcounter == samplingrate * timetosample * blocksperfile:
            UNIFIEDfile.close()
            UNIFIEDsequence = 0
            starttime = time.time()
            UNIFIEDfilecount += 1
            UNIFIEDcounter = 0
            if UNIFIEDfilecount < filestomake or filestomake == -1:  # if -1 always continue
                UNIFIEDfilepath = basepath + datetime.datetime.now().strftime("%Y%m%d/%H%M00") + ".bin"
                os.mkdir(basepath+datetime.datetime.now().strftime("%Y%m%d")) # If the directory for the current y/m/d doesnt exist, create it
                UNIFIEDfile = open(UNIFIEDfilepath, "wb")
                recreate_UNIFIEDheader()
                UNIFIEDfile.write(UNIFIEDheader)
                print("UNIFIEDheader: ", UNIFIEDheader)
        elif UNIFIEDcounter % (samplingrate * timetosample) == 0: # This is for if enough samples have been written to fill a block
            UNIFIEDsequence += 1
            recreate_UNIFIEDheader()
            UNIFIEDfile.write(UNIFIEDheader)
    if UNIFIEDfilecount >= filestomake and filestomake != -1:  # if -1 never disconnect
        connection.disconnect()
        print("Disconnected")
        break
UNIFIEDfile.close()
