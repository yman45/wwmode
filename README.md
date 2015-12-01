WWmode
======

**WWmode is a tool for collecting data about devices in network, store it in
database and search through it.**

As of now it support db update and some search operations.

### Update

To update a db simply run it with *-update* key. It take some time, log any
intresting events and even check hosts for some errors.

### Search

To search through db records use *-search -attr value* key. Where attr is
record attribute. For example: `-search -vlans 505` to find devices with 505
VLAN.
You can search through:
    
    * VLAN database - **vlans**
    * IPv4 address - **ip**
    * Domain name - **dname** 
    * Contact - **contact**
    * Locatoin - **location**
    * Device model - **model**
    * Firmware version - **firmware**
