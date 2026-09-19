import logging
from abc import ABC, abstractmethod

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BaseStatsScraper(ABC):
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        self.logger = logging.getLogger(self.__class__.__name__)

    def find_element(self, by, value, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            self.logger.error(f"Element not found: {by}={value}")
            self.driver.save_screenshot(f"element_not_found_{value.replace(' ', '_')}.png")
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

    @abstractmethod
    def login(self, username, password):
        pass

    @abstractmethod
    def process_student_data(self, student_id):
        pass

    @abstractmethod
    def get_stats(self, *args, **kwargs):
        pass
