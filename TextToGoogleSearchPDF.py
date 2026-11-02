# Copyright 2026 Matthew Nichols
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Opens a list of search terms as Google searches in a regular (visible) Chrome window, a batch at a time,
# so an analyst can review each results page. Then saves every open search tab to a PDF.
#
# How it works:
#   1. "Open Next Batch" launches Chrome with a remote-debugging port and a separate profile folder,
#      and opens the next batch of searches in tabs. You review the pages (and solve anything Google asks of you).
#   2. "Save Open Tabs to PDF" attaches to that same Chrome and saves each page that is ALREADY LOADED.
#      It does not send any new request to Google. Pages are printed to real PDFs (clickable links, selectable text)
#      from a snapshot of the loaded page; if that fails for a tab, a full-height image is saved instead.
#
# Requirements: Python 3, Chrome, and:  python -m pip install selenium pillow
#   (Selenium 4.6+ finds or downloads a matching ChromeDriver automatically.)
#   (Without Pillow the pages are saved as PNG images instead of PDFs.)

import base64
import io
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlparse

from selenium import webdriver

# import GUI library
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

SEARCH_URL = "https://www.google.com/search?q="
DEBUG_PORT = 9222
MAX_CAPTURE_HEIGHT = 16000   # Chrome can't reliably capture images taller than about 16,384 px

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "settings.json")
PROFILE_DIR = os.path.join(SCRIPT_DIR, "chrome_profile")   # separate profile so the debugging port works

date_str = date.today().strftime("%m-%d-%Y")

# Program state
terms = []          # search terms loaded from the text file
next_index = 0      # position of the next term to open
saved_tab_ids = set()   # Chrome tabs already saved, so they are never saved twice
directory = ""      # output folder for the saved files
chrome_path = ""    # path to chrome.exe


############################################################################
# Settings (remember the output folder, Chrome path, and driver path)
def load_settings():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}

def save_settings():
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump({"directory": directory, "chrome_path": chrome_path}, f)
    except OSError:
        pass

def find_chrome():
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return shutil.which("google-chrome") or shutil.which("chromium") or ""


############################################################################
# Helpers
def build_url(term):
    # quote_plus handles spaces, quotes, and special characters (so "exact phrase" searches still work)
    return SEARCH_URL + quote_plus(term)

def clean_filename(text):
    invalid_characters = set(['<', '>', ':', '"', '/', '\\', '|', '?', '*'])
    cleaned = ''.join('_' if char in invalid_characters else char for char in text)
    return cleaned.strip(" .")[:100] or "search"

def update_status(message=None):
    if message:
        status_label.config(text=message)
    elif not terms:
        status_label.config(text="No terms loaded.")
    elif next_index >= len(terms):
        status_label.config(text=f"Opened all {len(terms)} searches.")
    else:
        status_label.config(text=f"Opened {next_index} of {len(terms)}. Next: {terms[next_index]}")
    root.update_idletasks()


############################################################################
# Selection buttons
def select_file():
    global terms, next_index
    chosen = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if not chosen:
        return

    # utf-8-sig also handles files saved from Notepad with a byte-order mark
    with open(chosen, "r", encoding="utf-8-sig") as f:
        # one term per line, dropping blank lines and stray spaces
        loaded = [line.strip() for line in f.read().splitlines() if line.strip()]

    if not loaded:
        messagebox.showwarning("Empty file", "The selected file has no search terms.")
        return

    terms = loaded
    next_index = 0
    selected_file_label.config(text="Selected file: " + chosen)
    update_status()

def select_directory():
    global directory
    chosen = filedialog.askdirectory()
    if chosen:
        directory = chosen
        selected_directory_label.config(text="Output folder: " + directory)
        save_settings()

def select_chrome():
    global chrome_path
    chosen = filedialog.askopenfilename(title="Select chrome.exe", filetypes=[("Chrome", "chrome.exe"), ("All files", "*.*")])
    if chosen:
        chrome_path = chosen
        selected_chrome_label.config(text="Chrome: " + chrome_path)
        save_settings()


############################################################################
# Step 1: open the next batch of searches in Chrome
def open_next_batch():
    global next_index

    if not terms:
        messagebox.showwarning("No terms", "Please select a text file of search terms first.")
        return
    if not (chrome_path and os.path.isfile(chrome_path)):
        messagebox.showwarning("Chrome not found", "Please select chrome.exe.")
        return
    if next_index >= len(terms):
        messagebox.showinfo("Finished", "All searches have been opened. Select a file to start again.")
        return

    try:
        batch = max(1, int(batch_size.get()))
    except ValueError:
        messagebox.showwarning("Batch size", "Batch size must be a whole number.")
        return

    end = min(next_index + batch, len(terms))
    urls = [build_url(term) for term in terms[next_index:end]]

    # If Chrome is already running with this profile, the new URLs open as tabs in that same window.
    subprocess.Popen([
        chrome_path,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
    ] + urls)

    next_index = end
    update_status()


