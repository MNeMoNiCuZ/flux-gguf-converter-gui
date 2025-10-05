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
    echo You can do this by running the following command in this directory:
    echo git clone https://github.com/ggerganov/llama.cpp.git
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
set DEFAULT_PYTHON_PATH=
set DEFAULT_PYTHON_NUM=

:: Display the found Python versions
echo --------------------
echo Found Python Versions
echo --------------------

for /f "tokens=1,*" %%a in ('py -0p') do (
    echo %%a | findstr /R "^[ ]*-" > nul && (
        set /a COUNT+=1
        set "version=%%a"
        set "rest=%%b"

        set "version=!version:-32=!!"
        set "version=!version:-64=!!"
        set "version=!version:-=!!"
        set "version=!version:V:=!!"
        set "PYTHON_VER_!COUNT!=!version!"

        set "path_part=!rest!"
        echo !rest! | findstr /C:"*" > nul
        if !errorlevel! equ 0 (
            for /f "tokens=1,*" %%x in ("!rest!") do (
                set "PYTHON_PATH_!COUNT!=%%y"
                set "DEFAULT_PYTHON_PATH=%%y"
                set "DEFAULT_PYTHON_NUM=!COUNT!"
            )
        ) else (
            for /f "tokens=*" %%x in ("!path_part!") do (
                set "PYTHON_PATH_!COUNT!=%%x"
            )
        )
    )
)

for /l %%i in (1, 1, %COUNT%) do (
    set "default_label="
    if "%%i" == "!DEFAULT_PYTHON_NUM!" (
        set "default_label= (default)"
    )
    echo %%i. !PYTHON_VER_%%i!!default_label! - !PYTHON_PATH_%%i!
)
echo.

:: Make sure at least one Python version was found
if %COUNT%==0 (
    echo No Python installations found via Python Launcher. Exiting.
    goto end
)

:: Prompt user to select a Python version
:select_version
set "SELECTED_NUM="
set /p "SELECTED_NUM=Enter the number of the Python version to use (Press Enter for default): "

if not defined SELECTED_NUM (
    if defined DEFAULT_PYTHON_PATH (
        set "SELECTED_PYTHON_PATH=!DEFAULT_PYTHON_PATH!"
    ) else (
        echo No default Python version found. Please select one from the list.
        goto select_version
    )
) else (
    set /a "num_val=0"
    set /a "num_val=!SELECTED_NUM!"
    if !num_val! equ 0 (
        echo Invalid selection. Please try again.
        goto select_version
    )
    if !num_val! gtr %COUNT% (
        echo Invalid selection. Please try again.
        goto select_version
    )
    if !num_val! lss 1 (
        echo Invalid selection. Please try again.
        goto select_version
    )
    set "SELECTED_PYTHON_PATH=!PYTHON_PATH_%SELECTED_NUM%!"
)

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

"%SELECTED_PYTHON_PATH%" -m venv "%VENV_PATH%"

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
    echo call "%%VENV_PATH%%\Scripts\activate"
    echo "%%VENV_PATH%%\Scripts\python.exe" -m pip install --upgrade pip
    echo echo Pip has been upgraded in the virtual environment %VENV_NAME%.
    echo echo To deactivate, manually type 'deactivate'.
) > "%LLAMA_CPP_DIR%\venv_update.bat"

:: Create build directory
if not exist "%LLAMA_CPP_DIR%\\build" (
    echo Creating build directory in %LLAMA_CPP_DIR%...
    mkdir "%LLAMA_CPP_DIR%\\build"
)

:: Copy convert.py to llama.cpp directory
echo Copying convert.py to %LLAMA_CPP_DIR%...
copy "%~dp0scripts\\convert.py" "%LLAMA_CPP_DIR%\\convert.py" >nul

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
        uv pip install -r "%LLAMA_REQS_PATH%" --prerelease=allow
    ) else (
        pip install --pre -r "%LLAMA_REQS_PATH%"
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
echo.
echo IMPORTANT: You need to manually install PyTorch.
echo Please visit https://pytorch.org/get-started/locally/ for instructions.
echo Activate your virtual environment before installing PyTorch.

echo.
echo -------------------------
echo Compilation Instructions
echo -------------------------
echo The 'build' directory has been created for you inside 'llama.cpp'.
echo To compile the project, you will need to have CMake and a C++ compiler installed.
echo If you have Visual Studio 2022 installed with the "Desktop development with C++" workload, you are ready to compile.
echo.
echo 1. Open a new terminal or command prompt.
echo 2. Navigate to the build directory:
echo    cd llama.cpp\build
echo 3. Configure the build:
echo    cmake .. -DLLAMA_CURL=OFF
echo 4. Compile the 'llama-quantize' tool:
echo    cmake --build . --config Debug -j10 --target llama-quantize
echo.
echo After compilation, you will find 'llama-quantize.exe' in the 'llama.cpp\build\bin\Debug' directory.

:: Keep the command prompt open
cmd /k

:cleanup
:: Clean up
echo Cleanup complete.
endlocal

:end
pause
