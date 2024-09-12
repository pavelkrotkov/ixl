import logging
import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from bs4 import BeautifulSoup

# Set up logging once at the module level
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class BaseStatsScraper(ABC):
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.student_data = {}

    def find_element(self, by, value, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            self.logger.error(f"Element not found: {by}={value}")
            self.driver.save_screenshot(
                f"element_not_found_{value.replace(' ', '_')}.png"
            )
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
    def get_stats(self):
        pass


class IXLStatsScraper(BaseStatsScraper):
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

            self.find_element(
                By.CSS_SELECTOR, "label[data-cy^='subaccount-selection-']"
            )
            parent_subaccount = self.find_element(
                By.XPATH,
                "//label[contains(@data-cy, 'subaccount-selection-') and .//span[text()='Parent']]",
            )
            parent_subaccount.click()
            self.logger.info("Selected 'Parent' subaccount")

        except Exception as e:
            self.logger.error(f"Login or subaccount selection failed: {str(e)}")
            self.driver.save_screenshot("ixl_login_error.png")
            raise

    def select_date_range(self, option="Today"):
        try:
            self.find_element(By.CSS_SELECTOR, ".date-range")
            self.click_element(
                By.CSS_SELECTOR, ".date-range .option-select.global .select-open"
            )
            self.find_element(By.CSS_SELECTOR, ".date-range .select-body")
            self.click_element(
                By.XPATH, f"//div[@class='option' and contains(text(), '{option}')]"
            )
            self.wait.until(
                EC.text_to_be_present_in_element(
                    (By.CSS_SELECTOR, ".date-range .option-selection"), option
                )
            )
            self.logger.info(f"Selected date range: {option}")
        except Exception as e:
            self.logger.error(f"Failed to select date range: {str(e)}")
            self.driver.save_screenshot("ixl_date_range_error.png")
            raise

    def get_student_options(self):
        self.click_element(
            By.CSS_SELECTOR, ".student-select .option-select.global .select-open"
        )
        self.find_element(By.CSS_SELECTOR, ".student-select .select-body")
        return self.driver.find_elements(
            By.CSS_SELECTOR,
            ".option-select.global.default.active .select-dropdown .option",
        )

    def select_student(self, student_name):
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                student_options = self.get_student_options()
                for student in student_options:
                    if student.get_attribute("data-name") == student_name:
                        student.click()
                        self.wait.until(
                            EC.text_to_be_present_in_element(
                                (By.CSS_SELECTOR, ".student-select .option-selection"),
                                student_name,
                            )
                        )
                        return True
                continue
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

    def process_student_data(self, student_name):
        try:
            time.sleep(3)
            stats_element = self.find_element(
                By.CSS_SELECTOR, ".summary-stat-container"
            )
            stats_text = " ".join(stats_element.text.split())
            self.logger.info(f"IXL Stats for {student_name}: {stats_text.lower()}")
            self.student_data[student_name] = {"stats": stats_text.lower()}

            # Check if progress report is needed
            if (
                "answered 0 questions spent 0 min practicing made progress in 0 skills"
                not in stats_text.lower()
            ):
                self.get_progress_and_improvement_data(student_name)
            else:
                self.logger.info(f"No progress to report for {student_name}")

        except Exception as e:
            self.logger.error(f"Error processing IXL data for {student_name}: {str(e)}")

    def get_progress_and_improvement_data(self, student_name):
        try:
            self.driver.get("https://www.ixl.com/analytics/progress-and-improvement")
            self.logger.info(
                f"Navigated to Progress and Improvement page for {student_name}"
            )
            time.sleep(3)

            table = self.find_element(By.CSS_SELECTOR, ".student-improvement-table")
            table_html = table.get_attribute("outerHTML")
            self.student_data[student_name]["progress_table"] = table_html

            rows = table.find_elements(By.CSS_SELECTOR, ".skill-row")
            for row in rows:
                skill_name = row.find_element(
                    By.CSS_SELECTOR, ".skill-name-and-permacode span"
                ).text
                skill_code = row.find_element(By.CSS_SELECTOR, ".permacode").text
                time_spent = row.find_element(By.CSS_SELECTOR, ".skill-time").text
                questions = row.find_element(By.CSS_SELECTOR, ".skill-questions").text
                scores = [
                    x.text
                    for x in row.find_elements(
                        By.CSS_SELECTOR, ".skill-improvement .score"
                    )
                ]
                score_from = scores[0] if scores else "N/A"
                score_to = scores[1] if len(scores) > 1 else "N/A"

                log_message = f"{student_name} - Skill: {skill_name} ({skill_code}), Time: {time_spent}, Questions: {questions}, Improvement: {score_from} to {score_to}"
                self.logger.info(log_message)

            self.driver.get(self.login_url)
            self.logger.info(
                f"Navigated back to main analytics page for {student_name}"
            )

        except Exception as e:
            self.logger.error(
                f"Error extracting IXL progress and improvement data for {student_name}: {str(e)}"
            )
            self.driver.save_screenshot(
                f"ixl_progress_improvement_error_{student_name}.png"
            )
            raise

    def get_stats(self):
        try:
            username = os.environ.get("IXL_USERNAME")
            password = os.environ.get("IXL_PASSWORD")
            if not username:
                raise ValueError("IXL_USERNAME not set in environment variables")
            if not password:
                raise ValueError("IXL_PASSWORD not set in environment variables")

            self.login(username, password)
            self.select_date_range("Today")

            student_options = self.get_student_options()
            student_names = [
                student.get_attribute("data-name") for student in student_options
            ]

            for student_name in student_names:
                self.logger.info(f"Processing IXL student: {student_name}")
                if self.select_student(student_name):
                    self.process_student_data(student_name)
                else:
                    self.logger.warning(f"Failed to select IXL student: {student_name}")

        except Exception as e:
            self.logger.error(
                f"An error occurred during IXL stats collection: {str(e)}"
            )


class MathAcademyStatsScraper(BaseStatsScraper):
    def __init__(self, driver):
        super().__init__(driver)
        self.login_url = "https://mathacademy.com/login"
        self.base_activity_url = "https://mathacademy.com/students/{}/activity"

    def login(self, username, password):
        try:
            self.driver.get(self.login_url)

            username_field = self.find_element(By.ID, "usernameOrEmail")
            username_field.clear()
            username_field.send_keys(username)

            password_field = self.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)

            self.click_element(By.ID, "loginButton")

            WebDriverWait(self.driver, 10).until(EC.url_changes(self.login_url))

            self.logger.info("Successfully logged in to Math Academy")
        except Exception as e:
            self.logger.error(f"Login failed for Math Academy: {str(e)}")
            self.driver.save_screenshot("math_academy_login_error.png")
            raise

    def get_student_ids(self):
        student_ids = os.environ.get("MATHACADEMY_STUDENT_IDS", "")
        if not student_ids:
            self.logger.error("MATHACADEMY_STUDENT_IDS environment variable is not set")
            return []
        return student_ids.split(",")

    def process_student_data(self, student_id):
        try:
            activity_url = self.base_activity_url.format(student_id)
            self.driver.get(activity_url)

            # Get student name
            student_name_element = self.find_element(By.ID, "studentName")
            student_name = student_name_element.text.strip()

            # Extract daily and weekly XP
            daily_xp_element = self.find_element(By.ID, "dailyGoalPoints")
            daily_xp_text = daily_xp_element.text.strip()
            daily_xp_earned, daily_xp_goal = (
                daily_xp_text.split("/")[0],
                daily_xp_text.split("/")[1].split()[0],
            )

            weekly_xp_element = self.find_element(By.ID, "thisWeekTotalXP")
            weekly_xp = weekly_xp_element.text.split()[0]

            # Extract activity report
            activity_element = self.find_element(By.ID, "tasksFrame")
            activity_html = activity_element.get_attribute("outerHTML")

            self.student_data[student_name] = {
                "student_id": student_id,
                "daily_xp_earned": daily_xp_earned,
                "daily_xp_goal": daily_xp_goal,
                "weekly_xp": weekly_xp,
                "activity_html": activity_html,
            }

            self.logger.info(
                f"Processed Math Academy data for student: {student_name} (ID: {student_id})"
            )
        except Exception as e:
            self.logger.error(
                f"Error processing Math Academy data for student ID {student_id}: {str(e)}"
            )
            self.driver.save_screenshot(f"math_academy_student_{student_id}_error.png")

    @staticmethod
    def parse_activity_html(activity_html):
        soup = BeautifulSoup(activity_html, "html.parser")
        parsed_data = []
        date_count = 0

        for tr in soup.find_all("tr"):
            if tr.get("class", []) == []:
                date_td = tr.find("td", class_="dateHeader")
                if date_td:
                    date_count += 1
                    if date_count >= 2:
                        break  # Stop parsing after the second date row
                    xp_span = date_td.find("span", class_="dateTotalXP")
                    xp = xp_span.get_text(strip=True) if xp_span else ""

                    # Remove the XP span from the date_td to get the date
                    if xp_span:
                        xp_span.extract()
                    date = date_td.get_text(strip=True)
                    parsed_data.append({"type": "date", "date": date, "xp": xp})
            elif date_count < 3:  # Only parse task rows before the third date row
                task_type_td = tr.find("td", class_="taskTypeColumn")
                task_name_div = tr.find("div", class_="taskName")
                completion_td = tr.find("td", class_="taskCompletedColumn")
                points_span = tr.find("span", class_="taskPoints") or tr.find(
                    "span", class_="completedTaskPoints"
                )

                parsed_data.append(
                    {
                        "type": "task",
                        "task_type": (
                            task_type_td.get_text(strip=True) if task_type_td else ""
                        ),
                        "task_name": (
                            task_name_div.get_text(strip=True) if task_name_div else ""
                        ),
                        "completion": (
                            completion_td.get_text(strip=True) if completion_td else ""
                        ),
                        "points": (
                            points_span.get_text(strip=True) if points_span else ""
                        ),
                    }
                )

        return parsed_data

    @staticmethod
    def format_activity_html(parsed_data):
        html = "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        html += "<tr style='background-color: #f2f2f2;'><th>Type</th><th>Name</th><th>Completion</th><th>Points</th></tr>"

        for item in parsed_data:
            if item["type"] == "date":
                html += "<tr style='background-color: #e6e6e6;'>"
                html += f"<td colspan='4'><strong>{item['date']} - {item['xp']}</strong></td></tr>"
            else:
                html += f"<tr><td>{item['task_type']}</td><td>{item['task_name']}</td><td>{item['completion']}</td><td>{item['points']}</td></tr>"

        html += "</table>"
        return html

    def get_stats(self):
        try:
            username = os.environ.get("MATHACADEMY_USERNAME")
            password = os.environ.get("MATHACADEMY_PASSWORD")
            if not username:
                raise ValueError(
                    "MATHACADEMY_USERNAME not set in environment variables"
                )
            if not password:
                raise ValueError(
                    "MATHACADEMY_PASSWORD not set in environment variables"
                )

            self.login(username, password)

            student_ids = self.get_student_ids()
            for student_id in student_ids:
                self.process_student_data(student_id)

        except Exception as e:
            self.logger.error(
                f"An error occurred during Math Academy stats collection: {str(e)}"
            )


