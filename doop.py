# ==============================================================================
# ██████╗░░█████╗░░█████╗░██████╗░  ███████╗██╗███╗░░██╗██████╗░███████╗██████╗░
# ██╔══██╗██╔══██╗██╔══██╗██╔══██╗  ██╔════╝██║████╗░██║██╔══██╗██╔════╝██╔══██╗
# ██║░░██║██║░░██║██║░░██║██████╔╝  █████╗░░██║██╔██╗██║██║░░██║█████╗░░██████╔╝
# ██║░░██║██║░░██║██║░░██║██╔═══╝░  ██╔══╝░░██║██║╚████║██║░░██║██╔══╝░░██╔══██╗
# ██████╔╝╚█████╔╝╚█████╔╝██║░░░░░  ██║░░░░░██║██║░╚███║██████╔╝███████╗██║░░██║
# ╚═════╝░░╚════╝░░╚════╝░╚═╝░░░░░  ╚═╝░░░░░╚═╝╚═╝░░╚══╝╚═════╝░╚══════╝╚═╝░░╚═╝
# 
# DoopFinder
# Version: 1.0
# By @ItsDoodyTime
# https://github.com/ItsDoodyTime/DoopFinder
# ==============================================================================
# 
# Hey There!
# - Every section is labled for easier navigation
# - Some sections have a description and some don't
# 
# I don't know what I'm doing....
# Sorry if the code is bad!
# 
# - Happy Coding! ♥
# ==============================================================================


# =======================
# Imports
# =======================

import os
import sys
import hashlib
import shutil
import subprocess
import threading
import difflib
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
from PIL import Image, ImageTk
import imagehash
import cv2
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

# =======================
# Configuration
# =======================

# Similarity thresholds/scores
VISUAL_THRESHOLD = 0.80
FILENAME_THRESHOLD = 0.80
SIZE_THRESHOLD = 0.95
CONFIDENCE_THRESHOLD = 60
MAX_WORKERS = os.cpu_count()

IMAGE_EXT = {".jpg",".jpeg",".png",".bmp",".webp",".gif",".tiff",".ico"}
VIDEO_EXT = {".mp4",".mov",".mkv",".avi",".webm",".flv",".wmv"}
TEXT_EXT  = {".txt",".md",".json",".xml",".csv",".py",".js",".cpp",".html",".css"}
DOC_EXT   = {".pdf",".doc",".docx",".xls",".xlsx",".ppt",".pptx"}
ARCHIVE_EXT = {".zip",".rar",".7z",".tar",".gz"}
EXEC_EXT = {".exe",".msi",".bat",".sh",".app",".apk"}

# Runtime
cancel_scan = False
total_files = 0
processed_files = 0


# ==========================================================
# Util? backend stuff? idk
# ==========================================================

def log(msg):
    log_box.insert(tk.END, msg + "\n")
    log_box.see(tk.END)
    root.update_idletasks()

def update_progress(value):
    progress_var.set(value)
    root.update_idletasks()

def is_system_root(path):
    path = os.path.abspath(path)
    if os.name == "nt":
        drive = os.path.splitdrive(path)[0] + "\\"
        return path == drive
    else:
        return path == "/"

def get_category(ext):
    if ext in IMAGE_EXT: return "image"
    if ext in VIDEO_EXT: return "video"
    if ext in TEXT_EXT: return "text"
    if ext in DOC_EXT: return "document"
    if ext in ARCHIVE_EXT: return "archive"
    if ext in EXEC_EXT: return "executable"
    return "other"

def sha256(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                if cancel_scan:
                    return None
                h.update(chunk)
        return h.hexdigest()
    except:
        return None

def filename_similarity(a, b):
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()

def size_similarity(a, b):
    return min(a,b) / max(a,b)


# ==========================================================
# FFprobe stuff
# ==========================================================

def get_ffprobe_path():
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, "_internal", "ffprobe.exe")

