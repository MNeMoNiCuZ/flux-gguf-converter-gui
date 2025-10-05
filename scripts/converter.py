import os
import subprocess
import sys
from typing import List, Dict, Callable

def run_command(command: str, working_dir: str = None) -> None:
    try:
        print(f"Running command: {command}")
        subprocess.run(command, shell=True, cwd=working_dir, stdout=sys.stdout, stderr=sys.stderr, text=True, bufsize=1, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {str(e)}")
        raise

def get_absolute_path(path: str) -> str:
    return os.path.abspath(path)

def generate_conversion_plan(input_models: List[str], output_formats: List[str]) -> List[Dict]:
    plan = []
    for model in input_models:
        f16_model = model.replace(".safetensors", "-F16.gguf")
        outputs = []
        for fmt in output_formats:
            output_model = f16_model.replace("-F16.gguf", f"-{fmt}.gguf")
            outputs.append({
                "format": fmt,
                "output": output_model,
                "exists": os.path.exists(output_model) and os.path.getsize(output_model) > 0
            })
        plan.append({
            "input": model,
            "f16": f16_model,
            "outputs": outputs
        })
    return plan

def process_models(plan: List[Dict], convert_script_dir: str, llama_quantize_exe: str, progress_callback: Callable[[], None] = None, output_dir: str = None, keep_f16: bool = False) -> None:
    # Count only non-existing outputs for progress
    total_conversions = sum(1 for item in plan for output in item["outputs"] if not output["exists"])
    if total_conversions == 0:
        if progress_callback:
            progress_callback({
                "message": "All outputs already exist, nothing to do!",
                "progress": 100,
                "current": 0,
                "total": 0
            })
        return
        
    current_conversion = 0
    
    def update_progress(message: str, progress: float = None):
        if progress_callback:
            if progress is None:
                progress = (current_conversion / total_conversions) * 100
            progress_callback({
                "message": message,
                "progress": progress,
                "current": current_conversion,
                "total": total_conversions
            })
    
    for model_idx, item in enumerate(plan, 1):
        input_model = item["input"]
        f16_model = item["f16"]
        outputs = item["outputs"]
        model_name = os.path.basename(input_model)
        
        # Skip if all outputs for this model already exist
        if all(output["exists"] for output in outputs):
            update_progress(f"Skipping model {model_idx}/{len(plan)}, all outputs exist: {model_name}")
            continue
            
        try:
            # Check if F16 exists and has non-zero size
            if os.path.exists(f16_model) and os.path.getsize(f16_model) > 0:
                update_progress(f"Using existing F16 file for model {model_idx}/{len(plan)}: {model_name}")
                print(f"Using existing F16 file: {f16_model}")
            else:
                update_progress(f"Converting model {model_idx}/{len(plan)} to F16 as an intermediate step: {model_name}")
                print(f"\nConverting to F16: {input_model}")
                convert_command = f'python "{os.path.join(convert_script_dir, "convert.py")}" --src "{input_model}" --dst "{f16_model}"'
                run_command(convert_command, working_dir=convert_script_dir)
            
            # Verify F16 file exists and has size
            if not os.path.exists(f16_model) or os.path.getsize(f16_model) == 0:
                update_progress(f"Error: F16 file not found or empty for model {model_idx}/{len(plan)}: {model_name}")
                print(f"Error: F16 file not found or empty: {f16_model}")
                continue
            
            # Process all quantizations for this input file
            need_f16 = False
            for output in outputs:
                fmt = output["format"]
                output_model = output["output"]
                
                # Skip if output already exists
                if output["exists"]:
                    update_progress(f"Skipping existing {fmt} output for model {model_idx}/{len(plan)}: {model_name}")
                    continue
                    
                # If output_dir is specified, modify the output path
                if output_dir:
                    output_model = os.path.join(output_dir, os.path.basename(output_model))
                    output["output"] = output_model  # Update the plan
                
                try:
                    # Create output directory if it doesn't exist
                    os.makedirs(os.path.dirname(output_model), exist_ok=True)
                    
                    update_progress(f"Quantizing model {model_idx}/{len(plan)} to {fmt}: {model_name}")
                    print(f"\nQuantizing to {fmt}: {output_model}")
                    # Quantize to desired format
                    quantize_command = f'"{llama_quantize_exe}" "{f16_model}" "{output_model}" {fmt}'
                    run_command(quantize_command)
                    
                    # Update progress
                    current_conversion += 1
                    update_progress(f"Completed {fmt} quantization for model {model_idx}/{len(plan)}: {model_name}")
                    
                    # Mark if we need F16 (it's one of our desired outputs)
                    if fmt == "F16":
                        need_f16 = True
                        
                except Exception as e:
                    update_progress(f"Error creating {fmt} output for model {model_idx}/{len(plan)}: {model_name}")
                    print(f"Error creating {fmt} output: {str(e)}")
                    continue
            
            # Clean up F16 if:
            # 1. We're not keeping F16 files AND
            # 2. F16 isn't one of the desired outputs AND
            # 3. At least one quantization was successful
            should_keep = keep_f16 or need_f16 or "F16" in [out["format"] for out in outputs]
            if not should_keep and any(os.path.exists(out["output"]) for out in outputs):
                if os.path.exists(f16_model):
                    os.remove(f16_model)
                    update_progress(f"Cleaned up intermediate F16 file for model {model_idx}/{len(plan)}: {model_name}")
                    print(f"Deleted intermediate file: {f16_model}")
                    
        except Exception as e:
            update_progress(f"Error processing model {model_idx}/{len(plan)}: {model_name}")
            print(f"Error processing {input_model}: {str(e)}")
            continue

def get_base_paths() -> Dict[str, str]:
    # Get the directory where this script is located (scripts/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to get the base directory
    base_dir = os.path.dirname(script_dir)
    # Set convert script dir (llama.cpp)
    convert_script_dir = os.path.join(base_dir, "llama.cpp")
    # Set quantize exe path (llama.cpp/build/bin/Debug/llama-quantize.exe)
    llama_quantize_exe = os.path.join(convert_script_dir, "build", "bin", "Debug", "llama-quantize.exe")
    
    return {
        "base_dir": base_dir,
        "convert_script_dir": convert_script_dir,
        "llama_quantize_exe": llama_quantize_exe
    }