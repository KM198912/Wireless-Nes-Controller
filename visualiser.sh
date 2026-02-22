#!/bin/bash
# Visualiser script for the NES Wireless Controller project
#check for python3, we dont check the version here, because the binary is already called python3,
#if the user renamed python2 to python3, it will be their fault, we did everything right, they broke their system, not us
#not my monkey not my circus!
if ! command -v python3 &> /dev/null
then
    echo "python3 could not be found, please install it to run the visualiser"
    exit
else
    PYTHON_CMD=python3
fi

#mac might have a different python name, check for python and py too, and check the version to make sure it's 3.x
if ! command -v python &> /dev/null
then
    if ! command -v py &> /dev/null
    then
        echo "python could not be found, please install it to run the visualiser"
        exit
    else
        PYTHON_CMD=py
    fi
else
    PYTHON_CMD=python
fi
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
if [[ $PYTHON_VERSION != 3* ]]
then
    echo "python version 3.x is required, but found version $PYTHON_VERSION"
    exit
fi

#check for pyserial
if ! $PYTHON_CMD -c "import serial" &> /dev/null
then
    echo "pyserial is not installed, please install it with 'pip install pyserial'"
    exit
fi
#check for pillow
if ! $PYTHON_CMD -c "import PIL" &> /dev/null
then
    echo "Pillow is not installed, please install it with 'pip install Pillow'"
    exit
fi
#linux might need a extra check for tkinter
if ! $PYTHON_CMD -c "import tkinter" &> /dev/null
then
    echo "tkinter is not installed, please install it with 'sudo apt-get install python3-tk'"
    exit
fi
#run the visualiser in the background
echo "Starting visualiser in the background..."
$PYTHON_CMD visualiser.py &