@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=%~dp0.venv-hematotoxicity\Scripts\python.exe"
if not exist "%PYTHON%" (
    where py >nul 2>nul
    if errorlevel 1 (
        python -m venv ".venv-hematotoxicity" || goto failed
    ) else (
        py -3.11 -m venv ".venv-hematotoxicity" || py -3.12 -m venv ".venv-hematotoxicity" || py -3.13 -m venv ".venv-hematotoxicity" || goto failed
    )
)
"%PYTHON%" -m pip install -r "data\supplementary\hematotoxicity_v031\requirements_model.txt" || goto failed
set OPENBLAS_NUM_THREADS=1
"%PYTHON%" "data\supplementary\hematotoxicity_v031\run_pilot.py" %* || goto failed
echo.
echo Results: data\supplementary\hematotoxicity_v031\results
pause
exit /b 0
:failed
echo.
echo Failed. Install Python 3.11, 3.12 or 3.13 and check the error above.
pause
exit /b 1
