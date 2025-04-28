@echo off
echo 🔧 Starting the application setup...

REM Set root and config paths
set ROOT_DIR=%cd%\..
set AZURE_FOLDER=%ROOT_DIR%\.azure
set CONFIG_FILE=%AZURE_FOLDER%\config.json

REM Validate config.json
if not exist "%CONFIG_FILE%" (
    echo ❌ config.json not found at %CONFIG_FILE%
    exit /b 1
)

REM Extract default environment name
for /f "delims=" %%i in ('powershell -command "(Get-Content '%CONFIG_FILE%' | ConvertFrom-Json).defaultEnvironment"') do set DEFAULT_ENV=%%i

if not defined DEFAULT_ENV (
    echo ❌ Failed to extract defaultEnvironment from config.json
    exit /b 1
)

REM Set path to source .env file
set ENV_FILE=%AZURE_FOLDER%\%DEFAULT_ENV%\.env

if not exist "%ENV_FILE%" (
    echo ❌ .env file not found at %ENV_FILE%
    exit /b 1
)

REM ✅ 1. Copy full .env to src/api
set API_ENV_FILE=%ROOT_DIR%\src\api\.env
copy /Y "%ENV_FILE%" "%API_ENV_FILE%"
if errorlevel 1 (
    echo ❌ Failed to copy .env to src/api
    exit /b 1
)
echo ✅ Copied .env to src/api

REM ✅ 2. Extract REACT_APP_API_BASE_URL to src/App/.env
set APP_ENV_FILE=%ROOT_DIR%\src\App\.env
(for /f "tokens=1,* delims==" %%A in ('type "%ENV_FILE%" ^| findstr /B "REACT_APP_API_BASE_URL="') do (
    echo %%A=%%B
)) > "%APP_ENV_FILE%"

if exist "%APP_ENV_FILE%" (
    echo ✅ Created src/App/.env with REACT_APP_API_BASE_URL
) else (
    echo ❌ Failed to create src/App/.env
    exit /b 1
)


echo Restoring backend Python packages...
cd api
call python -m pip install -r requirements.txt
if "%errorlevel%" neq "0" (
    echo Failed to restore backend Python packages
    exit /B %errorlevel%
)
cd ..

echo Restoring frontend npm packages...
cd App
call npm install --force
if "%errorlevel%" neq "0" (
    echo Failed to restore frontend npm packages
    exit /B %errorlevel%
)
cd ..

echo Starting backend in a new terminal...
start cmd /k "cd api && python app.py --port=8000"
if "%errorlevel%" neq "0" (
    echo Failed to start backend
    exit /B %errorlevel%
)

echo Starting frontend in a new terminal...
start cmd /k "cd App && npm start"
if "%errorlevel%" neq "0" (
    echo Failed to start frontend
    exit /B %errorlevel%
)

echo Backend running at http://127.0.0.1:8000
echo Frontend running at http://localhost:3000