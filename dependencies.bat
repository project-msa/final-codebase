@echo off

:: Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Python dependency installation failed
    exit /b 1
)

:: Frontend dependencies
echo Installing frontend dependencies...
cd client
npm install
if %errorlevel% neq 0 (
    echo Frontend dependency installation failed
    exit /b 1
)
cd ..

:: Backend dependencies
echo Installing backend dependencies...
cd server
npm install
if %errorlevel% neq 0 (
    echo Backend dependency installation failed
    exit /b 1
)
cd ..

echo All dependencies installed successfully!
pause