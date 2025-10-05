@echo off
REM Launch the Flux GGUF Converter GUI

REM Get the directory where the batch script is located
set "base_dir=%~dp0"

REM Activate the virtual environment if it exists
if exist "%base_dir%llama.cpp\venv\Scripts\activate.bat" (
    call "%base_dir%llama.cpp\venv\Scripts\activate.bat"
)

REM Launch the GUI
python "%base_dir%scripts\convert_gui.py"

REM Deactivate virtual environment if it was activated
if exist "%base_dir%llama.cpp\venv\Scripts\activate.bat" (
    deactivate
)

pause 