from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from progress import MathAcademyStudentProgress
from scraper_base import BaseStatsScraper


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
            self.logger.error(f"Login failed for Math Academy: {e!s}")
            self.driver.save_screenshot("math_academy_login_error.png")
            raise

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
