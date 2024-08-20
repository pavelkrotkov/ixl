import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
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

            # Navigate and select options
            self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".field:nth-child(4) .avatar-image"))).click()
            self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".select-title > .option-selection"))).click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div/div/div/div[2]/div/div[2]"))).click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[2]/span"))).click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[2]/div/div[2]"))).click()

            # Extract and log first set of stats
            self.log_stats(logger)

            # Navigate to next set of stats
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div/span[2]"))).click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[2]/div/div[3]"))).click()

            # Extract and log second set of stats
            self.log_stats(logger)

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

if __name__ == "__main__":
    scraper = IXLStatsScraper()
    scraper.get_stats()