############################################################################
# Step 2: save every open search tab
#
# Preferred method (keeps links clickable): take a snapshot of the already-loaded page from your Chrome window,
# then print that snapshot to a real PDF in a separate headless Chrome. That second browser is deliberately
# cut off from the network (its proxy points nowhere), so it can only print what the snapshot already contains.
# Fallback method: if that fails for a tab, save a full-height image of the page (links not clickable).

MIN_PDF_BYTES = 8000   # a real results page prints to far more than this; tiny output means the print came out blank

def capture_full_page_image(driver):
    # Fallback: capture the loaded page as one full-height image
    driver.execute_cdp_cmd("Page.bringToFront", {})
    time.sleep(0.5)
    metrics = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
    size = metrics.get("cssContentSize") or metrics["contentSize"]
    width = math.ceil(size["width"])
    height = min(math.ceil(size["height"]), MAX_CAPTURE_HEIGHT)
    shot = driver.execute_cdp_cmd("Page.captureScreenshot", {
        "format": "png",
        "fromSurface": True,
        "captureBeyondViewport": True,
        "clip": {"x": 0, "y": 0, "width": width, "height": height, "scale": 1},
    })
    return base64.b64decode(shot["data"])

def write_image_capture(png_bytes, base_path):
    # Returns the path actually written
    if HAVE_PIL:
        pdf_path = base_path + ".pdf"
        Image.open(io.BytesIO(png_bytes)).convert("RGB").save(pdf_path, "PDF", resolution=96.0)
        return pdf_path
    png_path = base_path + ".png"
    with open(png_path, "wb") as f:
        f.write(png_bytes)
    return png_path

def make_print_driver(work_dir):
    # A separate headless Chrome used only for printing snapshots to PDF
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1600,1000")
    options.add_argument("--proxy-server=http://127.0.0.1:9")   # nothing listens here, so this browser cannot reach Google or anything else
    options.add_argument(f"--user-data-dir={os.path.join(work_dir, 'print_profile')}")
    return webdriver.Chrome(options=options)   # Selenium Manager finds/downloads a matching driver

def snapshot_to_pdf_bytes(print_driver, mhtml_text, work_dir):
    # Save the snapshot (a single-file copy of the loaded page) and print it to PDF
    mhtml_path = os.path.join(work_dir, "snapshot.mhtml")
    with open(mhtml_path, "w", encoding="utf-8", newline="") as f:
        f.write(mhtml_text)

    print_driver.execute_cdp_cmd("Emulation.setScriptExecutionDisabled", {"value": True})   # print the page as captured, don't re-run its scripts
    print_driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {"media": "screen"})         # lay out like the screen view, not the print view
    print_driver.get(Path(mhtml_path).as_uri())
    time.sleep(1.5)

    result = print_driver.execute_cdp_cmd("Page.printToPDF", {
        "printBackground": True,
        "landscape": False,
        "preferCSSPageSize": False,
        "paperWidth": 11.0,     # wide pages so Google lays out its desktop view
        "paperHeight": 17.0,    # tall pages so results are split across fewer pages
        "marginTop": 0.3,
        "marginBottom": 0.3,
        "marginLeft": 0.3,
        "marginRight": 0.3,
    })
    return base64.b64decode(result["data"])

def close_tab_if_possible(driver):
    # Close the current (already saved) tab, but never the last one: closing the last tab would shut Chrome down
    try:
        if close_after_save.get() and len(driver.window_handles) > 1:
            driver.close()
    except Exception:
        pass

