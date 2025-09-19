import os
import time
from flask import Flask, render_template_string
from threading import Thread
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import json

# Configuration
WEBSITE_URL = "https://defender.iai-shop.com/panel/cms-files.php"
CHROME_DRIVER_PATH = r""
USERNAME = ""
PASSWORD = ""


def wait_for_upload_complete(driver, timeout=120):
    """Wait for all uploads to complete"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        uploads = driver.find_elements(By.CSS_SELECTOR, "div.upload-progress, div.upload-status")
        if not uploads:
            return True
        time.sleep(2)
    return False


def process_product(driver, product_id, filename):
    # Go to product page
    product_url = f"https://defender.iai-shop.com/panel/product.php?idt={product_id}#descriptions"
    driver.get(product_url)
    time.sleep(2)

    try:
        # Add parameter
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a#parameter.nohref.addEl"))
        ).click()

        # Fill parameter form
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "fg_inline_parameter"))
        ).send_keys("Prezentacja 3")
        time.sleep(2)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "fg_inline_parameter"))
        ).send_keys(Keys.ENTER)
        driver.find_element(By.ID, "fg_inline_value1").send_keys("tak")
        time.sleep(2)
        driver.find_element(By.ID, "fg_inline_value1").send_keys(Keys.ENTER)
        driver.find_element(By.CSS_SELECTOR, "input[value='Dodaj']").click()
        time.sleep(1)

        # Click Prezentacja 360
        driver.find_element(By.CSS_SELECTOR, "div#showMenu_1339430129.nohref.showMenu").click()
        time.sleep(1)

        # Click additional options
        driver.find_element(By.CSS_SELECTOR, "a#editDistinction_1339430129.nohref.editDistinction").click()
        time.sleep(2)

        # Select radio buttons
        radio1 = driver.find_element(By.ID, "jsfg_distinction_1")
        driver.execute_script("arguments[0].click();", radio1)
        time.sleep(1)
        radio2 = driver.find_element(By.ID, "jsfg_projector_hide_1")
        driver.execute_script("arguments[0].click();", radio2)

        # Save changes
        driver.find_element(By.CSS_SELECTOR, "input[value='Zapisz']").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "input[value='Zapisz zmiany']").click()
        time.sleep(2)

        # Go to visibility page
        check_url = f"https://moto-tour.com.pl/projector.php?product={product_id}"
        driver.get(check_url)
        time.sleep(10)

    except Exception as e:
        print(f"Error processing product {product_id}: {str(e)}")
        driver.save_screenshot(f"error_{product_id}.png")
        return None


def upload_files(folder_path, product_id):
    print(f"\nProcessing folder: {folder_path}")
    print(f"Using product ID: {product_id}")

    try:
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        service = Service(CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(5)

        print("Opening website...")
        driver.get(WEBSITE_URL)

        print("Entering username...")
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input#panel_login.form__input"))
        )
        username_field.clear()
        username_field.send_keys(USERNAME)

        print("Entering password...")
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input#panel_password.form__input"))
        )
        password_field.clear()
        password_field.send_keys(PASSWORD)

        print("Submitting form...")
        password_field.send_keys(Keys.RETURN)
        time.sleep(2)
        driver.get(WEBSITE_URL)

        WebDriverWait(driver, 160).until(
            EC.visibility_of_element_located((By.ID, "name_span_1_302"))
        )
        print("Login successful. Starting upload process...")
        time.sleep(3)

        print("Navigating to skaner-3d...")
        driver.execute_script("""
            const span = Array.from(document.querySelectorAll('span'))
                .find(el => el.textContent.trim() === 'skaner-3d');
            if (span) span.click();
        """)
        time.sleep(2)

        try:
            print("Creating directory...")
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[value='Dodaj katalog']"))
            ).click()
            time.sleep(1)

            driver.find_element(By.ID, "fg_dir_name").send_keys(product_id)
            time.sleep(0.5)

            driver.find_element(By.CSS_SELECTOR, "img[onclick*='addDir']").click()
            time.sleep(2)

            print("Opening folder...")
            # Wait for the folder element to be present
            folder_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, f"//span[text()='{product_id}']"))
            )

            # Scroll the element into view with JavaScript
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});",
                                  folder_element)

            # Small pause for the scroll to complete
            time.sleep(1.5)

            # Click the element using JavaScript to avoid interception
            driver.execute_script("arguments[0].click();", folder_element)

            # Wait for any resulting page changes
            time.sleep(2)

            # Look for WEBP files in the folder
            webp_files_path = os.path.join(folder_path, 'WEBP Files')
            if not os.path.exists(webp_files_path):
                print(f"WEBP Files directory not found at: {webp_files_path}")
                # Try to find WEBP files directly in the folder
                webp_files_path = folder_path

            files = [os.path.join(webp_files_path, f) for f in os.listdir(webp_files_path)
                     if os.path.isfile(os.path.join(webp_files_path, f)) and f.lower().endswith('.webp')]

            if files:
                print(f"Uploading {len(files)} files...")
                WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[value='Dodaj pliki']"))
                ).click()
                time.sleep(3)

                file_input = driver.find_element(By.XPATH, "//input[@type='file']")
                file_input.send_keys("\n".join(files))
                time.sleep(45)

                if not wait_for_upload_complete(driver):
                    print("Warning: Upload timeout reached")
                else:
                    print("Upload completed successfully")

                print("Closing upload window...")
                try:
                    close_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.container-close[href='#']"))
                    )
                    close_button.click()
                    time.sleep(1)
                except Exception as e:
                    print(f"Could not find Close button: {str(e)}")
                    driver.save_screenshot(f"close_error_{product_id}.png")

            # Process the product
            if files:
                filename = os.path.splitext(files[0])[0]  # Get filename without extension
                print(f"\nProcessing product: {product_id} (File: {filename})")

                product_link = process_product(driver, product_id, filename)

                if product_link:
                    print(f"Successfully processed: {product_link}")
                else:
                    print(f"Failed to process product {product_id}")

            driver.quit()
            return True

        except Exception as e:
            print(f"Error processing {product_id}: {str(e)}")
            driver.save_screenshot(f"error_{product_id}.png")
            driver.quit()
            return False

    except Exception as e:
        print(f"Error processing {product_id}: {str(e)}")
        return False