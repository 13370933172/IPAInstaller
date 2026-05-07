@echo off
chcp 65001 >nul
echo ========================================
echo   IPA Installer - 构建独立可执行文件
echo ========================================
echo.

echo [1/3] 安装构建依赖...
pip install pyinstaller -q

echo [2/3] 清理旧构建...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo [3/3] 开始打包...
pyinstaller --clean --noconfirm IPAInstaller.spec

echo.
if exist "dist\IPAInstaller.exe" (
    echo ========================================
    echo   构建成功！
    echo   输出文件: dist\IPAInstaller.exe
    echo ========================================
) else (
    echo 构建失败，请检查上方错误信息。
)

pause
