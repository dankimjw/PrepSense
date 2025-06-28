@echo off
REM PrepSense Setup Script for Windows
REM This script automates the setup process for the PrepSense application

setlocal enabledelayedexpansion

REM Colors for output (Windows 10+)
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "RESET=[0m"
set "BOLD=[1m"

REM Print header function
echo.
echo %BLUE%%BOLD%============================================================%RESET%
echo %BLUE%%BOLD%                 PrepSense Automated Setup%RESET%
echo %BLUE%%BOLD%============================================================%RESET%
echo.

REM Check prerequisites
echo %BLUE%%BOLD%Checking Prerequisites%RESET%
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%Python is not installed%RESET%
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo %GREEN%Python installed: !PYTHON_VERSION!%RESET%
)

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%Node.js is not installed%RESET%
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
) else (
    for /f %%i in ('node --version') do set NODE_VERSION=%%i
    echo %GREEN%Node.js installed: !NODE_VERSION!%RESET%
)

REM Check npm
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%npm is not installed%RESET%
    pause
    exit /b 1
) else (
    for /f %%i in ('npm --version') do set NPM_VERSION=%%i
    echo %GREEN%npm installed: !NPM_VERSION!%RESET%
)

REM Check Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%Git is not installed%RESET%
    echo Please install Git from https://git-scm.com/
    pause
    exit /b 1
) else (
    echo %GREEN%Git is installed%RESET%
)

REM Create directories
echo.
echo %BLUE%%BOLD%Creating Required Directories%RESET%
echo.
if not exist "config" mkdir config
if not exist "logs" mkdir logs
if not exist "data" mkdir data
echo %GREEN%Created config, logs, and data directories%RESET%

REM Setup Python environment
echo.
echo %BLUE%%BOLD%Setting Up Python Environment%RESET%
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo %GREEN%Virtual environment created%RESET%
) else (
    echo %GREEN%Virtual environment already exists%RESET%
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo %RED%Failed to install Python dependencies%RESET%
    pause
    exit /b 1
)
echo %GREEN%Python dependencies installed%RESET%

REM Setup iOS app
echo.
echo %BLUE%%BOLD%Setting Up iOS App%RESET%
echo.

REM Change to ios-app directory
cd ios-app

REM Install npm dependencies
echo Installing npm dependencies...
npm install
if %errorlevel% neq 0 (
    echo %RED%Failed to install npm dependencies%RESET%
    cd ..
    pause
    exit /b 1
)
echo %GREEN%npm dependencies installed%RESET%

REM Check for Expo CLI
where expo >nul 2>&1
if %errorlevel% neq 0 (
    echo %YELLOW%Expo CLI not found%RESET%
    echo You can use 'npx expo' to run Expo commands
) else (
    echo %GREEN%Expo CLI is installed%RESET%
)

REM Return to root directory
cd ..

REM Setup environment file
echo.
echo %BLUE%%BOLD%Setting Up Environment Variables%RESET%
echo.

if exist ".env.template" (
    if exist ".env" (
        echo %YELLOW%.env file already exists%RESET%
        set /p OVERWRITE="Do you want to overwrite it? (y/N): "
        if /i "!OVERWRITE!" neq "y" (
            echo %GREEN%Keeping existing .env file%RESET%
        ) else (
            copy .env.template .env >nul
            echo %GREEN%.env file created from template%RESET%
        )
    ) else (
        copy .env.template .env >nul
        echo %GREEN%.env file created from template%RESET%
    )
    
    echo.
    echo %YELLOW%Please edit the .env file and add your API keys:%RESET%
    echo   1. Open .env in your text editor
    echo   2. Add your OpenAI API key
    echo   3. Add your Google Cloud credentials path
    echo   4. Save the file
) else (
    echo %RED%.env.template not found%RESET%
)

REM Print completion message
echo.
echo %BLUE%%BOLD%============================================================%RESET%
echo %BLUE%%BOLD%                  Setup Complete! 🎉%RESET%
echo %BLUE%%BOLD%============================================================%RESET%
echo.

echo %BOLD%Next Steps:%RESET%
echo.
echo 1. Configure your environment variables:
echo    %BLUE%Edit .env file with your API keys%RESET%
echo.
echo 2. Add Google Cloud credentials:
echo    %BLUE%Place your service account JSON file in the config\ directory%RESET%
echo    %BLUE%Update GOOGLE_APPLICATION_CREDENTIALS path in .env%RESET%
echo.
echo 3. Start the application:
echo    %GREEN%Backend:%RESET% python run_app.py
echo    %GREEN%iOS App:%RESET% python run_ios.py
echo.
echo 4. Access the services:
echo    %BLUE%API Documentation:%RESET% http://localhost:8001/docs
echo    %BLUE%iOS App:%RESET% Scan QR code with Expo Go
echo.
echo %BOLD%For more help, see the documentation in docs\%RESET%
echo.
pause