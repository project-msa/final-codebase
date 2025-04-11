#!/bin/bash

# Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt || {
    echo "Python dependency installation failed"
    exit 1
}

# Frontend dependencies
echo "Installing frontend dependencies..."
cd client && npm install || {
    echo "Frontend dependency installation failed"
    exit 1
}
cd ..

# Backend dependencies
echo "Installing backend dependencies..."
cd server && npm install || {
    echo "Backend dependency installation failed"
    exit 1
}
cd ..

echo "All dependencies installed successfully!"