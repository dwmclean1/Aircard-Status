# Aircard-Status

Web interface for viewing the general status of Sierra Wireless Aircard modems

 ![example](https://github.com/dwmclean1/Aircard-Status/blob/55c8f6300a688945efbeb72c8964b316f8277beb/Screen%20Shot%202021-10-09%20at%2011.45.13%20am.png)

## Overview

I made this simple web interface to show the modems signal quality and to access some settings that are not available through the built-in interface.
The modems ip address and port number are stored in a .env file in the base directory and is required for the app to run. These can later be changed through the web interface.

This is intended to be run as a local web server on a device such as a raspberry pi. Chrome is recommeded.

Currently I have only tested this with a Netgear AC800s. The response parser should be able to handle other models that use the same message formatting but it may be slighty buggy. 

## HOWTO

### Install dependencies

`$ pip install -r requirements.txt`
