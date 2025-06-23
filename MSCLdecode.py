# A script designed to read through and verify the data recorded from MSCLrecord.py
# It is able to record data into a csv

import sys
sys.path.append('/usr/lib/python3.13/dist-packages')
import os
os.environ['LD_LIBRARY_PATH'] = '/usr/lib/python3.13/dist-packages:' + os.environ.get('LD_LIBRARY_PATH', '')
print(os.environ['LD_LIBRARY_PATH'])
# import mscl
from python_mscl import mscl
import time
import struct
from collections import namedtuple
import plotly.graph_objs as go
import numpy as np
import plotly.io as pio
pio.renderers.default = "browser"
import matplotlib.pyplot as plt


# filepath = "./datasave/MSCL_samples_1745509274.6961424.txt"
# print(os.listdir("./data"))
miptypefull = [enum for enum in dir(mscl.MipTypes) if 'A' <= enum[0] <= 'Z']
miptypedict = {}
for miptype in miptypefull:
    miptypedict[getattr(mscl.MipTypes, miptype)] = miptype
DOPDATAS = [b'\x92\xd3', b'\x93\xd3', b'\x94\xd3', b'\x95\xd3', b'\x96\xd3', b'\x97\xd3', b'\x98\xd3', b'\x99\xd3',
            b'\x9a\xd3']
DOPDATAS2 = [b'\x93\x07', b'\x94\x07', b'\x95\x07', b'\x96\x07', b'\x97\x07', b'\x98\x07', b'\x99\x07', b'\x9A\x07',
             b'\x9b\x07', b'\x9c\x07', b'\x9d\x07', b'\x9e\x07', b'\x9f\x07', b'\xa0\x07']
GNSSECEFS = [b'\x91\x04', b'\x92\x04']
# directory = "./UNIFIEDdata/"
directory = "D:/UNIFIEDdata/MSCL_samples/20250522/"
directory2 = "D:/UNIFIEDdata/MSCL_samples/20250523/"

fieldsizes = []
fieldidentities = ()
pattern = []


def determine_total_size(fields):
    global fieldsizes, fieldidentities, pattern
    fieldsizes = []
    fieldidentities = ()
    pattern = []
    for field in fields:
        # print(f"Field {field} = {miptypedict[field]}")
        # Everything are 4byte floats
        # POS, VEL, ACCEL, and VECTOR should all be 3vectors, and quaternion is 4
        # POS is recored in 8 byte increments
        # Pressure is 1 float
        # in struct, l is long and 4byte int, f is float and 4byte float, d is double and 8byte float
        fieldidentities = fieldidentities + (miptypedict[field],)
        match field:
            case 33344:  # CH_FIELD_ESTFILTER_ECEF_POS
                fieldsizes.append(24)  # 24 bytes, i.e., 3 8byte floats
                pattern.append("3d")
            case 33345:  # CH_FIELD_ESTFILTER_ECEF_VEL
                fieldsizes.append(12)
                pattern.append("3f")
            case 33308:  # CH_FIELD_ESTFILTER_COMPENSATED_ACCEL
                fieldsizes.append(16)  # 16 bytes, i..e, 4 4bytes
                pattern.append("4f")
            case 33283:  # CH_FIELD_ESTFILTER_ESTIMATED_ORIENT_QUATERNION
                fieldsizes.append(12)
                pattern.append("3f")
            case 33299:  # CH_FIELD_ESTFILTER_ESTIMATED_GRAVITY_VECTOR
                fieldsizes.append(12)
                pattern.append("3f")
            case 32774:  # CH_FIELD_SENSOR_SCALED_MAG_VEC
                fieldsizes.append(12)
                pattern.append("3f")
            case 32791:  # CH_FIELD_SENSOR_SCALED_AMBIENT_PRESSURE
                fieldsizes.append(4)
                pattern.append("f")
            case 32772:  # CH_FIELD_SENSOR_SCALED_ACCEL_VEC
                fieldsizes.append(12)
                pattern.append("3f")
            case 32778:  # CH_FIELD_SENSOR_ORIENTATION_QUATERNION
                fieldsizes.append(16)
                pattern.append("4f")
            case 32773:  # CH_FIELD_SENSOR_SCALED_GYRO_VEC
                fieldsizes.append(12)
                pattern.append("3f")
            case 32788:  # CH_FIELD_SENSOR_TEMPERATURE_STATISTICS
                fieldsizes.append(12)
                pattern.append("3f")
            case 32775:  # CH_FIELD_SENSOR_DELTA_THETA_VEC
                fieldsizes.append(12)
                pattern.append("3f")
            case 32776:  # CH_FIELD_SENSOR_DELTA_VELOCITY_VEC
                fieldsizes.append(12)
                pattern.append("3f")
            case 32832:  # CH_FIELD_SENSOR_ODOMETER_DATA
                fieldsizes.append(8)
                pattern.append("2f")
            case 33293:  # CH_FIELD_ESTFILTER_ESTIMATED_LINEAR_ACCEL
                fieldsizes.append(12)
                pattern.append("3f")
            case 33287:  # CH_FIELD_ESTFILTER_ESTIMATED_ACCEL_BIAS
                fieldsizes.append(12)
                pattern.append("3f")
            case 33294:  # CH_FIELD_ESTFILTER_ESTIMATED_ANGULAR_RATE
                fieldsizes.append(12)
                pattern.append("3f")
            case 33286:  # CH_FIELD_ESTIMATED_GYRO_BIAS
                fieldsizes.append(12)
                pattern.append("3f")
            case 33335:  # CH_FIELD_ESTFILTER_ECEF_VEL_UNCERT
                fieldsizes.append(12)
                pattern.append("3f")
            case _:
                print("Unknown field! Case: ", field)
                exit()
    # print(f"Case {field} of size {fieldsizes[-1]}")
    # print("Fieldsizes: ", fieldsizes)
    totalsize = 0
    for fieldsize in fieldsizes:
        totalsize += fieldsize
    return totalsize


