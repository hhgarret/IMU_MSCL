import sys
sys.path.append('/usr/lib/python3.13/dist-packages')
import os
os.environ['LD_LIBRARY_PATH'] = '/usr/lib/python3.13/dist-packages:'+os.environ.get('LD_LIBRARY_PATH', '')
print(os.environ['LD_LIBRARY_PATH'])
import mscl
import time
import struct

#filepath = "./datasave/MSCL_samples_1745509274.6961424.txt"
#print(os.listdir("./data"))
miptypefull = [enum for enum in dir(mscl.MipTypes) if 'A' <= enum[0] <= 'Z']
miptypedict = {}
for miptype in miptypefull:
   miptypedict[getattr(mscl.MipTypes, miptype)] = miptype
DOPDATAS = [b'\x92\xd3', b'\x93\xd3', b'\x94\xd3', b'\x95\xd3', b'\x96\xd3', b'\x97\xd3', b'\x98\xd3',b'\x99\xd3', b'\x9a\xd3']
DOPDATAS2 = [b'\x93\x07', b'\x94\x07', b'\x95\x07', b'\x96\x07', b'\x97\x07', b'\x98\x07', b'\x99\x07', b'\x9A\x07', b'\x9b\x07', b'\x9c\x07', b'\x9d\x07', b'\x9e\x07', b'\x9f\x07',b'\xa0\x07']
GNSSECEFS = [b'\x91\x04', b'\x92\x04']
#directory = "./IMUdata/"
#directory = "./ESTdata/"
#directory = "./UNIFIEDdata/"
directory = "/media/ncpa/4183-EE9B/UNIFIEDdata/"

def determine_total_size(fields):
	fieldsizes = []
	for field in fields:
		#print(f"Field {field} = {miptypedict[field]}")
		# Everything are 4byte floats
		# POS, VEL, ACCEL, and VECTOR should all be 3vectors, and quaternion is 4
		# POS is recored in 8 byte increments
		# Pressure is 1 float
		match field:
			case 33344: #CH_FIELD_ESTFILTER_ECEF_POS
				fieldsizes.append(24) # 24 bytes, i.e., 3 8byte flaots
			case 33345: #CH_FIELD_ESTFILTER_ECEF_VEL
				fieldsizes.append(12)
			case 33308: #CH_FIELD_ESTFILTER_COMPENSATED_ACCEL
				fieldsizes.append(16) #16 bytes, i..e, 4 4bytes
			case 33283: #CH_FIELD_ESTFILTER_ESTIMATED_ORIENT_QUATERNION
				fieldsizes.append(12)
			case 33299: #CH_FIELD_ESTFILTER_ESTIMATED_GRAVITY_VECTOR
				fieldsizes.append(12)
			case 32774: #CH_FIELD_SENSOR_SCALED_MAG_VEC
				fieldsizes.append(12)
			case 32791: #CH_FIELD_SENSOR_SCALED_AMBIENT_PRESSURE
				fieldsizes.append(4)
			case 32772: #CH_FIELD_SENSOR_SCALED_ACCEL_VEC
				fieldsizes.append(12)
			case 32778: #CH_FIELD_SENSOR_ORIENTATION_QUATERNION
				fieldsizes.append(16)
			case 32773: #CH_FIELD_SENSOR_SCALED_GYRO_VEC
				fieldsizes.append(12)
			case 32788: #CH_FIELD_SENSOR_TEMPERATURE_STATISTICS
				fieldsizes.append(12)
			case 32775: #CH_FIELD_SENSOR_DELTA_THETA_VEC
				fieldsizes.append(12)
			case 32776: #CH_FIELD_SENSOR_DELTA_VELOCITY_VEC
				fieldsizes.append(12)
			case 32832: #CH_FIELD_SENSOR_ODOMETER_DATA
				fieldsizes.append(8)
			case 33293: #CH_FIELD_ESTFILTER_ESTIMATED_LINEAR_ACCEL
				fieldsizes.append(12)
			case 33287: #CH_FIELD_ESTFILTER_ESTIMATED_ACCEL_BIAS
				fieldsizes.append(12)
			case 33294: #CH_FIELD_ESTFILTER_ESTIMATED_ANGULAR_RATE
				fieldsizes.append(12)
			case 33286: #CH_FIELD_ESTIMATED_GYRO_BIAS
				fieldsizes.append(12)
			case 33335: #CH_FIELD_ESTFILTER_ECEF_VEL_UNCERT
				fieldsizes.append(12)
			case _:
				print("Unknown field! Case: ", field)
				exit()
		#print(f"Case {field} of size {fieldsizes[-1]}")
	#print("Fieldsizes: ", fieldsizes)
	totalsize = 0
	for fieldsize in fieldsizes:
		totalsize += fieldsize
	return totalsize

for file in os.listdir(directory):
	print("\n\n")
	numunknowns = 0
	filepath = directory+file
	filesize = os.path.getsize(filepath)
	print("File size: ", filesize)
	file = open(filepath, "rb")
	count = 0
	while filesize-file.tell() > 0:
		numfields = int.from_bytes(file.read(2))
		timetosample = int.from_bytes(file.read(2))
		samplingrate = int.from_bytes(file.read(2))
		sequence = int.from_bytes(file.read(2))
		numsamples = timetosample * samplingrate
		# Read in timestamp (12 bytes total? 8 and 4?)
		fields = []
		for i in range(numfields):
			fields.append(int.from_bytes(file.read(2)))
		headersize = 8 + 2*numfields + 10
		totalsize = determine_total_size(fields)
		blocksize = headersize+totalsize*timetosample*samplingrate
		timestamp = file.read(10)
		if sequence == 0:
			print(f"Numfields {numfields}, numsamples {numsamples}, sampling rate{samplingrate}, samplingtime {timetosample}, fields {fields}, timestamp {timestamp}, sequence {sequence}, headersize {headersize}")

		for i in range(numsamples):
			file.read(totalsize)
		if sequence % 50 == 0:
			print("Block : ",sequence,", remaining_bytes: ", (filesize-file.tell()),", total size: ", totalsize , ", blocks left: ", (filesize-file.tell())/blocksize)
	# Should read all but one 'packet', so remaining_bytes should equal total size!
	continue


#print(dir(mscl.MipDataPoint))

