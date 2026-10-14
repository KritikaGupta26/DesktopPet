@echo off
setlocal
cd /d "%~dp0"
py -3.12 -c "import sys; print('Python', sys.version.split()[0])"
if errorlevel 1 (
    echo Install Python 3.12 with the Windows Python launcher, then run this file again.
    pause
    exit /b 1
)
py -3.12 -c "from PIL import Image, ImageTk; import tkinter"
if errorlevel 1 (
    py -3.12 -m pip install Pillow==11.3.0
    if errorlevel 1 (
        echo Pillow could not be installed. Check the displayed error.
        pause
        exit /b 1
    )
)
powershell.exe -NoProfile -Command "Get-Process WaterPanda -ErrorAction SilentlyContinue | Stop-Process"
echo Close any older Python-source panda copy before launching v37.
start "" pyw -3.12 "%~dp0Start_Water_Puppy.pyw"
endlocal
