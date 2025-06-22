import os
import re
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

class ModRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mod Folder Renamer")
        self.root.geometry("600x400")
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Directory selection
        dir_frame = tk.Frame(self.root)
        dir_frame.pack(pady=10, padx=10, fill=tk.X)
        
        tk.Label(dir_frame, text="Directory:").pack(side=tk.LEFT)
        self.dir_var = tk.StringVar()
        tk.Entry(dir_frame, textvariable=self.dir_var, state='readonly', width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(dir_frame, text="Browse", command=self.select_directory).pack(side=tk.LEFT)
        
        # Start button
        tk.Button(self.root, text="Rename Mod Folders", command=self.start_renaming, 
                  bg="#4CAF50", fg="white").pack(pady=10)
        
        # Log area
        tk.Label(self.root, text="Log:").pack(anchor=tk.W, padx=10)
        self.log_area = scrolledtext.ScrolledText(self.root, height=15)
        self.log_area.pack(padx=10, pady=(0, 10), fill=tk.BOTH, expand=True)
        self.log_area.config(state=tk.DISABLED)
    
    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_var.set(directory)
    
    def log_message(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
    
    def clear_log(self):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)
    
    def extract_mod_name(self, file_path):
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Find the <name> tag - try with and without namespace
            name_element = None
            
            # Try without namespace first
            name_element = root.find('name')
            
            # If not found, try with common namespace prefixes
            if name_element is None:
                for prefix in ['', '{http://schemas.microsoft.com/ado/2007/08/dataservices}', 
                               '{http://www.w3.org/2005/Atom}']:
                    name_element = root.find(f'{prefix}name')
                    if name_element is not None:
                        break
            
            if name_element is None:
                self.log_message("  ❌ No <name> element found in XML")
                return None
            
            mod_name = name_element.text
            if not mod_name or mod_name.strip() == "":
                self.log_message("  ❌ <name> element is empty")
                return None
                
            return mod_name.strip()
            
        except ET.ParseError:
            self.log_message("  ❌ Error parsing XML file")
            return None
        except Exception as e:
            self.log_message(f"  ❌ Unexpected error: {str(e)}")
            return None
    
    def start_renaming(self):
        directory = self.dir_var.get()
        if not directory or not os.path.exists(directory):
            messagebox.showerror("Error", "Please select a valid directory")
            return
        
        self.clear_log()
        self.log_message(f"Starting process in: {directory}")
        
        processed = 0
        renamed = 0
        errors = 0
        
        for folder_name in os.listdir(directory):
            folder_path = os.path.join(directory, folder_name)
            if not os.path.isdir(folder_path):
                continue
                
            processed += 1
            self.log_message(f"\nProcessing: {folder_name}")
            
            # Look for metadata.xml file
            metadata_path = os.path.join(folder_path, "metadata.xml")
            if not os.path.exists(metadata_path):
                self.log_message("  ❌ metadata.xml not found")
                errors += 1
                continue
            
            # Extract mod name from metadata
            mod_name = self.extract_mod_name(metadata_path)
            if not mod_name:
                errors += 1
                continue
            
            # Clean and validate new name
            clean_name = re.sub(r'[\\/*?:"<>|]', '', mod_name).strip()
            if not clean_name:
                self.log_message("  ❌ Invalid name after cleaning")
                errors += 1
                continue
            
            # Check if renaming is needed
            new_path = os.path.join(directory, clean_name)
            if folder_path == new_path:
                self.log_message(f"  ✔ Already named correctly: {clean_name}")
                continue
            
            # Check if a folder with the new name already exists
            if os.path.exists(new_path):
                self.log_message(f"  ❌ Destination folder already exists: {clean_name}")
                errors += 1
                continue
            
            # Attempt to rename
            try:
                os.rename(folder_path, new_path)
                self.log_message(f"  ✔ Renamed to: {clean_name}")
                renamed += 1
            except Exception as e:
                self.log_message(f"  ❌ Rename failed: {str(e)}")
                errors += 1
        
        # Show summary
        self.log_message("\n" + "="*50)
        self.log_message(f"Process completed!\nProcessed: {processed}\nRenamed: {renamed}\nErrors: {errors}")
        self.log_message("="*50)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModRenamerApp(root)
    root.mainloop()