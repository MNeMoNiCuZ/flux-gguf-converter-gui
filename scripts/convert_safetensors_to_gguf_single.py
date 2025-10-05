import os
import subprocess
import sys
from typing import Dict
import argparse

def run_command(command: str, working_dir: str = None) -> None:
    try:
        print(f"Running command: {command}")
        result = subprocess.run(command, shell=True, cwd=working_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Print output for debugging
        print(result.stdout.decode())
        if result.stderr:
            print(f"Error: {result.stderr.decode()}")
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {str(e)}")
        sys.exit(1)

def get_absolute_path(path: str) -> str:
    return os.path.abspath(path)

def get_base_paths() -> Dict[str, str]:
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to get the base directory
    base_dir = os.path.dirname(script_dir)
    
    return {
        "base_dir": base_dir,
        "convert_script_dir": os.path.join(base_dir, "llama.cpp"),
        "llama_quantize_exe": os.path.join(base_dir, "build", "bin", "Debug", "llama-quantize.exe")
    }

def process_single_model(input_model: str, output_format: str, paths: Dict[str, str]) -> None:
    # Convert paths to absolute
    input_model = get_absolute_path(input_model)
    
    # Generate output paths
    f16_model = input_model.replace(".safetensors", "-F16.gguf")
    output_model = f16_model.replace("-F16.gguf", f"-{output_format}.gguf")
    
    # Convert to F16
    convert_command = f'python "{os.path.join(paths["convert_script_dir"], "convert.py")}" --src "{input_model}"'
    run_command(convert_command, working_dir=paths["convert_script_dir"])
    
    # Quantize to desired format
    quantize_command = f'"{paths["llama_quantize_exe"]}" "{f16_model}" "{output_model}" {output_format}'
    run_command(quantize_command)
    
    # Clean up F16
    if os.path.exists(f16_model):
        os.remove(f16_model)
        print(f"Deleted intermediate file: {f16_model}")
    
    print(f"\nConversion complete!")
    print(f"Input: {input_model}")
    print(f"Output: {output_model}")

def main():
    parser = argparse.ArgumentParser(description="Convert a single safetensor model to GGUF format")
    parser.add_argument("--input", required=True, help="Input model path")
    parser.add_argument("--output", required=True, help="Output quantization format (e.g., Q4_K_S, Q5_K_M)")
    args = parser.parse_args()

    # Get base paths
    paths = get_base_paths()
    
    # Process the model
    process_single_model(args.input, args.output, paths)

if __name__ == "__main__":
    main()
