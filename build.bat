@echo off
echo ========================================
echo   IPA Installer - Build
echo ========================================
echo.

echo [1/3] Installing build dependencies...
pip install pyinstaller -q

echo [2/3] Cleaning old build...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo [3/3] Building...
pyinstaller --clean --noconfirm IPAInstaller.spec

echo.
if exist "dist\IPAInstaller.exe" (
    echo ========================================
    echo   Build Success!
    echo   Output: dist\IPAInstaller.exe
    echo ========================================
) else (
    echo Build failed, please check the error messages above.
)

pause