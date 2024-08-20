import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import os
import time

class IXLStatsScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.set_window_size(1920, 1080)
        self.wait = WebDriverWait(self.driver, 10)

    def __del__(self):
        if hasattr(self, 'driver'):
            self.driver.quit()

    def get_stats(self):
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        username = os.environ.get('IXL_USERNAME')
        password = os.environ.get('IXL_PASSWORD')
        assert username and password, "Credentials not set in environment variables"

        try:
            # Login
            self.driver.get("https://www.ixl.com/analytics/student-usage#")
            self.wait.until(EC.presence_of_element_located((By.ID, "qlusername"))).send_keys(username)
            self.wait.until(EC.presence_of_element_located((By.ID, "qlpassword"))).send_keys(password)
            self.wait.until(EC.element_to_be_clickable((By.ID, "qlsubmit"))).click()

            # Select parent
            self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".field:nth-child(4) .avatar-image"))).click()
            self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".select-title > .option-selection"))).click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div/div/div/div[2]/div/div[2]"))).click()

            self.select_students()

            # Logout
            self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#user-nav-wrapper > .display-name"))).click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Sign out')]"))).click()

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            if hasattr(self, 'driver'):
                self.driver.save_screenshot("error_screenshot.png")
            raise

    def log_stats(self, logger):
        time.sleep(5)
        name = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".title-start"))).text
        summary = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".summary-stat-container"))).text
        
        # Clean the strings: remove newlines and extra whitespace
        name = ' '.join(name.split())
        summary = ' '.join(summary.split())
        
        logger.info(f"{name} {summary}")

    def select_students(self):
        try:
            # Wait for and locate the specific dropdown
            dropdown = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".option-select.global.default.active"))
            )

            # Open the dropdown
            dropdown_opener = dropdown.find_element(By.CSS_SELECTOR, ".select-title .prompt-query-or-selection-wrapper")
            ActionChains(self.driver).move_to_element(dropdown_opener).click().perform()

            # Get all student options
            student_options = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".option-select.global.default.active .select-dropdown .option"))
            )

            for student in student_options:
                student_name = student.get_attribute('data-name')
                self.logger.info(f"Selecting student: {student_name}")

                # Click the student option
                ActionChains(self.driver).move_to_element(student).click().perform()

                # Wait for page to load after selection
                WebDriverWait(self.driver, 10).until(
                    EC.text_to_be_present_in_element(
                        (By.CSS_SELECTOR, ".option-select.global.default.active .select-title .option-selection"),
                        student_name
                    )
                )

                # Perform actions for this student
                self.process_student_data(student_name)

                # Reopen the dropdown for the next iteration
                if student != student_options[-1]:  # Don't reopen for the last student
                    # Re-locate the dropdown opener as the page might have refreshed
                    dropdown_opener = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".option-select.global.default.active .select-title .prompt-query-or-selection-wrapper"))
                    )
                    ActionChains(self.driver).move_to_element(dropdown_opener).click().perform()

        except TimeoutException:
            self.logger.error("Timeout occurred while trying to interact with the student dropdown")
            self.driver.save_screenshot("dropdown_error.png")
        except StaleElementReferenceException:
            self.logger.error("The page structure changed unexpectedly during student selection")
            self.driver.save_screenshot("stale_element_error.png")
        except Exception as e:
            self.logger.error(f"An error occurred while selecting students: {str(e)}")
            self.driver.save_screenshot("student_selection_error.png")

    def process_student_data(self, student_name):
        # Implement the logic to process data for each student
        self.logger.info(f"Processing data for {student_name}")
        # Add your data processing logic here
        self.log_stats()  

if __name__ == "__main__":
    scraper = IXLStatsScraper()
    scraper.get_stats()