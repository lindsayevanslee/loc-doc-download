import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException
import os
import json
import glob

def setup_chrome_options(current_chrome_options, download_folder):
    #chrome_options = Options()
    current_chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "safebrowsing.enabled": True
    })
    
    # Force XML files to be downloaded instead of opened in the browser
    current_chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    current_chrome_options.add_argument('--safebrowsing-disable-download-protection')
    current_chrome_options.add_argument('--safebrowsing-disable-extension-blacklist')
    
    return current_chrome_options

def get_publication_info(driver, xpath, item_description):
    try:
        # Wait for the title element to be present
        info_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return info_element.text.strip()
    except Exception as e:
        print(f"Error getting publication {item_description}")
        return f"Unknown_{item_description}"

def sanitize_filename(filename):
    invalid_chars = '<>:"/\\|?*'  # Invalid characters for a filename
    for char in invalid_chars:
        filename = filename.replace(char, '_')  # Replace invalid characters with underscores
    return filename

def extract_and_save_metadata(driver, download_folder):
    try:
        # Find the metadata div
        metadata_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "item-cataloged-data"))
        )
        
        metadata = {}
        h3_elements = metadata_div.find_elements(By.TAG_NAME, "h3")
        
        for h3 in h3_elements:
            title = h3.text.strip()
            ul = h3.find_element(By.XPATH, "following-sibling::ul[1]")
            li_elements = ul.find_elements(By.TAG_NAME, "li")
            
            if len(li_elements) == 1:
                metadata[title] = li_elements[0].text.strip()
            else:
                metadata[title] = [li.text.strip() for li in li_elements]
        
        # Save metadata as JSON
        with open(os.path.join(download_folder, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
        
        print("Metadata saved successfully.")
    except Exception as e:
        print(f"Error extracting metadata")
        


def handle_technical_difficulties(driver, max_retries=3, delay=5):
    """
    Handle the "We're experiencing technical difficulties" error by refreshing the page.
    
    :param driver: The Selenium WebDriver instance
    :param max_retries: Maximum number of refresh attempts
    :param delay: Delay between refresh attempts in seconds
    :return: True if the error is resolved, False otherwise
    """
    for attempt in range(max_retries):
        if "site-error" in driver.page_source:
            print(f"Encountered technical difficulties. Attempt {attempt + 1} of {max_retries} to refresh...")
            driver.refresh()
            time.sleep(delay)
        else:
            return True
    return False


def wait_for_download_complete(directory, file_ext, timeout=60, check_interval=1):
    """Wait for the download to complete by monitoring file size."""
    deadline = time.time() + timeout
    latest_file = None
    last_size = -1

    while time.time() < deadline:
        # Find the latest file of type file_ext in the directory that doesn't start with "page_"
        files = [f for f in glob.glob(os.path.join(directory, f'*.{file_ext}')) if not os.path.basename(f).startswith('page_')]
        if not files:
            time.sleep(check_interval)
            continue
        
        latest_file = max(files, key=os.path.getmtime)
        
        # Check if the file size has stopped changing
        current_size = os.path.getsize(latest_file)
        if current_size == last_size:
            return latest_file  # Download is complete
        
        last_size = current_size
        time.sleep(check_interval)
    
    return None  # Timeout reached

def rename_latest_file(latest_file, new_file_name, max_attempts=5, delay=1):
    """Rename the downloaded file with multiple attempts."""
    if not latest_file:
        print("No file to rename.")
        return False

    for attempt in range(max_attempts):
        try:
            new_file_path = os.path.join(os.path.dirname(latest_file), new_file_name)
            
            # If a file with the new name already exists, delete it
            if os.path.exists(new_file_path):
                os.remove(new_file_path)
            
            os.rename(latest_file, new_file_path)
            print(f"Successfully renamed file to {new_file_name}")
            return True
        except Exception as e:
            print(f"Error renaming file (attempt {attempt + 1}): {str(e)}")
            time.sleep(delay)
    
    print(f"Failed to rename file after {max_attempts} attempts")
    return False



def download_and_rename_file(driver, download_folder, file_type, current_page):
    """file_type = 'PDF' or 'OCR(ALTO)' """

    download_dropdown = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "download"))
    )

    if file_type == "OCR(ALTO)":
        # Find the OCR(ALTO) option and get its value
        ocr_option = download_dropdown.find_element(By.XPATH, f"//option[contains(text(), '{file_type}')]")
        download_url = ocr_option.get_attribute("value")

        response = requests.get(download_url)
        if response.status_code == 200:
            file_path = os.path.join(download_folder, f"page_{current_page}.xml")
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print(f"Successfully downloaded OCR(ALTO) for page {current_page}")
        else:
            print(f"Failed to download OCR(ALTO) for page {current_page}")

    else:
        # For PDF, use the existing method
        download_dropdown.find_element(By.XPATH, f"//option[contains(text(), '{file_type}')]").click()
        download_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, './/div[@class="files input-group-small"]//button[@type="submit"]'))
        )
        download_button.click()

        # Wait for the download to complete and get the file path
        if file_type == "OCR(ALTO)":
            file_extension = "xml" 
        elif file_type == "PDF":
            file_extension = "pdf"

        latest_file = wait_for_download_complete(download_folder, file_extension)
        print(f"Latest file: {latest_file}")
        if latest_file:
            print(f"{file_type} download completed successfully")
            new_file_name = f"page_{current_page}.{file_extension}"
            if rename_latest_file(latest_file, new_file_name):
                print(f"Successfully processed {file_type} for page {current_page}")
            else:
                print(f"Warning: Could not rename {file_type} file for page {current_page}")
        else:
            print(f"{file_type} download timed out or failed")


