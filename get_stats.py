import logging
import os
import smtplib
import time
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ixl_parser import process_table_html
from progress import IXLStudentProgress, MathAcademyStudentProgress
from report import build_report

# Set up logging once at the module level
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


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
    def process_student_data(self, student_id: str) -> MathAcademyStudentProgress | None:
        try:
            self.driver.get(self.base_activity_url.format(student_id))
            student_name = self.find_element(By.ID, "studentName").text.strip()

            daily_xp_text = self.find_element(By.ID, "dailyGoalPoints").text.strip()
            daily_xp_earned, daily_xp_goal = (
                daily_xp_text.split("/")[0],
                daily_xp_text.split("/")[1].split()[0],
            )
            weekly_xp = self.find_element(By.ID, "thisWeekTotalXP").text.split()[0]
            activity_html = self.find_element(By.ID, "tasksFrame").get_attribute("outerHTML")

            self.logger.info(
                f"Processed Math Academy data for student: {student_name} (ID: {student_id})"
            )
            return MathAcademyStudentProgress(
                student_id,
                student_name,
                daily_xp_earned,
                daily_xp_goal,
                weekly_xp,
                activity_html,
            )
        except Exception as e:
            self.logger.error(
                f"Error processing Math Academy data for student ID {student_id}: {e!s}"
            )
            self.driver.save_screenshot(f"math_academy_student_{student_id}_error.png")
            return None

    def get_stats(
        self, username: str, password: str, student_ids: list[str]
    ) -> list[MathAcademyStudentProgress]:
        data = []
        try:
            self.login(username, password)
            for student_id in student_ids:
                if student_data := self.process_student_data(student_id):
                    data.append(student_data)
        except Exception as e:
            self.logger.error(f"An error occurred during Math Academy stats collection: {e!s}")
        return data


def setup_driver():
    chrome_options = Options()
    headless_mode = os.environ.get("HEADLESS", "true").lower() == "true"
    if headless_mode:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    if os.environ.get("GITHUB_ACTIONS"):
        driver = webdriver.Chrome(options=chrome_options)
    else:
        from webdriver_manager.chrome import ChromeDriverManager

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_window_size(1920, 1080)
    return driver


def send_email(
    subject: str,
    html_content: str,
    gmail_user: str,
    gmail_app_password: str,
    recipients: list[str],
) -> None:
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = gmail_user
    message["To"] = ", ".join(recipients)
    message.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_app_password)
            server.sendmail(gmail_user, recipients, message.as_string())
        logging.info(f"Email sent successfully to {', '.join(recipients)}")
    except Exception as e:
        logging.error(f"Failed to send email: {e!s}")


def _require_env(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"{name} not set in environment variables")
    return value


def _require_csv_env(name, empty_message):
    values = [value.strip() for value in _require_env(name).split(",") if value.strip()]
    if not values:
        raise ValueError(empty_message)
    return values


def main():
    logger = logging.getLogger(__name__)

    ixl_username = _require_env("IXL_USERNAME")
    ixl_password = _require_env("IXL_PASSWORD")
    mathacademy_username = _require_env("MATHACADEMY_USERNAME")
    mathacademy_password = _require_env("MATHACADEMY_PASSWORD")
    mathacademy_student_ids = _require_csv_env(
        "MATHACADEMY_STUDENT_IDS", "MATHACADEMY_STUDENT_IDS must contain at least one ID"
    )
    gmail_user = _require_env("GMAIL_USER")
    gmail_app_password = _require_env("GMAIL_APP_PASSWORD")
    recipients = _require_csv_env(
        "RECIPIENT_EMAILS", "RECIPIENT_EMAILS must contain at least one address"
    )
    send_email_enabled = os.environ.get("SEND_EMAIL", "false").lower() == "true"

    driver = setup_driver()
    ixl_data: list[IXLStudentProgress] = []
    math_academy_data: list[MathAcademyStudentProgress] = []

    try:
        try:
            ixl_data = IXLStatsScraper(driver).get_stats(ixl_username, ixl_password)
            logger.info("IXL scraping completed successfully")
        except Exception as e:
            logger.error(f"Error during IXL scraping: {e!s}")

        try:
            math_academy_data = MathAcademyStatsScraper(driver).get_stats(
                mathacademy_username,
                mathacademy_password,
                mathacademy_student_ids,
            )
            logger.info("Math Academy scraping completed successfully")
        except Exception as e:
            logger.error(f"Error during Math Academy scraping: {e!s}")

        if not (ixl_data or math_academy_data):
            logger.warning("No data collected from either IXL or Math Academy. No email sent.")
            return

        html_content = build_report(ixl_data, math_academy_data)
        if send_email_enabled:
            send_email(
                "IXL and Math Academy Progress Report",
                html_content,
                gmail_user,
                gmail_app_password,
                recipients,
            )
        else:
            logger.info("skipping sending email")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e!s}")
    finally:
        driver.quit()
        logger.info("Script execution completed.")


if __name__ == "__main__":
    main()