def setup_driver():
    chrome_options = Options()
    headless_mode = os.environ.get("HEADLESS", "true").lower() == "true"
    if headless_mode:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    if os.environ.get("GITHUB_ACTIONS"):
        service = Service("chromedriver")
    else:
        from webdriver_manager.chrome import ChromeDriverManager

        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_window_size(1920, 1080)
    return driver


def send_email(subject, html_content):
    gmail_user = os.environ.get("GMAIL_USER")
    gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipients = os.environ.get("RECIPIENT_EMAILS", "").split(",")

    if not all([gmail_user, gmail_app_password, recipients]):
        logging.error("Email configuration is incomplete. Skipping email send.")
        return

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
        logging.error(f"Failed to send email: {str(e)}")


def main():
    logger = logging.getLogger(__name__)

    driver = setup_driver()
    ixl_data = {}
    math_academy_data = {}

    try:
        # IXL scraping
        try:
            ixl_scraper = IXLStatsScraper(driver)
            ixl_scraper.get_stats()
            ixl_data = ixl_scraper.student_data
            logger.info("IXL scraping completed successfully")
        except Exception as e:
            logger.error(f"Error during IXL scraping: {str(e)}")

        # Math Academy scraping
        try:
            math_academy_scraper = MathAcademyStatsScraper(driver)
            math_academy_scraper.get_stats()
            math_academy_data = math_academy_scraper.student_data
            logger.info("Math Academy scraping completed successfully")
        except Exception as e:
            logger.error(f"Error during Math Academy scraping: {str(e)}")

        # Prepare and send email
        if ixl_data or math_academy_data:
            html_content = "<html><body>"
            if ixl_data:
                # IXL Report
                html_content += "<h2>IXL</h2>"
                for student_name, data in ixl_data.items():
                    html_content += f"<h3>{student_name} {data['stats']}</h3>"
                    if "progress_table" in data:
                        html_content += data["progress_table"]

            if math_academy_data:
                # Math Academy Report
                html_content += "<h2>Math Academy</h2>"
                for student_name, data in math_academy_data.items():
                    html_content += f"<h3>{student_name}: today {data['daily_xp_earned']}/{data['daily_xp_goal']} XP, this week {data['weekly_xp']} XP</h3>"

                    parsed_activity = MathAcademyStatsScraper.parse_activity_html(
                        data["activity_html"]
                    )
                    formatted_activity = MathAcademyStatsScraper.format_activity_html(
                        parsed_activity
                    )
                    html_content += formatted_activity

            html_content += "</body></html>"

            if os.environ.get("SEND_EMAIL", "false").lower() == "true":
                send_email("IXL and Math Academy Progress Report", html_content)
            else:
                logger.info("skipping sending email")
        else:
            logger.warning(
                "No data collected from either IXL or Math Academy. No email sent."
            )

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
    finally:
        driver.quit()
        logger.info("Script execution completed.")


if __name__ == "__main__":
    main()