def save_open_tabs():
    if not directory:
        messagebox.showwarning("No output folder", "Please select an output folder first.")
        return

    # Attach to the Chrome window that "Open Next Batch" started
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
    try:
        driver = webdriver.Chrome(options=options)   # Selenium Manager finds/downloads a matching driver
    except Exception as error:
        messagebox.showerror(
            "Could not attach to Chrome",
            "Open a batch first and leave that Chrome window open, then try again.\n\n"
            "If this keeps happening, update Selenium (python -m pip install --upgrade selenium) and try again.\n\n"
            + str(error)[:400]
        )
        return

    work_dir = tempfile.mkdtemp(prefix="search_snapshots_")
    print_driver = None
    print_driver_error = ""
    try:
        update_status("Starting PDF printer...")
        print_driver = make_print_driver(work_dir)
    except Exception as error:
        print_driver_error = str(error)[:300]

    saved_with_links, saved_as_images, blocked, other_errors = [], [], 0, []
    try:
        for handle in list(driver.window_handles):
            if handle in saved_tab_ids:
                continue      # saved in an earlier run (only possible for a tab that was kept open)
            driver.switch_to.window(handle)
            parsed = urlparse(driver.current_url)

            # Only handle Google search result tabs
            if parsed.netloc not in ("www.google.com", "google.com"):
                continue
            if parsed.path.startswith("/sorry"):
                blocked += 1      # Google is asking for a captcha: leave this tab for you to handle
                continue
            if parsed.path != "/search":
                continue

            term = parse_qs(parsed.query).get("q", ["search"])[0]
            base_path = os.path.join(directory, f"www_{clean_filename(term)}_Google_Search_{date_str}")
            update_status(f"Saving: {term}")

            # Preferred: real PDF from a snapshot, with clickable links
            if print_driver:
                try:
                    driver.execute_cdp_cmd("Page.bringToFront", {})
                    mhtml_text = driver.execute_cdp_cmd("Page.captureSnapshot", {"format": "mhtml"})["data"]
                    pdf_bytes = snapshot_to_pdf_bytes(print_driver, mhtml_text, work_dir)
                    if len(pdf_bytes) >= MIN_PDF_BYTES:
                        with open(base_path + ".pdf", "wb") as f:
                            f.write(pdf_bytes)
                        saved_with_links.append(term)
                        saved_tab_ids.add(handle)
                        close_tab_if_possible(driver)
                        continue
                except Exception:
                    pass   # fall through to the image fallback below

            # Fallback: full-height image (links not clickable)
            try:
                write_image_capture(capture_full_page_image(driver), base_path)
                saved_as_images.append(term)
                saved_tab_ids.add(handle)
                close_tab_if_possible(driver)
            except Exception as error:
                other_errors.append(f"{term}: {str(error)[:150]}")
    finally:
        # Stop ChromeDriver but leave Chrome itself open (quit() could close the browser we attached to)
        try:
            driver.service.stop()
        except Exception:
            pass
        if print_driver:
            try:
                print_driver.quit()
            except Exception:
                pass
        shutil.rmtree(work_dir, ignore_errors=True)

    update_status()
    total = len(saved_with_links) + len(saved_as_images)
    summary = f"Saved {total} page(s) to:\n{directory}"
    summary += f"\n\nWith clickable links: {len(saved_with_links)}"
    if saved_as_images:
        summary += f"\nSaved as images (links NOT clickable): {len(saved_as_images)}"
        if print_driver_error:
            summary += f"\n(The PDF printer could not start: {print_driver_error})"
        if not HAVE_PIL:
            summary += "\n(Pillow is not installed, so image fallbacks are PNG files. Run: python -m pip install pillow)"
    if blocked:
        summary += f"\n\n{blocked} tab(s) showing a Google verification page were skipped. Resolve them in Chrome, then save again."
    if other_errors:
        summary += "\n\nProblems:\n" + "\n".join(other_errors[:5])
    if total == 0 and not blocked and not other_errors:
        summary = "No Google search tabs were found. Open a batch first, then wait for the pages to finish loading."
    messagebox.showinfo("Save complete", summary)


############################################################################
#Create User Interface
root = tk.Tk()
root.title("Text to Google Search Tabs and PDFs")
root.geometry('560x500')

master_frame = tk.Frame(root)
master_frame.pack(padx=10, pady=10)

def make_row(button_text, command):
    frame = tk.Frame(master_frame)
    frame.pack(pady=6, anchor="w")
    tk.Button(frame, text=button_text, command=command, width=30).pack(side=tk.LEFT)
    label = tk.Label(frame, text="", wraplength=260, justify=tk.LEFT)
    label.pack(side=tk.LEFT, padx=10)
    return label

selected_file_label = make_row("Select Text File of Search Terms", select_file)
selected_directory_label = make_row("Select Output Folder", select_directory)
selected_chrome_label = make_row("Select Chrome (chrome.exe)", select_chrome)

#Batch size frame
batch_frame = tk.Frame(master_frame)
batch_frame.pack(pady=10)
tk.Label(batch_frame, text="Tabs to open per batch:").pack(side=tk.LEFT)
batch_size = tk.Spinbox(batch_frame, from_=1, to=25, width=4)
batch_size.delete(0, tk.END)
batch_size.insert(0, "10")
batch_size.pack(side=tk.LEFT, padx=10)

#Close-after-save option
close_after_save = tk.BooleanVar(value=True)
tk.Checkbutton(master_frame, text="Close each tab after it is saved", variable=close_after_save).pack(pady=4)

#Action buttons
tk.Button(master_frame, text="1. Open Next Batch", command=open_next_batch, width=30).pack(pady=8)
tk.Button(master_frame, text="2. Save Open Tabs to PDF", command=save_open_tabs, width=30).pack(pady=8)

#Status
status_label = tk.Label(master_frame, text="No terms loaded.", wraplength=500, justify=tk.LEFT)
status_label.pack(pady=15)
#End of Create User Interface
############################################################################

#Restore previously saved selections, if the paths still exist
settings = load_settings()
if os.path.isdir(settings.get("directory", "")):
    directory = settings["directory"]
    selected_directory_label.config(text="Output folder: " + directory)
if os.path.isfile(settings.get("chrome_path", "")):
    chrome_path = settings["chrome_path"]
else:
    chrome_path = find_chrome()
if chrome_path:
    selected_chrome_label.config(text="Chrome: " + chrome_path)

root.mainloop()
