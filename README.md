# loc-doc-download
Library of Congress document download

## Overview
This repository contains scripts to automate the downloading and renaming of newspaper pages from the Library of Congress website. The primary functionality includes:

- Downloading newspaper pages in PDF and OCR (ALTO) formats.
- Renaming downloaded files based on the page number.
- Handling technical difficulties during the download process.
- Organizing downloaded files into structured folders based on publication title and date.
- Pulling out text from the OCR files and saving it in a separate text file.

## Scripts
- `download_pages.py`: Contains the main logic for downloading and renaming newspaper pages.
- `transcribe_pages.py`: Extracts text from the OCR files and saves it in a separate text file.

## Usage
1. Ensure you have the necessary dependencies installed. You can create the environment using the `environment.yml` file:
    ```sh
    conda env create -f environment.yml
    conda activate loc-doc-download
    ```

2. Update the URL in the `download_pages.py` script to the first page of the newspaper

2. Run the `download_pages.py` script
    ```sh
    python download_pages.py
    ```

## Output

The `download_pages.py` script will download the newspaper pages in PDF and OCR formats and save them in a `downloads` folder in the current directory. The downloaded files will be organized into structured folders based on the publication title and date. The metadata for each publication will be saved as a JSON file in each publication's folder.

The `transcribe_pages.py` script will extract the text from the OCR files and save it in a separate text file in the same folder as the OCR file.


## Functions
### `download_pages.py`
- `rename_latest_file(latest_file, new_file_name, max_attempts=5, delay=1)`: Renames the downloaded file with multiple attempts.
- `download_and_rename_file(driver, download_folder, file_type, current_page)`: Downloads a file of the specified type and renames it based on the current page number.
- `download_newspaper_pages(url)`: Downloads newspaper pages from a given URL.
- `setup_chrome_options(current_chrome_options, download_folder)`: Sets up Chrome options for downloading files.
- `get_publication_info(driver, xpath, item_description)`: Retrieves the publication information from a web page.
- `sanitize_filename(filename)`: Sanitizes a given filename by replacing any invalid characters with underscores.
- `extract_and_save_metadata(driver, download_folder)`: Extracts metadata from a web page and saves it as a JSON file.
