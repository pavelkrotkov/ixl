import time

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from scraper_base import BaseStatsScraper


class IXLSession(BaseStatsScraper):
    def __init__(self, driver):
        super().__init__(driver)
        self.login_url = "https://www.ixl.com/analytics/student-usage#"

    def login(self, username, password):
        try:
            self.driver.get(self.login_url)
            self.find_element(By.ID, "qlusername").send_keys(username)
            self.find_element(By.ID, "qlpassword").send_keys(password)
            self.click_element(By.ID, "qlsubmit")
            self.logger.info("Successfully logged in to IXL")

            self.find_element(By.CSS_SELECTOR, "label[data-cy^='subaccount-selection-']")
            parent_subaccount = self.find_element(
                By.XPATH,
                "//label[contains(@data-cy, 'subaccount-selection-') and .//span[text()='Parent']]",
            )
            parent_subaccount.click()
            self.logger.info("Selected 'Parent' subaccount")
        except Exception as e:
            self.logger.error(f"Login or subaccount selection failed: {e!s}")
            self.driver.save_screenshot("ixl_login_error.png")
            raise

    def select_date_range(self):
        try:
            self.click_element(By.CSS_SELECTOR, ".date-range .option-select.global .select-open")
            self.click_element(By.XPATH, "//div[@class='option' and contains(text(), 'Today')]")
            self.wait.until(
                EC.text_to_be_present_in_element(
                    (By.CSS_SELECTOR, ".date-range .option-selection"), "Today"
                )
            )
            self.logger.info("Selected date range: Today")
        except Exception as e:
            self.logger.error(f"Failed to select date range: {e!s}")
            self.driver.save_screenshot("ixl_date_range_error.png")
            raise

    def get_student_options(self):
        self.click_element(By.CSS_SELECTOR, ".student-select .option-select.global .select-open")
        self.find_element(By.CSS_SELECTOR, ".student-select .select-body")
        return self.driver.find_elements(
            By.CSS_SELECTOR,
            ".option-select.global.default.active .select-dropdown .option",
        )

    def select_student(self, student_name):
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                for student in self.get_student_options():
                    if student.get_attribute("data-name") == student_name:
                        student.click()
                        self.wait.until(
                            EC.text_to_be_present_in_element(
                                (By.CSS_SELECTOR, ".student-select .option-selection"),
                                student_name,
                            )
                        )
                        return True
            except StaleElementReferenceException:
                if attempt < max_attempts - 1:
                    self.logger.warning(
                        f"Stale element encountered when selecting {student_name}. Retrying..."
                    )
                    time.sleep(3)
                else:
                    self.logger.error(
                        f"Failed to select student {student_name} after {max_attempts} attempts."
                    )
                    return False
        return False
