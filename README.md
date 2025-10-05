# Flux GGUF Converter

A tool with a graphical user interface (GUI) and command-line scripts for converting Flux-based SAFETENSOR models to the GGUF format, using [llama.cpp](https://github.com/ggerganov/llama.cpp) for quantization.

## Features

-   **Easy-to-use GUI** for converting models.
-   Process **multiple files** at once.
-   Select from a wide range of **quantization formats**.
-   Monitor **CPU and GPU usage** during conversion.
-   Option to **retain intermediate F16 files**.
-   Specify a **custom directory for output files**.
-   **Command-line interface** for interactive and argument-based processing.

## Prerequisites & Installation

The setup process involves three main steps: cloning the required repositories, setting up a unified Python virtual environment, and compiling `llama.cpp`.

### Step 1: Clone Repositories

1.  **Clone this project (`flux-gguf-converter-gui`):**
    ```bash
    git clone <repository-url>
    cd flux-gguf-converter-gui
    ```

2.  **Clone `llama.cpp`:**
    It is crucial that you clone `llama.cpp` into the `flux-gguf-converter-gui` directory.
    ```bash
    git clone https://github.com/ggerganov/llama.cpp.git
    ```

Your folder structure should look like this:

```
/flux-gguf-converter-gui/
|-- scripts/
|-- llama.cpp/
|   |-- build/
|   |-- ...
|-- launch_converter_gui.bat
|-- ...
```

### Step 2: Create Virtual Environment & Install Dependencies

To ensure all Python scripts work correctly, you should create a single virtual environment inside the `llama.cpp` directory and install the requirements for both projects into it.

1.  **Run the venv creation script:**
    This script is configured to create the virtual environment inside the `llama.cpp` folder within the project directory.
    ```bash
    venv_create.bat
    ```
    Follow the on-screen prompts. This will create a `venv` folder inside `llama.cpp` and install the required packages from `requirements.txt` (for this GUI) and `llama.cpp/requirements.txt`.

### Step 3: Patch and Compile `llama.cpp`

1.  **Navigate into the `llama.cpp` directory:**
    ```bash
    cd llama.cpp 
    ```

2.  **Apply Patch:**
    If you have a patch file (e.g., `lcpp.patch`), apply it using the following command:
    ```bash
    git apply lcpp.patch
    ```

3.  **Compile `llama.cpp`:**
    The recommended method is using `cmake`.
    ```bash
    # Create a build directory
    mkdir build
    cd build

    # Configure the build
    cmake ..

    # Compile the quantize tool. 
    # We use the Debug config because the scripts are configured to look for the executable in the .../bin/Debug/ directory.
    # The -j flag speeds up compilation by using multiple cores.
    cmake --build . --config Debug -j10 --target llama-quantize
    ```

    After a successful compilation, you should have `llama-quantize.exe` inside the `llama.cpp/build/bin/Debug` directory. The scripts are configured to find it there.

## Usage

### Using the GUI

1.  Navigate to the `flux-gguf-converter-gui` directory.
2.  Run the `launch_converter_gui.bat` script. This will activate the correct virtual environment and start the app.
3.  **Add Files:** Click "Browse Files" to select one or more `.safetensors` models.
4.  **Select Output Formats:** Check the boxes for the GGUF formats you want to create.
5.  **Convert:** Click the "Convert" button to begin.

### Using the Command-Line Scripts

Activate the virtual environment first by running `venv_activate.bat` inside the `llama.cpp` directory, then run the scripts from the `flux-gguf-converter-gui` directory.

#### Interactive Multi-File Conversion
This script allows you to convert multiple models at once. If you run it without arguments, it will enter an interactive mode where you can specify the input models and output formats.
```bash
python scripts/convert_safetensors_to_gguf.py
```

#### Command-Line Arguments and Examples

##### `convert_safetensors_to_gguf.py`

| Argument | Description | Example |
| --- | --- | --- |
| `--inputs` | One or more paths to the input `.safetensors` models. | `--inputs "C:\models\model1.safetensors" "C:\models\model2.safetensors"` |
| `--outputs`| One or more quantization formats to output. | `--outputs Q4_K_S Q8_0` |

**Windows Example:**
```bash
python scripts/convert_safetensors_to_gguf.py --inputs "C:\models\MyModel.safetensors" --outputs Q4_K_S Q8_0
```

**Linux Example:**
```bash
python scripts/convert_safetensors_to_gguf.py --inputs "/models/MyModel.safetensors" --outputs Q4_K_S Q8_0
```

##### `convert_safetensors_to_gguf_single.py`

| Argument | Description | Example |
| --- | --- | --- |
| `--input` | The path to the input `.safetensors` model. | `--input "C:\models\MyModel.safetensors"` |
| `--output`| The quantization format to output. | `--output Q4_K_S` |

**Windows Example:**
```bash
python scripts/convert_safetensors_to_gguf_single.py --input "C:\models\MyModel.safetensors" --output Q4_K_S
```

**Linux Example:**
```bash
python scripts/convert_safetensors_to_gguf_single.py --input "/models/MyModel.safetensors" --output Q4_K_S
```

## Appendix

### Manual Conversion Process

The conversion is a two-step process handled automatically by the scripts:

1.  **Convert `.safetensors` to a temporary `F16.gguf` file:**
    This is done by `llama.cpp`'s `convert.py` script.
    ```bash
    python convert.py --src H:\AI\Models\MyModel.safetensors
    ```

2.  **Quantize the `F16.gguf` file to the final target format:**
    This is done by the `llama-quantize` executable you compiled.
    ```bash
    build\bin\Debug\llama-quantize.exe H:\AI\Models\MyModel-F16.gguf H:\AI\Models\MyModel-Q4_K_S.gguf Q4_K_S
    ```

### Available Quantization Types

The following is a list of quantization types supported by `llama.cpp`:

```
   2  or  Q4_0    :  4.34G, +0.4685 ppl @ Llama-3-8B
   3  or  Q4_1    :  4.78G, +0.4511 ppl @ Llama-3-8B
   8  or  Q5_0    :  5.21G, +0.1316 ppl @ Llama-3-8B
   9  or  Q5_1    :  5.65G, +0.1062 ppl @ Llama-3-8B
  19  or  IQ2_XXS :  2.06 bpw quantization
  20  or  IQ2_XS  :  2.31 bpw quantization
  28  or  IQ2_S   :  2.5  bpw quantization
  29  or  IQ2_M   :  2.7  bpw quantization
  24  or  IQ1_S   :  1.56 bpw quantization
  31  or  IQ1_M   :  1.75 bpw quantization
  10  or  Q2_K    :  2.96G, +3.5199 ppl @ Llama-3-8B
  21  or  Q2_K_S  :  2.96G, +3.1836 ppl @ Llama-3-8B
  23  or  IQ3_XXS :  3.06 bpw quantization
  26  or  IQ3_S   :  3.44 bpw quantization
  27  or  IQ3_M   :  3.66 bpw quantization mix
  12  or  Q3_K    : alias for Q3_K_M
  22  or  IQ3_XS  :  3.3 bpw quantization
  11  or  Q3_K_S  :  3.41G, +1.6321 ppl @ Llama-3-8B
  12  or  Q3_K_M  :  3.74G, +0.6569 ppl @ Llama-3-8B
  13  or  Q3_K_L  :  4.03G, +0.5562 ppl @ Llama-3-8B
  25  or  IQ4_NL  :  4.50 bpw non-linear quantization
  30  or  IQ4_XS  :  4.25 bpw non-linear quantization
  15  or  Q4_K    : alias for Q4_K_M
  14  or  Q4_K_S  :  4.37G, +0.2689 ppl @ Llama-3-8B
  15  or  Q4_K_M  :  4.58G, +0.1754 ppl @ Llama-3-8B
  17  or  Q5_K    : alias for Q5_K_M
  16  or  Q5_K_S  :  5.21G, +0.1049 ppl @ Llama-3-8B
  17  or  Q5_K_M  :  5.33G, +0.0569 ppl @ Llama-3-8B
  18  or  Q6_K    :  6.14G, +0.0217 ppl @ Llama-3-8B
   7  or  Q8_0    :  7.96G, +0.0026 ppl @ Llama-3-8B
  33  or  Q4_0_4_4 :  4.34G, +0.4685 ppl @ Llama-3-8B
  34  or  Q4_0_4_8 :  4.34G, +0.4685 ppl @ Llama-3-8B
  35  or  Q4_0_8_8 :  4.34G, +0.4685 ppl @ Llama-3-8B
   1  or  F16     : 14.00G, +0.0020 ppl @ Mistral-7B
  32  or  BF16    : 14.00G, -0.0050 ppl @ Mistral-7B
   0  or  F32     : 26.00G              @ 7B
          COPY    : only copy tensors, no quantizing
```

## References

-   [llama.cpp](https://github.com/ggerganov/llama.cpp): The underlying conversion and quantization tools are from this repository.
-   [llama.cpp/src/llama-arch.h](https://github.com/ggerganov/llama.cpp/blob/master/src/llama-arch.h): The source file defining the supported model architectures in `llama.cpp`.

## Acknowledgements

-   [city96/ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF): The conversion script used in this project is based on the work from this repository. We acknowledge and appreciate their contribution to the open-source community.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.