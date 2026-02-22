@ECHO OFF
REM Visualiser for ESP32 CPU emulator
REM Reads button states from serial and displays them graphically
REM Requires Python 3 and pyserial, install with: pip install pyserial
REM check for the required Python version
python --version 2>NUL | find "Python 3" >NUL
IF ERRORLEVEL 1 (
    ECHO Python 3 is required to run this visualiser. Please install it from https://www.python.org/downloads/
    PAUSE
    EXIT /B 1
)

REM check for python3 or py command
python3 --version 2>NUL | find "Python 3" >NUL
IF ERRORLEVEL 1 (
    py --version 2>NUL | find "Python 3" >NUL
    IF ERRORLEVEL 1 (
        ECHO Python 3 is required to run this visualiser. Please install it from https://www.python.org/downloads/
        PAUSE
        EXIT /B 1
    ) ELSE (
        SET PYTHON=py
    )
) ELSE (
    SET PYTHON=python3
)

REM check for pyserial
%PYTHON% -c "import serial" 2>NUL
IF ERRORLEVEL 1 (
    ECHO pyserial is required to run this visualiser. Please install it with: pip install pyserial
    PAUSE
    EXIT /B 1
)
REM check for pillow
%PYTHON% -c "from PIL import Image" 2>NUL
IF ERRORLEVEL 1 (
    ECHO Pillow is required to run this visualiser. Please install it with: pip install Pillow
    PAUSE
    EXIT /B 1
)
REM run the visualiser script in the background
ECHO Starting visualiser in the background using %PYTHON%...
start /B %PYTHON% visualiser.py