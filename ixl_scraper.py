import time

from selenium.webdriver.common.by import By

from ixl_parser import process_table_html
from ixl_session import IXLSession
from progress import IXLStudentProgress


class IXLStatsScraper(IXLSession):
    def process_student_data(self, student_id: str) -> IXLStudentProgress | None:
        student_name = student_id
        try:
            time.sleep(3)
            stats_element = self.find_element(By.CSS_SELECTOR, ".summary-stat-container")
            stats_text = " ".join(stats_element.text.split()).lower()
            self.logger.info(f"IXL Stats for {student_name}: {stats_text}")

            progress_table = None
            if (
                "answered 0 questions spent 0 min practicing made progress in 0 skills"
                in stats_text
            ):
                self.logger.info(f"No progress to report for {student_name}")
            else:
                table_html = self.get_progress_and_improvement_data(student_name)
                progress_table = process_table_html(table_html) if table_html else None

            return IXLStudentProgress(student_name, stats_text, progress_table)
        except Exception as e:
            self.logger.error(f"Error processing IXL data for {student_name}: {e!s}")
            return None

    def get_progress_and_improvement_data(self, student_name: str) -> str | None:
        try:
            self.driver.get("https://www.ixl.com/analytics/progress-and-improvement")
            self.logger.info(f"Navigated to Progress and Improvement page for {student_name}")
            time.sleep(3)

            table = self.find_element(By.CSS_SELECTOR, ".student-improvement-table")
            table_html = table.get_attribute("outerHTML")

            self.driver.get(self.login_url)
            self.logger.info(f"Navigated back to main analytics page for {student_name}")
            return table_html
        except Exception as e:
            self.logger.error(
                f"Error extracting IXL progress and improvement data for {student_name}: {e!s}"
            )
            self.driver.save_screenshot(f"ixl_progress_improvement_error_{student_name}.png")
            return None

    def get_stats(self, username, password) -> list[IXLStudentProgress]:
        data = []
        try:
            self.login(username, password)
            self.select_date_range()
            student_names = [
                name
                for student in self.get_student_options()
                if (name := student.get_attribute("data-name"))
            ]

            for student_name in student_names:
                self.logger.info(f"Processing IXL student: {student_name}")
                if not self.select_student(student_name):
                    self.logger.warning(f"Failed to select IXL student: {student_name}")
                    continue
                if student_data := self.process_student_data(student_name):
                    data.append(student_data)
        except Exception as e:
            self.logger.error(f"An error occurred during IXL stats collection: {e!s}")
        return data
