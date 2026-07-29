@echo off
echo ==========================================================
echo FIXING WINDOWS NUL DRIVER PERMISSIONS
echo ==========================================================
echo.
echo NOTE: You MUST run this script as an Administrator!
echo If you just double-clicked it normally, it might fail.
echo Please right-click this file and select "Run as administrator".
echo.
pause

echo Enabling the Null service...
sc config null start= system
sc start null

echo.
echo Done! Please restart your IDE/Editor now.
pause
