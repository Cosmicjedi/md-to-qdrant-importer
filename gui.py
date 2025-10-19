"""
GUI Application for MD to Qdrant Importer
User-friendly interface for bulk importing markdown files
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from threading import Thread
from typing import Optional
import json
import os

from config import Config, get_config
from import_processor import ImportProcessor, ImportResult


class ImporterGUI:
    """Main GUI application"""
    
    def __init__(self, root: tk.Tk):
        """
        Initialize GUI
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("MD to Qdrant Importer")
        self.root.geometry("900x750")
        
        # Configuration
        self.config: Optional[Config] = None
        self.processor: Optional[ImportProcessor] = None
        
        # Processing state
        self.is_processing = False
        self.current_results = []
        
        # Create GUI
        self._create_menu()
        self._create_widgets()
        
        # Try to load config
        self._load_config()
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Config", command=self._load_config_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_widgets(self):
        """Create main widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # Configuration status
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="5")
        config_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        self.config_status_label = ttk.Label(config_frame, text="Not loaded", foreground="red")
        self.config_status_label.grid(row=0, column=0, sticky=tk.W)
        
        ttk.Button(config_frame, text="Load/Reload Config", command=self._load_config).grid(
            row=0, column=1, sticky=tk.E
        )
        
        # Collection prefix configuration
        prefix_frame = ttk.LabelFrame(main_frame, text="Collection Prefix", padding="5")
        prefix_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        prefix_frame.columnconfigure(1, weight=1)
        
        ttk.Label(prefix_frame, text="Prefix:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.prefix_var = tk.StringVar(value="game")
        prefix_entry = ttk.Entry(prefix_frame, textvariable=self.prefix_var, width=30)
        prefix_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        ttk.Button(prefix_frame, text="Update Collections", command=self._update_prefix).grid(
            row=0, column=2, padx=5
        )
        
        # Collections preview
        self.collections_label = ttk.Label(prefix_frame, text="Collections: (not configured)", foreground="gray")
        self.collections_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # Input directory selection
        input_frame = ttk.LabelFrame(main_frame, text="Input Directory", padding="5")
        input_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)
        
        self.input_dir_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.input_dir_var, state='readonly').grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5)
        )
        ttk.Button(input_frame, text="Browse...", command=self._browse_input).grid(
            row=0, column=1
        )
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="5")
        options_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Include subdirectories (recursive)",
            variable=self.recursive_var
        ).grid(row=0, column=0, sticky=tk.W)
        
        self.skip_existing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Skip files already in database",
            variable=self.skip_existing_var
        ).grid(row=1, column=0, sticky=tk.W)
        
        self.extract_npcs_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Extract NPCs (requires Azure AI)",
            variable=self.extract_npcs_var
        ).grid(row=2, column=0, sticky=tk.W)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, pady=(0, 10))
        
        self.import_button = ttk.Button(
            button_frame,
            text="Start Import",
            command=self._start_import,
            state='disabled'
        )
        self.import_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(
            button_frame,
            text="Stop",
            command=self._stop_import,
            state='disabled'
        )
        self.stop_button.grid(row=0, column=1, padx=5)
        
        ttk.Button(
            button_frame,
            text="View Stats",
            command=self._show_stats
        ).grid(row=0, column=2, padx=5)
        
        ttk.Button(
            button_frame,
            text="Save Results",
            command=self._save_results
        ).grid(row=0, column=3, padx=5)
        
        # Progress and log
        log_frame = ttk.LabelFrame(main_frame, text="Progress", padding="5")
        log_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            log_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Log text
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            wrap=tk.WORD,
            state='disabled'
        )
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar
        self.status_label = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_label.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
    
    def _update_collections_display(self):
        """Update the collections preview label"""
        if self.config:
            prefix = self.prefix_var.get()
            collections_text = (
                f"Collections: {prefix}_npcs, {prefix}_rulebooks, {prefix}_adventurepaths"
            )
            self.collections_label.config(text=collections_text, foreground="black")
    
    def _update_prefix(self):
        """Update the collection prefix"""
        new_prefix = self.prefix_var.get().strip()
        
        if not new_prefix:
            messagebox.showwarning("Warning", "Prefix cannot be empty")
            return
        
        # Validate prefix (basic check for valid collection name)
        if not new_prefix.replace('_', '').replace('-', '').isalnum():
            messagebox.showwarning(
                "Warning",
                "Prefix can only contain letters, numbers, underscores, and hyphens"
            )
            return
        
        # Update environment variable
        os.environ['QDRANT_COLLECTION_PREFIX'] = new_prefix
        
        # Reload config with force_reload to pick up new prefix
        self._load_config(force_reload=True)
        
        self._log(f"Collection prefix updated to: {new_prefix}")
        self._update_collections_display()
    
    def _log(self, message: str):
        """Add message to log"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def _update_status(self, message: str):
        """Update status bar"""
        self.status_label.config(text=message)
    
    def _load_config_file(self):
        """Load config from selected file"""
        file_path = filedialog.askopenfilename(
            title="Select .env file",
            filetypes=[("Environment files", "*.env"), ("All files", "*.*")]
        )
        if file_path:
            self._load_config(file_path, force_reload=True)
    
    def _load_config(self, env_file: Optional[str] = None, force_reload: bool = False):
        """Load configuration"""
        try:
            # FIXED: Force reload when needed to pick up new prefix
            self.config = get_config(env_file, force_reload=force_reload)
            is_valid, errors = self.config.validate()
            
            if is_valid:
                self.config_status_label.config(text="Loaded ✓", foreground="green")
                self._log("Configuration loaded successfully")
                self._log(str(self.config))
                
                # Update prefix from config
                self.prefix_var.set(self.config.qdrant_collection_prefix)
                self._update_collections_display()
                
                # Initialize processor
                self.processor = ImportProcessor(
                    self.config,
                    progress_callback=self._progress_callback
                )
                
                # Set default input directory
                if self.config.input_directory.exists():
                    self.input_dir_var.set(str(self.config.input_directory))
                
                # Enable import button
                self.import_button.config(state='normal')
            else:
                self.config_status_label.config(text="Invalid ✗", foreground="red")
                error_msg = "Configuration errors:\n" + "\n".join(errors)
                self._log(error_msg)
                messagebox.showerror("Configuration Error", error_msg)
                
        except Exception as e:
            self.config_status_label.config(text="Error ✗", foreground="red")
            self._log(f"Error loading config: {e}")
            messagebox.showerror("Error", f"Failed to load configuration:\n{e}")
    
    def _browse_input(self):
        """Browse for input directory"""
        directory = filedialog.askdirectory(title="Select Input Directory")
        if directory:
            self.input_dir_var.set(directory)
    
    def _progress_callback(self, message: str, current: int = 0, total: int = 0):
        """Callback for progress updates"""
        self._log(message)
        if total > 0:
            progress = (current / total) * 100
            self.progress_var.set(progress)
        self._update_status(message)
    
    def _start_import(self):
        """Start import process"""
        if self.is_processing:
            return
        
        # Validate input directory
        input_dir = self.input_dir_var.get()
        if not input_dir:
            messagebox.showwarning("Warning", "Please select an input directory")
            return
        
        input_path = Path(input_dir)
        if not input_path.exists():
            messagebox.showerror("Error", f"Directory does not exist: {input_dir}")
            return
        
        # Show current collections being used
        prefix = self.prefix_var.get()
        collections_info = (
            f"Collections that will be used:\n"
            f"  - {prefix}_npcs (for NPCs)\n"
            f"  - {prefix}_rulebooks (for rulebooks)\n"
            f"  - {prefix}_adventurepaths (for adventures)"
        )
        
        # Confirm
        if not messagebox.askyesno(
            "Confirm Import",
            f"Import markdown files from:\n{input_dir}\n\n{collections_info}\n\nContinue?"
        ):
            return
        
        # Start processing in background thread
        self.is_processing = True
        self.import_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress_var.set(0)
        self.current_results = []
        
        thread = Thread(target=self._run_import, args=(input_path,), daemon=True)
        thread.start()
    
    def _run_import(self, input_path: Path):
        """Run import in background thread"""
        try:
            self._log("=" * 60)
            self._log(f"Starting import from: {input_path}")
            self._log(f"Collection prefix: {self.config.qdrant_collection_prefix}")
            self._log("=" * 60)
            
            results = self.processor.process_directory(
                directory=input_path,
                recursive=self.recursive_var.get(),
                skip_existing=self.skip_existing_var.get(),
                extract_npcs=self.extract_npcs_var.get()
            )
            
            self.current_results = results
            
            # Summary
            successful = sum(1 for r in results if r.success)
            failed = sum(1 for r in results if not r.success)
            total_chunks = sum(r.chunks_imported for r in results)
            total_npcs = sum(r.npcs_extracted for r in results)
            
            # Collection distribution
            collection_counts = {}
            for r in results:
                if r.success and r.collection_used:
                    collection_counts[r.collection_used] = collection_counts.get(r.collection_used, 0) + 1
            
            self._log("=" * 60)
            self._log("Import Complete!")
            self._log(f"Total files: {len(results)}")
            self._log(f"Successful: {successful}")
            self._log(f"Failed: {failed}")
            self._log(f"Total chunks imported: {total_chunks}")
            self._log(f"Total NPCs extracted: {total_npcs}")
            self._log("\nCollection Distribution:")
            for coll, count in collection_counts.items():
                self._log(f"  {coll}: {count} files")
            self._log("=" * 60)
            
            # FIXED: Capture the success message in the closure
            success_message = (
                f"Import finished!\n\n"
                f"Files processed: {len(results)}\n"
                f"Successful: {successful}\n"
                f"Failed: {failed}\n"
                f"Chunks imported: {total_chunks}\n"
                f"NPCs extracted: {total_npcs}"
            )
            
            self.root.after(0, lambda msg=success_message: messagebox.showinfo(
                "Import Complete",
                msg
            ))
            
        except Exception as error:
            # FIXED: Capture the error message in a variable before the lambda
            error_message = f"An error occurred during import:\n{error}"
            self._log(f"ERROR: {error}")
            self.root.after(0, lambda msg=error_message: messagebox.showerror(
                "Import Error",
                msg
            ))
        
        finally:
            self.is_processing = False
            self.root.after(0, self._import_finished)
    
    def _import_finished(self):
        """Called when import finishes"""
        self.import_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.progress_var.set(100)
        self._update_status("Import complete")
    
    def _stop_import(self):
        """Stop import process"""
        # Note: This is a simplified version. Full implementation would need
        # proper threading control with events/flags
        self.is_processing = False
        self._log("Stop requested (will finish current file)...")
    
    def _show_stats(self):
        """Show database statistics"""
        if not self.processor:
            messagebox.showwarning("Warning", "Please load configuration first")
            return
        
        try:
            stats = self.processor.get_stats()
            
            stats_window = tk.Toplevel(self.root)
            stats_window.title("Database Statistics")
            stats_window.geometry("500x400")
            
            text = scrolledtext.ScrolledText(stats_window, wrap=tk.WORD)
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text.insert(tk.END, json.dumps(stats, indent=2))
            text.config(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get statistics:\n{e}")
    
    def _save_results(self):
        """Save import results to file"""
        if not self.current_results:
            messagebox.showwarning("Warning", "No results to save")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Results",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.processor.save_results(self.current_results, Path(file_path))
                self._log(f"Results saved to: {file_path}")
                messagebox.showinfo("Success", "Results saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save results:\n{e}")
    
    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About",
            "MD to Qdrant Importer\n\n"
            "Bulk import markdown files to Qdrant vector database\n"
            "with intelligent NPC extraction.\n\n"
            "Features:\n"
            "- Semantic chunking and embedding\n"
            "- Azure AI-powered NPC extraction\n"
            "- Separate canonical NPC storage\n"
            "- Configurable collection prefixes\n"
            "- Progress tracking and logging\n\n"
            "Version 1.2"
        )


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ImporterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
