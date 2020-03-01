cd %~dp0
@echo off
cls
:start
python Launcher.py

echo.
echo -----------------------------------------------
echo.
echo Python script finished. Do you want to restart?
echo.
set choice=
set /p choice="Press 'y'/<return> for Yes, 'n' for No: "
if not '%choice%'=='' set choice=%choice:~0,1%
if '%choice%'=='y' goto start
if '%choice%'=='' goto start

cmd