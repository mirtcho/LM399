#steps to install on Ubuntu x64
#
#from github clone this https://github.com/awelkie/pyhidapi
#git clone https://github.com/awelkie/pyhidapi.git
#start the script from pyhidapi dir
#sudo ./setup.py install
#the follofing demo script runc on python3
#
import hidapi

dev=hidapi.hid_open(vendor_id=0x0820, product_id=0x0001)
cmd = bytearray([0,0,0x86,0x66])
hidapi.hid_write(dev,cmd_bytea_ar)
rd=hidapi.hid_read(dev,27)

