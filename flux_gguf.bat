@echo off
REM Batch script to convert safetensor to F16 gguf and quantize it.

REM Enable delayed variable expansion
setlocal enabledelayedexpansion

REM Get the directory where the batch script is located
set "base_dir=%~dp0"

REM Remove trailing backslash if any
if "%base_dir:~-1%"=="\" set "base_dir=%base_dir:~0,-1%"

REM Set convert script path including convert.py
set "convert_script_dir=%base_dir%\llama.cpp"
set "convert_script_path=%convert_script_dir%\convert.py"

REM Set quantizer executable path
set "quantizer_exe=%convert_script_dir%\build\bin\Debug\llama-quantize.exe"

REM Debug: Print paths
echo Base directory: "%base_dir%"
echo Convert script path: "%convert_script_path%"
echo Quantizer executable: "%quantizer_exe%"

REM Check if quantizer executable exists
if not exist "%quantizer_exe%" (
    echo Error: Quantizer executable not found at "%quantizer_exe%".
    echo Listing contents of "%convert_script_dir%\build\bin\Debug\"
    dir "%convert_script_dir%\build\bin\Debug\"
    pause
    exit /b 1
)

REM Activate the virtual environment
if exist "%convert_script_dir%\venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "%convert_script_dir%\venv\Scripts\activate.bat"
) else (
    echo Error: Virtual environment activation script not found at "%convert_script_dir%\venv\Scripts\activate.bat".
    pause
    exit /b 1
)

REM Prompt user for quantization type
echo Choose quantization type (default is Q4_K_S):
echo Q4_0
echo Q4_1
echo Q5_0
echo Q5_1
echo IQ2_XXS
echo IQ2_XS
echo IQ2_S
echo IQ2_M
echo IQ1_S
echo IQ1_M
echo Q2_K
echo Q2_K_S
echo IQ3_XXS
echo IQ3_S
echo IQ3_M
echo Q3_K_S
echo Q3_K_M
echo Q3_K_L
echo IQ4_NL
echo IQ4_XS
echo Q4_K
echo Q4_K_S
echo Q4_K_M
echo Q5_K
echo Q5_K_S
echo Q5_K_M
echo Q6_K
echo Q8_0
echo Q4_0_4_4
echo Q4_0_4_8
echo Q4_0_8_8
echo F16
echo BF16
echo F32
echo COPY
set /p quantization_type="Enter the quantization type (Press Enter for default: 'Q4_K_S'): "

REM Use default if no input is provided
if "%quantization_type%"=="" (
    set "quantization_type=Q4_K_S"
)

REM Prompt user for input model path
set /p input_model="Enter the full path of the safetensor model (e.g., D:\AI\models\MyFluxModel-dev-fp8.safetensors): "

REM Validate input_model
if not exist "%input_model%" (
    echo Error: Input model file not found at "%input_model%".
    pause
    exit /b 1
)

REM Construct F16 model path
set "f16_model=%input_model:.safetensors=-F16.gguf%"

REM Run the convert.py script
echo.
echo Converting safetensor to F16 gguf...
python "%convert_script_path%" --src "%input_model%"
if errorlevel 1 (
    echo Conversion failed.
    pause
    exit /b 1
)

REM Check if F16 file exists
if not exist "%f16_model%" (
    echo Error: F16 file not found: "%f16_model%".
    pause
    exit /b 1
)
echo F16 file found: "%f16_model%". Proceeding to quantization.

REM Extract model name and folder
for %%F in ("%input_model%") do (
    set "model_name=%%~nF"
    set "output_dir=%%~dpF"
)

REM Construct quantized output model path with actual quantization type in the input model's folder
set "quantized_model=%output_dir%%model_name%-%quantization_type%.gguf"

REM Run llama-quantize.exe with chosen quantization type
echo.
echo Quantizing F16 gguf to %quantization_type% gguf...
"%quantizer_exe%" "%f16_model%" "%quantized_model%" %quantization_type%
if errorlevel 1 (
    echo Quantization failed.
    pause
    exit /b 1
)

REM Verify quantization success
if exist "%quantized_model%" (
    echo Quantization successful. Output file: "%quantized_model%"
    REM Delete the F16 intermediate file
    del "%f16_model%"
    if not exist "%f16_model%" (
        echo Deleted intermediate file: "%f16_model%".
    ) else (
        echo Failed to delete intermediate file: "%f16_model%".
    )
) else (
    echo Error: Quantized file not found: "%quantized_model%".
    pause
    exit /b 1
)

echo.
echo Process completed successfully.
pause
