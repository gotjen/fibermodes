@ECHO OFF
REM Start the mode solver from a source checkout.
REM Install the dependencies first: pip install -e .[gui]
SETLOCAL
SET PYTHONPATH=%~dp0;%PYTHONPATH%
pythonw -m fibermodesgui.modesolverapp
ENDLOCAL
