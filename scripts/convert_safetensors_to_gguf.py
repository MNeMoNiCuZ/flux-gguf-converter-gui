import os
import subprocess
import sys
import argparse
from typing import List, Dict
from tabulate import tabulate

def run_command(command: str, working_dir: str = None) -> None:
    try:
        print(f"Running command: {command}")
        subprocess.run(command, shell=True, cwd=working_dir, stdout=sys.stdout, stderr=sys.stderr, text=True, bufsize=1, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {str(e)}")
        sys.exit(1)

def get_absolute_path(path: str) -> str:
    return os.path.abspath(path)

def get_input_models() -> List[str]:
    print("Enter input models (one per line, empty line to finish):")
    models = []
    while True:
        model = input().strip()
        if not model:
            break
        models.append(get_absolute_path(model))
    return models

def get_output_formats() -> List[str]:
    print("\nEnter output formats (one per line, empty line to finish):")
    print("Available formats: Q4_K_S, Q4_K_M, Q5_K_S, Q5_K_M, Q8_0")
    formats = []
    while True:
        fmt = input().strip()
        if not fmt:
            break
        formats.append(fmt)
    return formats

def generate_conversion_plan(input_models: List[str], output_formats: List[str]) -> List[Dict]:
    plan = []
    for model in input_models:
        f16_model = model.replace(".safetensors", "-F16.gguf")
        for fmt in output_formats:
            output_model = f16_model.replace("-F16.gguf", f"-{fmt}.gguf")
            plan.append({
                "input": model,
                "f16": f16_model,
                "output": output_model,
                "format": fmt
            })
    return plan

def display_plan(plan: List[Dict]) -> None:
    # Display table format
    table_data = []
    for item in plan:
        table_data.append([
            item["input"],
            item["format"],
            item["output"]
        ])
    
    print("\nConversion Plan:")
    print(tabulate(table_data, headers=["Input Model", "Output Format", "Output Path"], tablefmt="grid"))
    
    # Display clean output list
    print("\nOutput Files (one per line):")
    for item in plan:
        print(item["output"])

def process_models(plan: List[Dict], convert_script_dir: str, llama_quantize_exe: str) -> None:
    processed_f16 = set()
    
    for item in plan:
        input_model = item["input"]
        f16_model = item["f16"]
        output_model = item["output"]
        fmt = item["format"]
        
        # Convert to F16 if not already done
        if f16_model not in processed_f16:
            convert_command = f'python "{os.path.join(convert_script_dir, "convert.py")}" --src "{input_model}"'
            run_command(convert_command, working_dir=convert_script_dir)
            processed_f16.add(f16_model)
        
        # Quantize to desired format
        quantize_command = f'"{llama_quantize_exe}" "{f16_model}" "{output_model}" {fmt}'
        run_command(quantize_command)
        
        # Clean up F16 if it's the last output for this input
        if not any(p["f16"] == f16_model and p["output"] != output_model for p in plan):
            if os.path.exists(f16_model):
                os.remove(f16_model)
                print(f"Deleted intermediate file: {f16_model}")

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

def main():
    parser = argparse.ArgumentParser(description="Convert safetensor models to GGUF format with multiple quantization options")
    parser.add_argument("--inputs", nargs="+", help="Input model paths")
    parser.add_argument("--outputs", nargs="+", help="Output quantization formats")
    args = parser.parse_args()

    # Get input models and output formats
    input_models = args.inputs if args.inputs else get_input_models()
    output_formats = args.outputs if args.outputs else get_output_formats()

    if not input_models or not output_formats:
        print("Error: Both input models and output formats are required")
        sys.exit(1)

    # Generate and display conversion plan
    plan = generate_conversion_plan(input_models, output_formats)
    display_plan(plan)

    # Process all models
    paths = get_base_paths()
    process_models(plan, paths["convert_script_dir"], paths["llama_quantize_exe"])

if __name__ == "__main__":
    main() 