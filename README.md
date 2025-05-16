# IMU_MSCL
A set of scripts for reading (and saving) data coming in from a 3DM-GQ7-GNSS/INS module by Lord/Microstrain, as well as parsing and checking health of a service.

In order to prepare a new up board to run the software:

Install python3.13 on dead snakes:
Sudo apt install software-properties-common
Sudo add-apt-repository papa:deadsnakes/ppa 
Sudo apt install python3.13

Get amd64_python3.13….deb package from lord microstrain
Sudo dpkg -i <file>.deb
Sudo apt install -f

Should now be in /use/lib/python3.13/dist-packages 

Get dependency:
Sudo apt-get install libpython3.13-dev

Modify ttyACM0 (or whatever serial port) permissions:
Sudo chmod 666 ttyACM0
