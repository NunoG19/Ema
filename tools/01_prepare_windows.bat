rmdir /s /q .win32\dist
rmdir /s /q .win32\build
cd ..
c:\python27\python.exe -m PyInstaller --name ema --icon data\images\icon48.png ema.py
move build tools\.win32
move dist tools\.win32
pause