def download_newspaper_pages(url):
    chrome_options = Options()
    chrome_options.add_argument("--window-size=500,500")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    while True:  # Main loop to cycle through all issues

        # Check for technical difficulties and handle if necessary
        if not handle_technical_difficulties(driver):
            print("Unable to resolve technical difficulties. Skipping to next issue.")
            break

        # Get the publication title and date and sanitize it to use as a folder name
        publication_title = get_publication_info(driver, './/div[@id="part-of"]//ul[@aria-labelledby="item-facet-part-of"]/li[1]/a', "title")
        publication_date = get_publication_info(driver, './/div[@id="facets-box"]//ul[@aria-labelledby="item-facet-dates"]/li/a', "date")
        

        print(f"Downloading pages of {publication_title} - {publication_date}")
        
        folder_name = sanitize_filename(publication_title) + "/" + sanitize_filename(publication_date)
        
        download_folder = os.path.join(os.getcwd(), "downloads", folder_name)
        os.makedirs(download_folder, exist_ok=True)

        # Extract and save metadata
        extract_and_save_metadata(driver, download_folder)

        # Set up Chrome options with the specific download folder
        updated_chrome_options = setup_chrome_options(chrome_options, download_folder)


        driver.quit()
        driver = webdriver.Chrome(options=updated_chrome_options)
        driver.get(url)

        while True:  # Inner loop for pages within an issue
            try:
                # Check for technical difficulties and handle if necessary
                if not handle_technical_difficulties(driver):
                    print("Unable to resolve technical difficulties. Skipping to next issue.")
                    break

                # Wait for the download button to be present
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "download")))

                page_dropdown = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "page"))
                )

                current_page = page_dropdown.find_element(By.CSS_SELECTOR, "option[selected]").get_attribute("value")
                print(f"Processing page {current_page}")

                # Download PDF
                download_and_rename_file(driver, download_folder, "PDF", current_page)

                # Download OCR ALTO
                download_and_rename_file(driver, download_folder, "OCR(ALTO)", current_page)

                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//a[contains(@class, "next")]'))
                )

                if "off" in next_button.get_attribute("class"):
                    print("Reached the last page of the current issue.")
                    break
                next_button.click()

                time.sleep(2)

            except StaleElementReferenceException:
                print("Page reloaded, retrying...")
                continue

            except Exception as e:
                print(f"An error occurred while downloading pages: {str(e)}")
                break

        # After finishing all pages of the current issue, try to move to the next issue
        try:
            # Check for technical difficulties before moving to the next issue
            #if not handle_technical_difficulties(driver):
            #    print("Unable to resolve technical difficulties. Exiting.")
            #    break

            # Look for the "Next issue" button
            next_issue_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//a[contains(@aria-labelledby, "next issue")]'))
            )

            if "off" in next_issue_button.get_attribute("class"):
                    print("Reached the last issue.")
                    break

            next_issue_button.click()
            print("Moving to the next issue...")
            time.sleep(5)  # Wait for the new issue page to load
            url = driver.current_url  # Update the URL for the next iteration

        except Exception as e:
            print(f"An error occurred while moving to the next issue: {str(e)}")
            break

    driver.quit()

# Usage
newspaper_url = "https://www.loc.gov/resource/sn96086912/1882-10-07/ed-1/?sp=1&st=image"
download_newspaper_pages(newspaper_url)
