@echo off
setlocal enabledelayedexpansion

echo -----------------------------------------------------------------
echo VENV Installation Script - Helps you create a virtual environment
echo -----------------------------------------------------------------

:: Define the relative path for the llama.cpp directory
set LLAMA_CPP_DIR=llama.cpp

:: Check if the llama.cpp directory exists
if not exist "%LLAMA_CPP_DIR%" (
    echo ERROR: The `llama.cpp` directory was not found at `%LLAMA_CPP_DIR%`.
    echo Please ensure you have cloned `llama.cpp` inside the `flux-gguf-converter-gui` directory.
    goto end
)

:: Temporarily disable delayed expansion to check for "!" in the path
setlocal disabledelayedexpansion
echo You are about to create a virtual environment in: %LLAMA_CPP_DIR%
set "CURRENT_PATH=%CD%"
set "MODIFIED_PATH=%CURRENT_PATH:!=%"
if not "%CURRENT_PATH%"=="%MODIFIED_PATH%" (
    echo WARNING: The current directory contains a "!" character, which may cause issues. Proceed at your own risk.
)
endlocal
setlocal enabledelayedexpansion


:: Initialize counter
set COUNT=0

:: Directly parse the output of py -0p to get versions and their paths
for /f "tokens=1,*" %%a in ('py -0p') do (
    :: Filter lines that start with a dash, indicating a Python version, and capture the path
    echo %%a | findstr /R "^[ ]*-" > nul && (
        set /a COUNT+=1
        set "pythonVersion=%%a"
        :: a quick, dirty but understandable solution
        set "pythonVersion=!pythonVersion:-32=!!"
        set "pythonVersion=!pythonVersion:-64=!!"
        set "pythonVersion=!pythonVersion:-=!!"
        set "pythonVersion=!pythonVersion:V:=!!"
        set "PYTHON_VER_!COUNT!=!pythonVersion!"
        set "PYTHON_PATH_!COUNT!=%%b"  :: Store the path in a separate variable
    )
)

:: Make sure at least one Python version was found
if %COUNT%==0 (
    echo No Python installations found via Python Launcher. Exiting.
    goto end
)

:: ... (rest of the python version selection logic is unchanged) ...

:: Prompt for virtual environment name with default 'venv'
echo ------------------------
echo Virtual Environment Name
echo ------------------------
echo Select the name for your virtual environment to be created in the llama.cpp folder.
set VENV_NAME=venv
set /p VENV_NAME="Enter the name for your virtual environment (Press Enter for default 'venv'): "
if "!VENV_NAME!"=="" set VENV_NAME=venv

set VENV_PATH=%LLAMA_CPP_DIR%\%VENV_NAME%

:: Create the virtual environment using the selected Python version
echo.
echo Creating virtual environment at %VENV_PATH%...

py -%SELECTED_PYTHON_VER% -m venv "%VENV_PATH%"

:: Add .gitignore to the virtual environment folder
echo Creating .gitignore in the %VENV_PATH% folder...
(
    echo # Ignore all content in the virtual environment directory
    echo *
    echo # Except this file
    echo !.gitignore
) > "%VENV_PATH%\.gitignore"

:: Generate the venv_activate.bat file in the llama.cpp directory
echo Generating venv_activate.bat in %LLAMA_CPP_DIR%...
(
    echo @echo off
    echo cd %%~dp0
    echo set VENV_PATH=%VENV_NAME%
    echo.
    echo echo Activating virtual environment...
    echo call "%%VENV_PATH%%\Scripts\activate"
    echo echo Virtual environment activated.
    echo cmd /k
) > "%LLAMA_CPP_DIR%\venv_activate.bat"

:: Generate the venv_update.bat file for a one-time pip upgrade
echo Generating venv_update.bat for a one-time pip upgrade...
(
    echo @echo off
    echo cd %%~dp0
    echo echo Activating virtual environment %VENV_NAME% and upgrading pip...
    echo call "%VENV_PATH%\Scripts\activate"
    echo "%VPATH%\Scripts\python.exe" -m pip install --upgrade pip
    echo echo Pip has been upgraded in the virtual environment %VENV_NAME%.
    echo echo To deactivate, manually type 'deactivate'.
) > "%LLAMA_CPP_DIR%\venv_update.bat"


:: Activate the new environment to install packages
call "%VENV_PATH%\Scripts\activate.bat"


echo.

echo ---------------------
echo Upgrading pip install
echo ---------------------
set /p UPGRADE_NOW="Do you want to upgrade your pip version now? (Y/N) (Press Enter for default 'Y'): "
if not defined UPGRADE_NOW set UPGRADE_NOW=Y
if /I "%UPGRADE_NOW%"=="Y" (
    echo Upgrading pip...
    python -m pip install --upgrade pip
)

:: uv pip package installer
echo.

echo ------------------------
echo uv pip package installer
echo ------------------------
echo uv is a Python package that improves package installation speed
set /p INSTALL_UV="Do you want to install 'uv' package? (Y/N) (Press Enter for default 'Y'): "
if "!INSTALL_UV!"=="" set INSTALL_UV=Y
set INSTALL_UV=!INSTALL_UV:~0,1!

if /I "!INSTALL_UV!"=="Y" (
    echo Installing 'uv' package...
    pip install uv
    set UV_INSTALLED=1
) else (
    set UV_INSTALLED=0
)

:: Check if requirements.txt exists and handle installation
echo.

echo ------------------------------------------------------
echo Installing dependencies from requirements.txt files...

set GUI_REQS_PATH=requirements.txt
set LLAMA_REQS_PATH=llama.cpp\requirements.txt

if exist "%GUI_REQS_PATH%" (
    echo GUI requirements.txt found.
    if "!UV_INSTALLED!"=="1" (
        uv pip install -r "%GUI_REQS_PATH%"
    ) else (
        pip install -r "%GUI_REQS_PATH%"
    )
) else (
    echo GUI requirements.txt not found. Skipping.
)

if exist "%LLAMA_REQS_PATH%" (
    echo llama.cpp requirements.txt found.
    if "!UV_INSTALLED!"=="1" (
        uv pip install -r "%LLAMA_REQS_PATH%"
    ) else (
        pip install -r "%LLAMA_REQS_PATH%"
    )
) else (
    echo llama.cpp requirements.txt not found. Skipping.
)


:: List installed packages
echo.

echo Listing installed packages...
pip list

echo.

echo Setup complete. Your virtual environment is ready in the %LLAMA_CPP_DIR% folder.
echo To activate it in the future, run venv_activate.bat from the %LLAMA_CPP_DIR% folder.
echo To deactivate the virtual environment, type 'deactivate'.

:: Keep the command prompt open
cmd /k

:cleanup
:: Clean up
echo Cleanup complete.
endlocal

:end
pause
