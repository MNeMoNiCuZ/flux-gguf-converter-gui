import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict
import converter
import threading
import queue
import psutil
import GPUtil
from datetime import datetime
from tabulate import tabulate

class ConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Flux GGUF Converter")
        self.root.geometry("1000x600")  # Increased height
        self.root.resizable(False, False)
        
        # Initialize queue for thread communication
        self.queue = queue.Queue()
        
        # Load saved preferences
        self.config_file = os.path.join(os.path.dirname(__file__), "config.json")
        self.load_config()
        
        # Initialize variables
        self.selected_files = []
        self.selected_formats = {}
        self.conversion_thread = None
        self.is_converting = False
        self.keep_f16 = tk.BooleanVar(value=self.config.get("keep_f16", False))
        self.output_path = tk.StringVar(value=self.config.get("output_path", ""))
        
        self.create_widgets()
        self.load_saved_formats()
        
        # Start monitoring system resources
        self.start_monitoring()
        
    def start_monitoring(self):
        """Start monitoring system resources in a separate thread"""
        def monitor():
            last_cpu = -1
            last_gpu = -1
            last_memory = ""
            
            while True:
                try:
                    # Get CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    
                    # Get GPU usage if available
                    try:
                        gpus = GPUtil.getGPUs()
                        if gpus:
                            gpu_percent = gpus[0].load * 100
                            gpu_memory = f"{gpus[0].memoryUsed}MB/{gpus[0].memoryTotal}MB"
                        else:
                            gpu_percent = 0
                            gpu_memory = "N/A"
                    except:
                        gpu_percent = 0
                        gpu_memory = "N/A"
                    
                    # Only update if values have changed
                    if (cpu_percent != last_cpu or 
                        gpu_percent != last_gpu or 
                        gpu_memory != last_memory):
                        
                        # Update last values
                        last_cpu = cpu_percent
                        last_gpu = gpu_percent
                        last_memory = gpu_memory
                        
                        # Update status with system info
                        status_text = f"CPU: {cpu_percent}% | GPU: {gpu_percent:.1f}% ({gpu_memory})"
                        if hasattr(self, 'system_status'):
                            self.system_status.config(text=status_text)
                    
                except Exception as e:
                    print(f"Error monitoring system: {e}")
                
                # Sleep for a short time without blocking the GUI
                threading.Event().wait(1)
                
        # Start monitoring in a daemon thread
        threading.Thread(target=monitor, daemon=True).start()
        
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="Input Files", padding="5")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Text input area with scrollbar
        text_scroll = ttk.Scrollbar(file_frame)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.path_text = tk.Text(file_frame, height=6, yscrollcommand=text_scroll.set)
        self.path_text.pack(fill=tk.X, pady=5)
        text_scroll.config(command=self.path_text.yview)
        
        # Button frame
        button_frame = ttk.Frame(file_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # Left side buttons
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side=tk.LEFT)
        
        ttk.Button(
            left_buttons,
            text="Browse Files",
            command=self.add_files
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            left_buttons,
            text="Validate Files",
            command=self.validate_files
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            left_buttons,
            text="Clear All",
            command=self.clear_files
        ).pack(side=tk.LEFT, padx=5)
        
        # Right side buttons
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side=tk.RIGHT)
        
        ttk.Button(
            right_buttons,
            text="Select All Output Formats",
            command=self.select_all_formats
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            right_buttons,
            text="Clear All Output Formats",
            command=self.clear_all_formats
        ).pack(side=tk.LEFT, padx=5)
        
        # Format selection frame
        format_frame = ttk.LabelFrame(main_frame, text="Output Formats", padding="5")
        format_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create grid of format checkboxes
        self.format_vars = {}
        
        # Define format groups
        format_groups = {
            "Q2": ["Q2_K", "Q2_K_S"],
            "Q3": ["Q3_K_S", "Q3_K_M", "Q3_K_L"],
            "Q4": ["Q4_0", "Q4_1", "Q4_K", "Q4_K_S", "Q4_K_M"],
            "Q5": ["Q5_0", "Q5_1", "Q5_K", "Q5_K_S", "Q5_K_M"],
            "Q6": ["Q6_K"],
            "Q8": ["Q8_0"],
            "MISC": ["F16", "BF16", "F32", "COPY"]
        }
        
        # Create column headers
        headers = list(format_groups.keys())
        for i, header in enumerate(headers):
            ttk.Label(format_frame, text=header, font=("Helvetica", 10, "bold")).grid(
                row=0, column=i, padx=5, pady=(0, 2), sticky="w"
            )
        
        # Add formats to grid
        for col, (header, group_formats) in enumerate(format_groups.items()):
            for row, fmt in enumerate(group_formats, start=1):
                var = tk.BooleanVar(value=fmt in self.config.get("selected_formats", {}))
                self.format_vars[fmt] = var
                
                ttk.Checkbutton(
                    format_frame,
                    text=fmt,
                    variable=var,
                    command=self.save_selected_formats
                ).grid(row=row, column=col, padx=5, pady=1, sticky="w")
            
        # Configure grid columns to be equal width
        for i in range(len(format_groups)):
            format_frame.grid_columnconfigure(i, weight=1)
            
        # Output Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding="5")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Output path
        path_frame = ttk.Frame(settings_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(path_frame, text="Output Path:").pack(side=tk.LEFT, padx=(0, 5))
        
        output_entry = ttk.Entry(
            path_frame,
            textvariable=self.output_path
        )
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        output_entry.insert(0, "")  # Clear any existing text
        output_entry.config(foreground="gray")
        
        # Add placeholder text
        def on_focus_in(event):
            if output_entry.get() == "Leave empty to use input file's directory":
                output_entry.delete(0, tk.END)
                output_entry.config(foreground="black")
        
        def on_focus_out(event):
            if not output_entry.get():
                output_entry.insert(0, "Leave empty to use input file's directory")
                output_entry.config(foreground="gray")
        
        output_entry.bind("<FocusIn>", on_focus_in)
        output_entry.bind("<FocusOut>", on_focus_out)
        on_focus_out(None)  # Set initial state
        
        ttk.Button(
            path_frame,
            text="Browse",
            command=self.browse_output_path
        ).pack(side=tk.RIGHT)
        
        # F16 handling
        f16_frame = ttk.Frame(settings_frame)
        f16_frame.pack(fill=tk.X, pady=5)
        
        ttk.Checkbutton(
            f16_frame,
            text="Keep intermediate F16 files",
            variable=self.keep_f16,
            command=self.save_settings
        ).pack(side=tk.LEFT)
        
        # Convert button frame (always at bottom)
        convert_frame = ttk.Frame(main_frame)
        convert_frame.pack(fill=tk.X, pady=(0, 2))
        
        # Convert button
        self.convert_button = ttk.Button(
            convert_frame,
            text="Convert",
            command=self.start_conversion,
            style="Large.TButton"
        )
        self.convert_button.pack(fill=tk.X, pady=2)
        
        # Progress frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 2))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=2)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 2))
        
        # Status label
        self.status_label = ttk.Label(status_frame, text="")
        self.status_label.pack(fill=tk.X)
        
        # System status label
        self.system_status = ttk.Label(status_frame, text="")
        self.system_status.pack(fill=tk.X)
        
        # Create custom style for large button
        style = ttk.Style()
        style.configure("Large.TButton", font=("Helvetica", 12))
        
    def check_queue(self):
        """Check for messages from the conversion thread"""
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg["type"] == "progress":
                    self.progress_var.set(msg["progress"])
                    self.status_label.config(text=msg["message"])
                elif msg["type"] == "complete":
                    self.is_converting = False
                    self.convert_button.config(state="normal")
                    self.status_label.config(text="Conversion completed successfully!")
                    messagebox.showinfo("Success", "Conversion completed successfully!")
                elif msg["type"] == "error":
                    self.is_converting = False
                    self.convert_button.config(state="normal")
                    self.status_label.config(text="Conversion failed!")
                    messagebox.showerror("Error", msg["text"])
        except queue.Empty:
            pass
        finally:
            if self.is_converting:
                self.root.after(100, self.check_queue)
                
    def start_conversion(self):
        if self.is_converting:
            return
            
        # Get files from text area
        text = self.path_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showerror("Error", "Please add at least one input file")
            return
            
        files = [line.strip() for line in text.split('\n') if line.strip()]
        if not files:
            messagebox.showerror("Error", "Please add at least one input file")
            return
            
        # Validate files before proceeding
        if not self.validate_files():
            messagebox.showerror("Error", "Please fix invalid files before proceeding")
            return
            
        selected_formats = [
            fmt for fmt, var in self.format_vars.items()
            if var.get()
        ]
        
        if not selected_formats:
            messagebox.showerror("Error", "Please select at least one output format")
            return
            
        # Disable convert button and start conversion thread
        self.is_converting = True
        self.convert_button.config(state="disabled")
        self.progress_var.set(0)
        self.status_label.config(text="Starting conversion...")
        
        # Start conversion thread
        self.conversion_thread = threading.Thread(
            target=self.conversion_worker,
            args=(files, selected_formats),
            daemon=True
        )
        self.conversion_thread.start()
        
        # Start checking queue
        self.check_queue()
        
    def conversion_worker(self, files, selected_formats):
        """Worker thread for conversion process"""
        try:
            paths = converter.get_base_paths()
            plan = converter.generate_conversion_plan(files, selected_formats)
            
            # Display conversion plan in console
            print("\nConversion Plan:")
            table_data = []
            for item in plan:
                for output in item["outputs"]:
                    table_data.append([
                        item["input"],
                        output["format"]
                    ])
            print(tabulate(table_data, headers=["Input Model", "Output Format"], tablefmt="grid"))
            
            # Get output directory, if specified
            output_dir = self.output_path.get()
            if output_dir == "Leave empty to use input file's directory":
                output_dir = ""
            
            def progress_callback(progress_info):
                """Handle progress updates"""
                self.queue.put({
                    "type": "progress",
                    "progress": progress_info["progress"],
                    "message": progress_info["message"]
                })
            
            # Process models
            converter.process_models(
                plan,
                paths["convert_script_dir"],
                paths["llama_quantize_exe"],
                progress_callback=progress_callback,
                output_dir=output_dir if output_dir else None,
                keep_f16=self.keep_f16.get()
            )
            
            # Display final output files list
            print("\nOutput Files (one per line):")
            for item in plan:
                for output in item["outputs"]:
                    print(output["output"])
            
            self.queue.put({"type": "complete"})
            
        except Exception as e:
            self.queue.put({"type": "error", "text": str(e)})
            
    def update_progress(self, processed, total):
        """Update progress in the GUI"""
        progress = (processed / total) * 100
        self.queue.put({
            "type": "progress",
            "value": progress,
            "text": f"Processing output {processed}/{total} ({progress:.1f}%)"
        })
        
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "selected_formats": {},
                "keep_f16": False,
                "output_path": ""
            }
            self.save_config()
            
    def save_config(self):
        # Only save selected formats
        config = {
            "selected_formats": {
                fmt: var.get()
                for fmt, var in self.format_vars.items()
            },
            "keep_f16": self.keep_f16.get(),
            "output_path": self.output_path.get()
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
            
    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Select Model Files",
            filetypes=[
                ("All Supported Formats", "*.safetensors;*.pth;*.pt;*.bin"),
                ("Safetensors Files", "*.safetensors"),
                ("PyTorch Files", "*.pth;*.pt;*.bin"),
                ("All Files", "*.*")
            ]
        )
        if files:
            # Get current text and add new files
            current_text = self.path_text.get("1.0", tk.END).strip()
            new_files = "\n".join(files)
            
            # Combine with existing text, avoiding duplicates
            all_files = set(current_text.split("\n") if current_text else [])
            all_files.update(files)
            
            # Update text area with all files
            self.path_text.delete("1.0", tk.END)
            self.path_text.insert("1.0", "\n".join(sorted(all_files)))
            
            # Validate the files
            self.validate_files()
                
    def validate_files(self):
        text = self.path_text.get("1.0", tk.END).strip()
        if not text:
            self.status_label.config(text="No files to validate")
            return False
            
        # Split into lines and clean up
        paths = [line.strip() for line in text.split('\n') if line.strip()]
        
        valid_files = []
        invalid_files = []
        existing_outputs = []
        
        # Get selected formats for output validation
        selected_formats = [
            fmt for fmt, var in self.format_vars.items()
            if var.get()
        ]
        
        for file in paths:
            file = file.strip()
            if not file:
                continue
                
            if not os.path.exists(file):
                invalid_files.append(f"{file} (File not found)")
                continue
                
            # Check for supported extensions
            ext = os.path.splitext(file)[1].lower()
            if ext not in ['.safetensors', '.pth', '.pt', '.bin']:
                invalid_files.append(f"{file} (Unsupported format: {ext})")
                continue
                
            valid_files.append(file)
            
            # Check for existing outputs if formats are selected
            if selected_formats:
                f16_model = file.replace(".safetensors", "-F16.gguf")
                for fmt in selected_formats:
                    output_model = f16_model.replace("-F16.gguf", f"-{fmt}.gguf")
                    
                    # If output directory is specified, modify the path
                    output_dir = self.output_path.get()
                    if output_dir and output_dir != "Leave empty to use input file's directory":
                        output_model = os.path.join(output_dir, os.path.basename(output_model))
                    
                    if os.path.exists(output_model) and os.path.getsize(output_model) > 0:
                        existing_outputs.append(f"{os.path.basename(file)} -> {fmt}")
        
        # Update status and show warnings
        status_parts = []
        if valid_files:
            status_parts.append(f"{len(valid_files)} valid files")
        if invalid_files:
            status_parts.append(f"{len(invalid_files)} invalid files")
        if existing_outputs:
            status_parts.append(f"{len(existing_outputs)} existing outputs")
            
        self.status_label.config(text=", ".join(status_parts))
        
        # Show warnings
        warnings = []
        if invalid_files:
            warnings.append("The following files were invalid:\n" + "\n".join(invalid_files))
        if existing_outputs:
            warnings.append("The following outputs already exist and will be skipped:\n" + "\n".join(existing_outputs))
            
        if warnings:
            messagebox.showwarning(
                "Validation Results",
                "\n\n".join(warnings)
            )
            return len(invalid_files) == 0  # Return True if no invalid files
        
        return True
                
    def clear_files(self):
        self.path_text.delete("1.0", tk.END)
        self.status_label.config(text="")
        
    def load_saved_formats(self):
        """Load saved format selections from config"""
        saved_formats = self.config.get("selected_formats", {})
        for fmt, var in self.format_vars.items():
            # Only set to True if explicitly saved as True
            var.set(saved_formats.get(fmt, False))
            
    def save_selected_formats(self):
        self.config["selected_formats"] = {
            fmt: var.get()
            for fmt, var in self.format_vars.items()
        }
        self.save_config()

    def select_all_formats(self):
        """Select all output formats"""
        for var in self.format_vars.values():
            var.set(True)
        self.save_selected_formats()
        
    def clear_all_formats(self):
        """Clear all output formats"""
        for var in self.format_vars.values():
            var.set(False)
        self.save_selected_formats()

    def browse_output_path(self):
        path = filedialog.askdirectory(
            title="Select Output Directory"
        )
        if path:
            self.output_path.set(path)
            self.save_settings()
            
    def save_settings(self):
        self.config["keep_f16"] = self.keep_f16.get()
        self.config["output_path"] = self.output_path.get()
        if self.config["output_path"] == "Leave empty to use input file's directory":
            self.config["output_path"] = ""
        self.save_config()

def main():
    root = tk.Tk()
    app = ConverterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 