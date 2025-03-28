#!/bin/bash

set -e 

# Restoring backend Python packages
echo "Restoring backend Python packages..."
cd api
python -m pip install -r requirements.txt || { echo "Failed to restore backend Python packages"; exit 1; }
cd ..

# Restoring frontend npm packages
echo "Restoring frontend npm packages..."
cd App
npm install --force || { echo "Failed to restore frontend npm packages"; exit 1; }
cd ..

# Starting backend in the background
echo "Starting backend..."
(cd api && python app.py --port=8000 &) || { echo "Failed to start backend"; exit 1; }

# Starting frontend in the background
echo "Starting frontend..."
(cd App && npm start &) || { echo "Failed to start frontend"; exit 1; }

# Display running services
echo "Backend running at http://127.0.0.1:8000"
echo "Frontend running at http://localhost:3000"