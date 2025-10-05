@echo off
REM Launch the Flux GGUF Converter GUI

REM Get the directory where the batch script is located
set "base_dir=%~dp0"

REM Activate the virtual environment if it exists
if exist "%base_dir%llama.cpp\venv\Scripts\activate.bat" (
    call "%base_dir%llama.cpp\venv\Scripts\activate.bat"

    REM Check if required modules are installed
    python -c "import gguf; import packaging" 2>nul
    if errorlevel 1 (
        echo "ERROR: Required modules (gguf, packaging) are not installed in the virtual environment."
        echo "Please run 'venv_create.bat' to set up the virtual environment properly,"
        echo "or manually install them with: pip install gguf packaging"
        pause
        exit /b 1
    )
)

REM Launch the GUI
python "%base_dir%scripts\convert_gui.py"

REM Deactivate virtual environment if it was activated
if exist "%base_dir%llama.cpp\venv\Scripts\activate.bat" (
    deactivate
)

pause 