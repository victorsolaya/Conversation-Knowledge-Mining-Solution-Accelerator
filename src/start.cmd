@echo off
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

echo Starting backend...
start /B python api/app.py --port=8000
if "%errorlevel%" neq "0" (
    echo Failed to start backend
    exit /B %errorlevel%
)

echo Starting frontend...
start /B cmd /c "cd App && npm start"
if "%errorlevel%" neq "0" (
    echo Failed to start frontend
    exit /B %errorlevel%
)

echo Backend running at http://127.0.0.1:8000
echo Frontend running at http://localhost:3000
