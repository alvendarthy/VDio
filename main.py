import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
import os
import subprocess
import threading
import shutil
import re
import sys
import json

# --- 1. Import pywinstyles for Frosted Glass ---
try:
    import pywinstyles
    HAS_PYWINSTYLES = True
except ImportError:
    HAS_PYWINSTYLES = False
    print("Tip: Run 'pip install pywinstyles' for the frosted glass effect.")

class DownloadApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- App Title & Icon ---
        self.title("VDio")
        
        if os.path.exists("vdio.icon"):
            try:
                self.iconbitmap("vdio.icon")
            except Exception as e:
                print(f"Warning: Could not load icon. {e}")
        
        # Window Configuration
        self.geometry("600x500")
        self.resizable(False, False)
        
        # Color Constants
        self.bg_color = "#343647"
        self.border_color = "#9DA1B6"
        self.text_color = "#FFFFFF"
        self.console_color = "#2b2d3b"
        self.dot_red = "#ED6A5E"
        self.dot_yellow = "#F5BF4F"
        self.dot_green = "#61C554"

        self.configure(fg_color=self.bg_color)
        
        # --- 2. Apply Frosted Glass Effect ---
        if HAS_PYWINSTYLES:
            try:
                pywinstyles.apply_style(self, "acrylic")
                self.wm_attributes("-alpha", 0.99) 
            except Exception:
                self.wm_attributes("-alpha", 0.90)
        else:
            self.wm_attributes("-alpha", 0.90)

        # Grid Layout
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=0)
        self.grid_rowconfigure(5, weight=0)

        # --- Window Controls ---
        self.dots_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dots_frame.grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(20, 20))

        def create_dot(parent, color):
            canvas = ctk.CTkCanvas(parent, width=14, height=14, bg=self.bg_color, highlightthickness=0)
            canvas.configure(bg=self.bg_color) 
            canvas.create_oval(1, 1, 13, 13, fill=color, outline="")
            canvas.pack(side="left", padx=3)

        create_dot(self.dots_frame, self.dot_red)
        create_dot(self.dots_frame, self.dot_yellow)
        create_dot(self.dots_frame, self.dot_green)

        # --- URL Input ---
        self.url_label = ctk.CTkLabel(self, text="Url:", font=("Arial", 14), text_color=self.text_color)
        self.url_label.grid(row=1, column=0, padx=(40, 10), pady=10, sticky="e")

        self.url_entry = ctk.CTkEntry(
            self, placeholder_text="https://...", fg_color="#2b2d3b", 
            border_color=self.border_color, border_width=1, text_color=self.text_color,
            height=35, corner_radius=4
        )
        self.url_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.past_btn = ctk.CTkButton(
            self, text="Past", font=("Arial", 14), fg_color="transparent",
            border_color=self.border_color, border_width=1, text_color=self.text_color,
            hover_color="#4A4D61", width=60, height=35, corner_radius=6,
            command=self.paste_from_clipboard
        )
        self.past_btn.grid(row=1, column=2, padx=(0, 40), pady=10)

        # --- Save Input ---
        self.save_label = ctk.CTkLabel(self, text="Save:", font=("Arial", 14), text_color=self.text_color)
        self.save_label.grid(row=2, column=0, padx=(40, 10), pady=10, sticky="e")

        self.save_entry = ctk.CTkEntry(
            self, fg_color="#2b2d3b", border_color=self.border_color,
            border_width=1, text_color=self.text_color, height=35, corner_radius=4
        )
        self.save_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        # Bind Double Click to Open Directory
        self.save_entry.bind("<Double-Button-1>", self.open_save_directory)

        # Default path
        default_path = str(Path.home() / "Downloads")
        self.save_entry.insert(0, default_path)

        self.folder_btn = ctk.CTkButton(
            self, text="📁", font=("Arial", 20), fg_color="transparent",
            border_color=self.border_color, border_width=1, text_color="#E0E0E0",
            hover_color="#4A4D61", width=50, height=35, corner_radius=6,
            command=self.browse_directory
        )
        self.folder_btn.grid(row=2, column=2, padx=(0, 40), pady=10)

        # --- Output Log ---
        self.log_box = ctk.CTkTextbox(
            self, fg_color=self.console_color, text_color="#00FF00",
            font=("Consolas", 12), activate_scrollbars=True
        )
        self.log_box.grid(row=3, column=0, columnspan=3, padx=40, pady=10, sticky="nsew")
        self.log_box.insert("0.0", "Ready.\n")
        self.log_box.configure(state="disabled")

        # --- Download Button ---
        self.download_btn = ctk.CTkButton(
            self, text="Download", font=("Arial", 15), fg_color="transparent",
            border_color=self.border_color, border_width=1, text_color=self.text_color,
            hover_color="#4A4D61", height=45, corner_radius=8,
            command=self.start_download_thread
        )
        self.download_btn.grid(row=4, column=0, columnspan=3, sticky="ew", padx=80, pady=(10, 30))

        # --- Load Config at Startup ---
        self.load_config()

    # --- Config Methods ---
    def get_config_path(self):
        return Path(__file__).parent / "config.json"

    def load_config(self):
        try:
            config_file = self.get_config_path()
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    saved_path = data.get("save_path", "")
                    if saved_path and os.path.isdir(saved_path):
                        self.save_entry.delete(0, "end")
                        self.save_entry.insert(0, saved_path)
                        self.log(f"Config: Restored save path.")
        except Exception as e:
            print(f"Config Load Error: {e}")

    def save_config(self):
        try:
            current_path = self.save_entry.get().strip()
            if current_path and os.path.isdir(current_path):
                config_file = self.get_config_path()
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump({"save_path": current_path}, f, indent=4)
        except Exception as e:
            self.log(f"Config Save Error: {e}")

    # --- Directory Open Function ---
    def open_save_directory(self, event=None):
        path = self.save_entry.get().strip()
        if os.path.isdir(path):
            try:
                if os.name == 'nt':
                    os.startfile(path)
                elif sys.platform == 'darwin':
                    subprocess.call(['open', path])
                else:
                    subprocess.call(['xdg-open', path])
                self.log(f"Opened directory: {path}")
            except Exception as e:
                self.log(f"Error opening directory: {e}")
        else:
            self.log(f"Directory not found: {path}")

    def paste_from_clipboard(self):
        try:
            content = self.clipboard_get().strip()
            url_pattern = re.compile(r'^https?://\S+$', re.IGNORECASE)

            if url_pattern.match(content):
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, content)
                self.log("Paste: Valid URL pasted from clipboard.")
            else:
                self.log("Paste: Clipboard content is NOT a valid URL.")
                messagebox.showwarning("Invalid URL", "Clipboard contents must start with http:// or https://")
                
        except Exception as e:
            self.log(f"Paste Error: Could not read clipboard ({str(e)})")

    def browse_directory(self):
        current_dir = self.save_entry.get()
        if not os.path.isdir(current_dir):
            current_dir = str(Path.home())
        selected = filedialog.askdirectory(initialdir=current_dir)
        if selected:
            self.save_entry.delete(0, "end")
            self.save_entry.insert(0, selected)
            self.save_config()

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def start_download_thread(self):
        url = self.url_entry.get().strip()
        save_dir = self.save_entry.get().strip()

        if not url:
            messagebox.showwarning("Warning", "URL not set")
            return
        
        if shutil.which("yt-dlp") is None:
            messagebox.showerror("Error", "yt-dlp is not installed or not in PATH.")
            return

        self.save_config()

        self.download_btn.configure(state="disabled", text="Checking...")
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

        thread = threading.Thread(target=self.run_download, args=(url, save_dir))
        thread.start()

    def run_download(self, url, root_save_dir):
        # Configuration to hide console window on Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            # --- PHASE 1: Get Video Title ---
            self.log("Fetching video title...")
            
            title_cmd = ["yt-dlp", "--get-title", url, "--no-warnings"]
            
            proc_title = subprocess.run(
                title_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8', 
                errors='replace',
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            video_title = None
            if proc_title.returncode == 0:
                video_title = proc_title.stdout.strip()
                self.log(f"Title: {video_title}")
            else:
                self.log(f"Warning: Could not fetch title. {proc_title.stderr.strip()}")
                # Fallback: if we can't get title, we cannot make a named folder.
                # proceed to standard download in root dir? Or abort?
                # Let's abort to be safe, or just use a fallback folder name.
                self.log("Aborting: Cannot verify title for folder creation.")
                return

            # --- PHASE 2: Create Subdirectory & Check Existing ---
            
            # Sanitize title for valid folder name (replace illegal chars with _)
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', video_title)
            
            # This is the dedicated directory for this video
            video_save_dir = os.path.join(root_save_dir, safe_title)

            # Ensure the directory exists
            if not os.path.exists(video_save_dir):
                try:
                    os.makedirs(video_save_dir, exist_ok=True)
                    self.log(f"Created directory: {safe_title}")
                except Exception as e:
                    self.log(f"Error creating directory: {e}")
                    return
            else:
                self.log(f"Directory exists: {safe_title}")

            # Now we check inside 'video_save_dir' for duplicates
            # Regex logic: Match files starting with the title inside that folder
            pattern_str = r"^" + re.escape(video_title) + r"\..+$"
            regex_pattern = re.compile(pattern_str)

            found_files = []
            try:
                for filename in os.listdir(video_save_dir):
                    if regex_pattern.match(filename):
                        found_files.append(filename)
            except Exception as e:
                self.log(f"Error scanning directory: {e}")

            if found_files:
                msg_txt = f"Found {len(found_files)} existing file(s) in '{safe_title}':\n"
                for f in found_files[:3]:
                    msg_txt += f"• {f}\n"
                if len(found_files) > 3:
                    msg_txt += f"...and {len(found_files)-3} others."
                
                msg_txt += "\n\nDo you want to DELETE these files and download again?"
                
                self.log(f"Conflict: {len(found_files)} existing file(s) found.")
                
                user_resp = messagebox.askyesno("File Exists", msg_txt)
                
                if not user_resp:
                    self.log("Download Cancelled by user.")
                    return
                else:
                    self.log("Removing existing files...")
                    for f in found_files:
                        try:
                            full_path = os.path.join(video_save_dir, f)
                            os.remove(full_path)
                            self.log(f"Deleted: {f}")
                        except Exception as e:
                            self.log(f"Error deleting {f}: {e}")

            # --- PHASE 3: Download ---
            self.download_btn.configure(text="Downloading...")
            
            # Update output template to point to the NEW video_save_dir
            output_template = f"{video_save_dir}/%(title)s.%(ext)s"
            command = ["yt-dlp", url, "-o", output_template]
            
            self.log(f"Starting Download...")

            process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            for line in process.stdout:
                self.log(line.strip())

            process.wait()
            return_code = process.returncode

            if return_code != 0:
                self.after(0, lambda: messagebox.showerror("Error", f"Download failed with code {return_code}"))
                self.log(f"Error: Process finished with code {return_code}")
            else:
                self.log("Download Completed Successfully!")

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.log(f"Exception: {str(e)}")
        
        finally:
            self.after(0, lambda: self.download_btn.configure(state="normal", text="Download"))

if __name__ == "__main__":
    app = DownloadApp()
    app.mainloop()