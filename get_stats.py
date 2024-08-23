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

    def login(self, username, password):
        try:
            self.driver.get("https://www.ixl.com/analytics/student-usage#")
            self.wait.until(EC.presence_of_element_located((By.ID, "qlusername"))).send_keys(username)
            self.wait.until(EC.presence_of_element_located((By.ID, "qlpassword"))).send_keys(password)
            self.wait.until(EC.element_to_be_clickable((By.ID, "qlsubmit"))).click()
            self.logger.info("Successfully logged in")

            # Wait for the subaccount selection to be available
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "label[data-cy^='subaccount-selection-']")))

            # Select the 'Parent' subaccount
            try:
                parent_subaccount = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//label[contains(@data-cy, 'subaccount-selection-') and .//span[text()='Parent']]")
                ))
                parent_subaccount.click()
                self.logger.info("Selected 'Parent' subaccount")
            except (TimeoutException, NoSuchElementException):
                self.logger.error("Failed to find or click 'Parent' subaccount")
                raise

            # Wait for the page to load after selecting the subaccount
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".date-range")))

        except Exception as e:
            self.logger.error(f"Login or subaccount selection failed: {str(e)}")
            self.driver.save_screenshot("login_error.png")
            raise

    def select_date_range(self, option="Today"):
        try:
            date_dropdown = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".date-range .option-select.global"))
            )
            dropdown_opener = date_dropdown.find_element(By.CSS_SELECTOR, ".select-open")
            ActionChains(self.driver).move_to_element(dropdown_opener).click().perform()

            self.wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".date-range .select-body"))
            )

            date_option = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//div[@class='option' and contains(text(), '{option}')]"))
            )
            ActionChains(self.driver).move_to_element(date_option).click().perform()

            self.wait.until(
                EC.text_to_be_present_in_element(
                    (By.CSS_SELECTOR, ".date-range .option-selection"),
                    option
                )
            )
            self.logger.info(f"Selected date range: {option}")
        except Exception as e:
            self.logger.error(f"Failed to select date range: {str(e)}")
            self.driver.save_screenshot("date_range_error.png")
            raise

    def select_students(self):
        try:
            name_dropdown = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".student-select .option-select.global"))
            )
            dropdown_opener = name_dropdown.find_element(By.CSS_SELECTOR, ".select-open")
            ActionChains(self.driver).move_to_element(dropdown_opener).click().perform()

            self.wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".student-select .select-body"))
            )

            student_options = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".option-select.global.default.active .select-dropdown .option"))
            )

            for student in student_options:
                student_name = student.get_attribute('data-name')
                self.logger.info(f"Selecting student: {student_name}")
                ActionChains(self.driver).move_to_element(student).click().perform()

                self.wait.until(
                    EC.text_to_be_present_in_element(
                        (By.CSS_SELECTOR, ".student-select .option-selection"),
                        student_name
                    )
                )

                self.process_student_data(student_name)

                if student != student_options[-1]:
                    name_dropdown = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".student-select .option-select.global"))
                    )
                    dropdown_opener = name_dropdown.find_element(By.CSS_SELECTOR, ".select-open")
                    ActionChains(self.driver).move_to_element(dropdown_opener).click().perform()

                    self.wait.until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, ".student-select .select-body"))
                    )

                    student_options = self.wait.until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".option-select.global.default.active .select-dropdown .option"))
                    )

        except Exception as e:
            self.logger.error(f"Error in selecting students: {str(e)}")
            self.driver.save_screenshot("student_selection_error.png")
            raise

    def process_student_data(self, student_name):
        try:
            time.sleep(1)
            
            # Wait for the stats to load
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".summary-stat-container")))
            
            # Extract the stats
            stats_element = self.driver.find_element(By.CSS_SELECTOR, ".summary-stat-container")
            stats_text = stats_element.text
            
            # Clean up the text (remove newlines and extra spaces)
            stats_text = ' '.join(stats_text.split())
            
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