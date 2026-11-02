# Text to Google Search Tabs and PDFs

A small Python desktop tool for analysts who need to run a list of Google searches and keep a record of the results. Load a text file of search terms, open them in batches in Chrome, review each page yourself, then save every loaded results page as a date-stamped PDF with clickable links and selectable text. Designed to keep a person in the loop; see Design history below.

## Features

- Loads search terms from a plain text file, one per line (blank lines are ignored).
- Opens searches in batches (1 to 25 tabs at a time) so you can review as you go.
- Saves each results page as `www_<search term>_Google_Search_<MM-DD-YYYY>.pdf`.
- PDFs are real PDFs: links are clickable and text is selectable.
- Skips tabs showing a Google verification page and tells you how many, so you can resolve them and save again.
- Optionally closes each tab after it is saved, and never saves the same tab twice.
- Remembers your output folder and Chrome location between runs.

## How it works

1. **Open Next Batch** starts Chrome with a remote-debugging port and a separate profile folder, then opens the next group of searches as tabs.
2. **Save Open Tabs to PDF** attaches to that Chrome window with Selenium and, for each Google results tab:
   - takes a snapshot of the page as already loaded (a single-file copy with its styling and images),
   - prints that snapshot to PDF in a second, headless Chrome that has no network access (its proxy points at an address where nothing is listening) and has page scripts disabled.

Because the printing browser cannot reach the network, the PDF is built entirely from the snapshot. Saving has been tested with the network disconnected.

If the snapshot-and-print step fails for a tab, the tool falls back to saving a full-height image of the page (as a PDF, or as a PNG if Pillow is not installed). Images do not have clickable links, and the results message says how many pages were saved each way.

## Requirements

- Python 3
- Google Chrome
- Python packages: `selenium` (4.6 or newer) and `pillow`

```
python -m pip install selenium pillow
```

Selenium 4.6+ finds or downloads a matching ChromeDriver automatically, so no manual driver setup is needed. Pillow is only used for the image fallback.

## Usage

1. Create a text file with one search term per line. Quotes and special characters work, for example:
   ```
   "example company" complaints
   example person name fraud
   ```
2. Run the script:
   ```
   python TextToGoogleSearchTabsPDF.py
   ```
3. Click **Select Text File of Search Terms** and choose your file.
4. Click **Select Output Folder** and choose where the PDFs should go.
5. Check that **Select Chrome** shows the right `chrome.exe` (it is detected automatically in the usual install locations).
6. Set how many tabs to open per batch.
7. Click **1. Open Next Batch**. Let the pages load, review them, and complete any verification prompt Google shows.
8. Click **2. Save Open Tabs to PDF**. Saved tabs are closed (unless you untick the option), so each save covers only the pages you haven't saved yet.
9. Repeat from step 7 until all terms are done.

## Notes and limitations

- Tested on Windows with Chrome. Chrome detection includes common macOS and Linux locations, but those have not been tested.
- The tool uses its own Chrome profile (a `chrome_profile` folder next to the script), so it does not have your logins or extensions.
- Pages are printed in portrait orientation on 11 x 17 in pages, with scripts disabled while printing, so interactive elements (for example expandable sections) may not appear exactly as they did on screen.
- The last open tab is never closed automatically, because closing the final tab would shut Chrome down.
- Very long pages are capped at 16,000 pixels tall in the image fallback.
- The tool does not try to bypass Google's verification prompts. It skips those tabs until you resolve them yourself.

## Troubleshooting

- **The window closes immediately when double-clicked:** double-clicking may use a different Python than your terminal, one without the packages installed. Run it from a terminal (`python TextToGoogleSearchTabsPDF.py`) to see the error, or install the packages for that Python with `py -m pip install selenium pillow`.
- **`No module named 'selenium'`:** run `python -m pip install selenium pillow` with the same Python you use to run the script.
- **"Could not attach to Chrome":** click Open Next Batch first and leave that Chrome window open, then click Save again. If it persists, update Selenium with `python -m pip install --upgrade selenium`.
- **Saved as images instead of PDFs:** the results message includes the reason the PDF printer could not start.

## Files created at runtime

- `settings.json`: your saved output folder and Chrome location.
- `chrome_profile/`: the separate Chrome profile used by the tool.

Neither should be committed to version control.

## About this project

A personal project built to speed up search documentation for investigative work. It was built with help from AI tools (ChatGPT and Claude) for learning Tkinter and Chrome's debugging interface and for reviewing changes, and tested on live batches of searches.

Use it in line with Google's terms of service and your organization's policies.

## Design history: from automated to human-in-the-loop

The first version of this tool drove a headless browser to run the searches and saves fully automatically. Google blocked it on the first request, and the right response to that is not to work around the block. The tool was redesigned so that a person stays in the loop:

- You open the searches in a normal, visible Chrome window, a batch at a time.
- You review the pages and handle any verification prompt yourself.
- Saving afterwards works only on pages that are already loaded. It sends no new requests to Google.

## License

Copyright 2026 Matthew Nichols. Licensed under the Apache License, Version 2.0. See [LICENSE.txt](LICENSE.txt) for details.
