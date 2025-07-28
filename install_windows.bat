@echo off
echo Installing VoiceAccess dependencies for Windows...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
echo.

REM Upgrade pip first
python -m pip install --upgrade pip

REM Install minimal requirements first
echo Installing minimal requirements...
python -m pip install -r requirements-minimal.txt

REM Try to install additional packages one by one
echo.
echo Installing additional packages...

python -m pip install scipy==1.11.4
python -m pip install librosa==0.10.1
python -m pip install soundfile==0.12.1
python -m pip install streamlit-webrtc==0.47.1
python -m pip install websockets==12.0
python -m pip install aiohttp==3.9.1
python -m pip install pydantic==2.5.2
python -m pip install altair==5.2.0
python -m pip install loguru==0.7.2
python -m pip install validators==0.22.0
python -m pip install threading-timer==0.1.0

echo.
echo Installation complete!
echo.
echo To run the application:
echo 1. Add your AssemblyAI API key to the .env file
echo 2. Run: streamlit run app.py
echo.
pause