def get_video_duration(path):
    try:
        result = subprocess.run(
            [get_ffprobe_path(),"-v","error","-show_entries","format=duration",
             "-of","default=noprint_wrappers=1:nokey=1",path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return round(float(result.stdout.strip()),2)
    except:
        return None


# ==========================================================
# Visual Hashing (Images & Videos)
# ==========================================================

def get_image_hash(path):
    try:
        img = Image.open(path).convert("RGB")
        return imagehash.phash(img)
    except:
        return None

def get_video_hash(path):
    try:
        cap = cv2.VideoCapture(path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, total//2)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        return imagehash.phash(img)
    except:
        return None

def hash_similarity(h1, h2):
    return 1 - (h1 - h2) / len(h1.hash.flatten())

# ==========================================================
# Metadata Extraction (Multi-threaded)
# ==========================================================

def extract_metadata(path):
    global processed_files
    if cancel_scan:
        return None

    ext = os.path.splitext(path)[1].lower()
    category = get_category(ext)

    data = {
        "path": path,
        "name": os.path.basename(path),
        "size": os.path.getsize(path),
        "ext": ext,
        "category": category,
        "sha": sha256(path),
        "hash": None,
        "duration": None
    }

    if category == "image":
        data["hash"] = get_image_hash(path)
    elif category == "video":
        data["hash"] = get_video_hash(path)
        data["duration"] = get_video_duration(path)

    processed_files += 1
    update_progress((processed_files/total_files)*100)

    return data

# ==========================================================
# Scaning operation
# ==========================================================

def cancel_operation():
    global cancel_scan
    cancel_scan = True
    log("\nScan cancelled by user.")

def scan_directory():

    global cancel_scan, total_files, processed_files
    cancel_scan = False
    processed_files = 0

    directory = path_entry.get()

    if not os.path.isdir(directory):
        messagebox.showerror("Error", "Invalid directory.")
        return

    if is_system_root(directory):
        messagebox.showerror("Safety Lock",
                             "Scanning system root is blocked for safety.")
        return

    move_enabled = move_var.get()

    log("Starting scan...\n")

    files = []
    for root_dir, _, filenames in os.walk(directory):
        for f in filenames:
            full = os.path.join(root_dir, f)
            if "Duplicates" in full or "Duplicate_Logs" in full:
                continue
            files.append(full)

    total_files = len(files)
    log(f"Files found: {total_files}")
    log("Extracting metadata...\n")

    data = []

    with ThreadPoolExecutor(MAX_WORKERS) as executor:
        futures = {executor.submit(extract_metadata, f): f for f in files}
        for future in as_completed(futures):
            if cancel_scan:
                return
            result = future.result()
            if result:
                data.append(result)

    log("Metadata extraction complete.\n")


# ======================================================
# Smart Size Bucketing Optimization
# ======================================================

    buckets = defaultdict(list)
    for item in data:
        bucket_key = round(item["size"] / 1000000)
        buckets[bucket_key].append(item)

    duplicates = []

    for bucket in buckets.values():
        for i in range(len(bucket)):
            for j in range(i+1, len(bucket)):
                if cancel_scan:
                    return

                a = bucket[i]
                b = bucket[j]
                confidence = 0
                reasons = []

                if a["sha"] and b["sha"] and a["sha"] == b["sha"]:
                    confidence += 40
                    reasons.append("Exact content match")

                if filename_similarity(a["name"], b["name"]) >= FILENAME_THRESHOLD:
                    confidence += 15
                    reasons.append("Similar filename")

                if size_similarity(a["size"], b["size"]) >= SIZE_THRESHOLD:
                    confidence += 10
                    reasons.append("Similar size")

                if a["hash"] and b["hash"]:
                    if hash_similarity(a["hash"], b["hash"]) >= VISUAL_THRESHOLD:
                        confidence += 40
                        reasons.append("Visual similarity")

                if a["duration"] and b["duration"]:
                    if abs(a["duration"] - b["duration"]) < 0.1:
                        confidence += 15
                        reasons.append("Same duration")

                if a["category"] == b["category"]:
                    confidence += 10
                    reasons.append("Same category")

                if confidence >= CONFIDENCE_THRESHOLD:
                    duplicates.append((a["path"], b["path"], confidence, reasons))
                    log(f"Duplicate ({confidence}%): {a['name']} <--> {b['name']}")


# ======================================================
# Results
# ======================================================

    if not duplicates:
        log("\nNo duplicates found.")
        log("Scan complete.")
        return

    if move_enabled:
        dup_folder = os.path.join(directory, "Duplicates")
        os.makedirs(dup_folder, exist_ok=True)

        moved = set()
        for _, b, _, _ in duplicates:
            if b not in moved:
                try:
                    shutil.move(b,
                                os.path.join(dup_folder,
                                os.path.basename(b)))
                    moved.add(b)
                except:
                    pass
        log("\nDuplicates moved to folder.")

    log_dir = os.path.join(directory, "Duplicate_Logs")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"log_{timestamp}.txt")

    with open(log_path, "w", encoding="utf-8") as f:
        for a,b,c,r in duplicates:
            f.write(f"{a} <--> {b} | {c}% | {', '.join(r)}\n")

    log(f"\nLog saved: {log_path}")
    log("Scan complete.")


# ==========================================================
# UI Stuff
# ==========================================================

# Too lazy to move these but this is unrelated to the UI, and it's just for the duplicate folder
def start_scan():
    threading.Thread(target=scan_directory).start()

def browse_folder():
    folder = filedialog.askdirectory()
    path_entry.delete(0, tk.END)
    path_entry.insert(0, folder)

# ----------------------------------------

root = tk.Tk()
root.title("DoopFinder")
root.geometry("850x650")
root.configure(bg="#1e1e1e")

# App Icon
icon_path = os.path.join("_internal", "assets","icon.ico")
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)

# Logo
logo_path = os.path.join("_internal", "assets","logo.png")
if os.path.exists(logo_path):
    img = Image.open(logo_path)
    img = img.resize((120,120))
    logo_img = ImageTk.PhotoImage(img)
    tk.Label(root, image=logo_img, bg="#1e1e1e").pack(pady=10)

tk.Label(root,
         text="DoopFinder",
         font=("Segoe UI",20,"bold"),
         bg="#1e1e1e",
         fg="white").pack()

tk.Label(root,
         text="Directory:",
         bg="#1e1e1e",
         fg="white").pack(pady=5)

path_entry = tk.Entry(root,
                      width=80,
                      bg="#2b2b2b",
                      fg="white",
                      insertbackground="white")
path_entry.pack()

tk.Button(root,
          text="Browse",
          command=browse_folder,
          bg="#333",
          fg="white").pack(pady=5)

move_var = tk.BooleanVar()
tk.Checkbutton(root,
               text="Move to 'Duplicates' folder",
               variable=move_var,
               bg="#1e1e1e",
               fg="white",
               selectcolor="#1e1e1e").pack(pady=5)

tk.Button(root,
          text="Start Scan",
          command=start_scan,
          bg="#444",
          fg="white",
          height=2).pack(pady=5)

tk.Button(root,
          text="Cancel Scan",
          command=cancel_operation,
          bg="#550000",
          fg="white").pack(pady=5)

progress_var = tk.DoubleVar()
progress = ttk.Progressbar(root,
                           variable=progress_var,
                           maximum=100)
progress.pack(fill="x", padx=20, pady=10)

log_box = scrolledtext.ScrolledText(root,
                                    bg="#111",
                                    fg="#00ff88",
                                    insertbackground="white")
log_box.pack(fill="both", expand=True,
             padx=10, pady=10)

root.mainloop()

