Use this to discover Siemens Sentron devices in your local ethernet.

This uses UDP broadcasts, as captured from Siemens "Sentron powerconfig v3.2"
Not all fields are decoded, and this has only been tested against a Sentron
PAC4200.  Once you have found the device like this, you can use regular
Modbus/TCP requests to probe for further information.

Usage:

    ./discover.py <local ip>

Where the <local ip> is given to properly select the correct outbound interface
send the UDP broadcast.

Example output:

    $ ./discover.py 
    Found a device: product=7KM4212-0BA00-3AA0 (plant=karls plant) {ip=192.168.255.100, netmask=255.255.255.0, gw=192.168.255.124} {SW ver: ?, Boot ver: ?}
    $


