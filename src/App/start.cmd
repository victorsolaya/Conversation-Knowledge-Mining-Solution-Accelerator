@echo off

REM Navigate to the project root (two levels up from src\App)
set ROOT_DIR=%cd%\..\..

REM Define .azure and config paths
set AZURE_FOLDER=%ROOT_DIR%\.azure
set CONFIG_FILE=%AZURE_FOLDER%\config.json

REM Exit if config.json not found
if not exist "%CONFIG_FILE%" (
    echo config.json not found at %CONFIG_FILE%
    exit /b 1
)

REM Extract the default environment name from config.json
for /f "delims=" %%i in ('powershell -command "(Get-Content '%CONFIG_FILE%' | ConvertFrom-Json).defaultEnvironment"') do set DEFAULT_ENV=%%i

REM Exit if no environment name was found
if not defined DEFAULT_ENV (
    echo Failed to extract defaultEnvironment from config.json
    exit /b 1
)

REM Define the full path to the .env file
set ENV_FILE=%AZURE_FOLDER%\%DEFAULT_ENV%\.env

REM Exit if the .env file doesn't exist
if not exist "%ENV_FILE%" (
    echo .env file not found at %ENV_FILE%
    exit /b 1
)

REM Copy the .env file to the current folder (src\App)
copy /Y "%ENV_FILE%" ".env"
if %errorlevel% neq 0 (
    echo Failed to copy .env file
    exit /b %errorlevel%
)

echo ✅ .env file copied to src\App

echo Restoring backend python packages...
call python -m pip install -r requirements.txt
if "%errorlevel%" neq "0" (
    echo Failed to restore backend python packages
    exit /B %errorlevel%
)

echo Restoring frontend npm packages...
cd frontend
call npm install
if "%errorlevel%" neq "0" (
    echo Failed to restore frontend npm packages
    exit /B %errorlevel%
)

echo Building frontend...
call npm run build
if "%errorlevel%" neq "0" (
    echo Failed to build frontend
    exit /B %errorlevel%
)

REM Set paths
set FRONTEND_BUILD=%ROOT_DIR%\frontend\build
set BACKEND_STATIC=%ROOT_DIR%\src\App\static

REM Create the static folder if it doesn't exist
if not exist "%BACKEND_STATIC%" mkdir "%BACKEND_STATIC%"

REM Copy index.html and favicon.ico
copy /Y "%FRONTEND_BUILD%\index.html" "%BACKEND_STATIC%\"
copy /Y "%FRONTEND_BUILD%\favicon.ico" "%BACKEND_STATIC%\"

REM Copy the entire 'static' subfolder
xcopy /E /Y /I "%FRONTEND_BUILD%\static" "%BACKEND_STATIC%\static"


echo Starting backend...
cd ..
start http://127.0.0.1:5000
call python -m uvicorn app:app --port 5000 --reload
if "%errorlevel%" neq "0" (
    echo Failed to start backend
    exit /B %errorlevel%
)
