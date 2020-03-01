cd %~dp0
@echo off
cls
:start
C:\Users\s.scannella\AppData\Local\Continuum\Anaconda2\python FarosLauncherGUI.py

echo.
echo -----------------------------------------------
echo.
echo Do you want to reconnect to the Faros ECG device?
echo.
set choice=
set /p choice="Press 'y'/<return> for Yes, 'n' for no: "
if not '%choice%'=='' set choice=%choice:~0,1%
if '%choice%'=='y' goto start
if '%choice%'=='' goto start

cmd