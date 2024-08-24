import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
import os
import sys
import time

class IXLStatsScraper:
    def __init__(self):
        self.setup_logger()
        self.setup_driver()

    def setup_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def setup_driver(self):
        chrome_options = Options()
        if not hasattr(sys, 'ps1'):
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        if os.environ.get('GITHUB_ACTIONS'):
            # Running in GitHub Actions
            service = Service("chromedriver")
        else:
            # Local development
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())

        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_window_size(1920, 1080)
        self.wait = WebDriverWait(self.driver, 10)
        self.logger.info("WebDriver setup completed")

    def find_element(self, by, value, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            self.logger.error(f"Element not found: {by}={value}")
            self.driver.save_screenshot(f"element_not_found_{value}.png")
            raise

    def click_element(self, by, value, timeout=10):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            ActionChains(self.driver).move_to_element(element).click().perform()
        except TimeoutException:
            self.logger.error(f"Element not clickable: {by}={value}")
            self.driver.save_screenshot(f"element_not_clickable_{value}.png")
            raise

    def login(self, username, password):
        try:
            self.driver.get("https://www.ixl.com/analytics/student-usage#")
            self.find_element(By.ID, "qlusername").send_keys(username)
            self.find_element(By.ID, "qlpassword").send_keys(password)
            self.click_element(By.ID, "qlsubmit")
            self.logger.info("Successfully logged in")

            self.find_element(By.CSS_SELECTOR, "label[data-cy^='subaccount-selection-']")
            parent_subaccount = self.find_element(
                By.XPATH, "//label[contains(@data-cy, 'subaccount-selection-') and .//span[text()='Parent']]"
            )
            parent_subaccount.click()
            self.logger.info("Selected 'Parent' subaccount")

        except Exception as e:
            self.logger.error(f"Login or subaccount selection failed: {str(e)}")
            self.driver.save_screenshot("login_error.png")
            raise

    def select_date_range(self, option="Today"):
        try:
            # Added: Check for presence of date range element
            self.find_element(By.CSS_SELECTOR, ".date-range")
            self.click_element(By.CSS_SELECTOR, ".date-range .option-select.global .select-open")
            self.find_element(By.CSS_SELECTOR, ".date-range .select-body")
            self.click_element(By.XPATH, f"//div[@class='option' and contains(text(), '{option}')]")
            self.wait.until(EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, ".date-range .option-selection"), option
            ))
            self.logger.info(f"Selected date range: {option}")
        except Exception as e:
            self.logger.error(f"Failed to select date range: {str(e)}")
            self.driver.save_screenshot("date_range_error.png")
            raise

    def select_students(self):
        try:
            self.click_element(By.CSS_SELECTOR, ".student-select .option-select.global .select-open")
            self.find_element(By.CSS_SELECTOR, ".student-select .select-body")
            student_options = self.driver.find_elements(By.CSS_SELECTOR, ".option-select.global.default.active .select-dropdown .option")

            for student in student_options:
                student_name = student.get_attribute('data-name')
                self.logger.info(f"Selecting student: {student_name}")
                student.click()
                self.wait.until(EC.text_to_be_present_in_element(
                    (By.CSS_SELECTOR, ".student-select .option-selection"), student_name
                ))
                self.process_student_data(student_name)
                if student != student_options[-1]:
                    self.click_element(By.CSS_SELECTOR, ".student-select .option-select.global .select-open")
                    self.find_element(By.CSS_SELECTOR, ".student-select .select-body")
                    student_options = self.driver.find_elements(By.CSS_SELECTOR, ".option-select.global.default.active .select-dropdown .option")
        except Exception as e:
            self.logger.error(f"Error in selecting students: {str(e)}")
            self.driver.save_screenshot("student_selection_error.png")
            raise

    def process_student_data(self, student_name):
        try:
            time.sleep(1)
            stats_element = self.find_element(By.CSS_SELECTOR, ".summary-stat-container")
            stats_text = ' '.join(stats_element.text.split())
            self.logger.info(f"Stats for {student_name}: {stats_text.lower()}")
        except Exception as e:
            self.logger.error(f"Error processing data for {student_name}: {str(e)}")

    def get_stats(self):
        try:
            username = os.environ.get('IXL_USERNAME')
            password = os.environ.get('IXL_PASSWORD')
            if not username or not password:
                raise ValueError("IXL credentials not set in environment variables")

            self.login(username, password)
            self.select_date_range("Today")
            self.select_students()
        except Exception as e:
            self.logger.error(f"An error occurred during stats collection: {str(e)}")
        finally:
            self.driver.quit()
            self.logger.info("WebDriver closed")

if __name__ == "__main__":
    scraper = IXLStatsScraper()
    scraper.get_stats()