def data_unpack(dataline):
    output = []
    position = 0
    for j, size in enumerate(fieldsizes):
        # print(pattern[j], size, position, dataline[position:position+size])
        output.append((fieldidentities[j], struct.unpack(pattern[j], dataline[position:position+size])))
        position += size
    return output


decimationfactor = 1000 # Get 1 out of each {decimationfactor} samples and add to csv!

pos = []
datafile = open("datafile.csv", "w")
headersize, totalsize, blocksize = 0, 0, 0

ls = os.listdir(directory)
ls2 = os.listdir(directory2)
files = []
for i, file in enumerate(ls):
    # 165600
    # if "170000" <= file[:-4] <= "180000":
        # print(file)
    files.append(directory+file)
for i, file in enumerate(ls2):
    files.append(directory2+file)
# ls += ls2
# exit()
xsave = 0

for filecount, filepath in enumerate(files):
    # print("\n\n")
    numunknowns = 0
    # filepath = directory + file
    filesize = os.path.getsize(filepath)
    # print("File size: ", filesize)
    print("File: ", filepath)
    file = open(filepath, "rb")
    count = 0
    while filesize - file.tell() > 0:
        # header is 2byte (num channels), 2byte (number of seconds in each block), 2byte (sampling rate), 2 byte(position in block), 2byte sv count
        # then 2 bytes each for each channel, then 10byte timestamp
        if count == 0:
            numfields = int.from_bytes(file.read(2))
            timetosample = int.from_bytes(file.read(2))
            samplingrate = int.from_bytes(file.read(2))
            sequence = int.from_bytes(file.read(2))
            svcount = int.from_bytes(file.read(2))
            numsamples = timetosample * samplingrate
            # Read in timestamp (12 bytes total? 8 and 4?)
            fields = []
            for i in range(numfields):
                fields.append(int.from_bytes(file.read(2)))
            headersize = 10 + 2 * numfields + 10
            totalsize = determine_total_size(fields)
            blocksize = headersize + totalsize * timetosample * samplingrate
            if sequence == 0 and filecount == 0:
                print(fieldidentities, pattern)
            #     exit()
            if filecount == 0:
                for j in range(len(fieldidentities)):
                    tmppat = pattern[j]
                    fieldidentity = fieldidentities[j]
                    datafile.write("tow, weeknumber")
                    if tmppat[0] == "3":
                        datafile.write(f",{fieldidentity}_x,{fieldidentity}_y,{fieldidentity}_z")
                    elif tmppat[0] == "4":
                        datafile.write(f",{fieldidentity}_x,{fieldidentity}_y,{fieldidentity}_z,{fieldidentity}_w")
                    elif tmppat[0] == "f":
                        datafile.write(f",{fieldidentity}")
                    elif tmppat[0] == "2":
                        datafile.write(f",{fieldidentity}_x,{fieldidentity}_y")
                datafile.write("\n")
                # datafile.write(f"{fieldidentities[0]}")
                # for fieldidentity in fieldidentities[1:]:
                #     datafile.write(f",{fieldidentity}")
                # datafile.write("\n")
                # datafile.close()
                # exit()
            timestamp = file.read(10)
            # Timestamp is composed of tow (8bytes) and weeknumber (2bytes)
            tow, weeknumber = struct.unpack("dh", timestamp)
        else:
            header = file.read(headersize)
            timestamp = header[-10:]
            tow, weeknumber = struct.unpack("dh", timestamp)
        # if sequence == 0:
        #     print(
        #         f"Numfields {numfields}, numsamples {numsamples}, sampling rate{samplingrate}, samplingtime {timetosample}, totalsize {totalsize}, timestamp {timestamp}, sequence {sequence}, headersize {headersize}")

        # Data = namedtuple("Data", fieldidentities)
        for i in range(numsamples):
            data = file.read(totalsize)
            # if i == 0:
            # print(copy[9][1])
            if (count*numsamples + i) % decimationfactor == 0: # Gets 1 out of each {decimationfactor} sample in the file
                copy = data_unpack(data)
                datafile.write(f"{tow},{weeknumber}")
                datafile.write(f",{copy[0][1][0]}")
                # print(len(copy[0][1]))
                for datapointsub in copy[0][1][1:]:
                    datafile.write(f",{datapointsub}")
                for datapoint in copy[1:]:
                    # print(len(datapoint[1]))
                    for datapointsub in datapoint[1]:
                        datafile.write(f",{datapointsub}")
                datafile.write("\n")
         # if count % 50 == 0:
        #     print("Block : ", sequence, ", remaining_bytes: ", (filesize - file.tell()), ", total size: ", totalsize,
        #           ", blocks left: ", (filesize - file.tell()) / blocksize)
    # Should read all but one 'packet', so remaining_bytes should equal total size!
        count += 1
    continue

datafile.close()

