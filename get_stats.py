import logging
import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from bs4 import BeautifulSoup

class IXLStatsScraper:
    def __init__(self):
        self.setup_logger()
        self.setup_driver()
        self.student_data = {}

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
        headless_mode = os.environ.get('HEADLESS', 'true').lower() == 'true'
        if headless_mode:
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
        self.logger.info(f"WebDriver setup completed. Headless mode: {headless_mode}")

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

    def get_student_options(self):
        self.click_element(By.CSS_SELECTOR, ".student-select .option-select.global .select-open")
        self.find_element(By.CSS_SELECTOR, ".student-select .select-body")
        return self.driver.find_elements(By.CSS_SELECTOR, ".option-select.global.default.active .select-dropdown .option")
        
    def select_student(self, student_name):
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                student_options = self.get_student_options()
                for student in student_options:
                    if student.get_attribute('data-name') == student_name:
                        student.click()
                        self.wait.until(EC.text_to_be_present_in_element(
                            (By.CSS_SELECTOR, ".student-select .option-selection"), student_name
                        ))
                        return True
                return False
            except StaleElementReferenceException:
                if attempt < max_attempts - 1:
                    self.logger.warning(f"Stale element encountered when selecting {student_name}. Retrying...")
                    time.sleep(1)
                else:
                    self.logger.error(f"Failed to select student {student_name} after {max_attempts} attempts.")
                    return False

    def select_students(self):
        try:
            student_options = self.get_student_options()
            student_names = [student.get_attribute('data-name') for student in student_options]
            if len(student_options):
                student_options[0].click()

            for student_name in student_names:
                self.logger.info(f"Processing student: {student_name}")
                if self.select_student(student_name):
                    self.process_student_data(student_name)
                    self.get_progress_and_improvement_data(student_name)
                    # Navigate back to the main analytics page
                    self.driver.get("https://www.ixl.com/analytics/student-usage#")
                else:
                    self.logger.warning(f"Failed to select student: {student_name}")

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
            self.student_data[student_name] = {'stats': stats_text.lower()}
        except Exception as e:
            self.logger.error(f"Error processing data for {student_name}: {str(e)}")

    def get_progress_and_improvement_data(self, student_name):
        try:
            self.driver.get("https://www.ixl.com/analytics/progress-and-improvement")
            self.logger.info(f"Navigated to Progress and Improvement page for {student_name}")
            time.sleep(3)
            
            # Wait for the table to load
            table = self.find_element(By.CSS_SELECTOR, ".student-improvement-table")

            # Get the HTML of the table
            table_html = table.get_attribute('outerHTML')

            # Store the table HTML in the student_data dictionary
            self.student_data[student_name]['progress_table'] = table_html

            # Extract and log the table data (for console output)
            rows = table.find_elements(By.CSS_SELECTOR, ".skill-row")
            for row in rows:
                skill_name = row.find_element(By.CSS_SELECTOR, ".skill-name-and-permacode span").text
                skill_code = row.find_element(By.CSS_SELECTOR, ".permacode").text
                time_spent = row.find_element(By.CSS_SELECTOR, ".skill-time").text
                questions = row.find_element(By.CSS_SELECTOR, ".skill-questions").text
                scores = [x.text for x in row.find_elements(By.CSS_SELECTOR, ".skill-improvement .score")]
                score_from = scores[0]
                score_to = scores[1]

                log_message = f"{student_name} - Skill: {skill_name} ({skill_code}), Time: {time_spent}, Questions: {questions}, Improvement: {score_from} to {score_to}"
                self.logger.info(log_message)

            # Navigate back to the main analytics page
            self.driver.get("https://www.ixl.com/analytics/student-usage#")
            self.logger.info(f"Navigated back to main analytics page for {student_name}")

        except Exception as e:
            self.logger.error(f"Error extracting progress and improvement data for {student_name}: {str(e)}")
            self.driver.save_screenshot(f"progress_improvement_error_{student_name}.png")
            raise

    def process_table_html(self, table_html):
        soup = BeautifulSoup(table_html, 'html.parser')
        
        # Create a new table
        new_table = soup.new_tag('table')
        new_table['style'] = 'border-collapse: collapse; width: 100%;'
        
        # Add header row
        header = soup.new_tag('tr')
        headers = ['Subject/Category/Skill', 'Code', 'Time Spent', '#', 'Score Improvement']
        for h in headers:
            th = soup.new_tag('th')
            th.string = h
            th['style'] = 'border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;'
            header.append(th)
        new_table.append(header)

        # Process rows
        for row in soup.select('div[class*="row"]'):
            new_row = soup.new_tag('tr')
            
            if 'subject-grade-row' in row.get('class', []):
                td = soup.new_tag('td')
                td.string = row.text.strip()
                td['colspan'] = '5'
                td['style'] = 'border: 1px solid #ddd; padding: 8px; font-weight: bold; background-color: #e6e6e6;'
                new_row.append(td)
            elif 'category-row' in row.get('class', []):
                td = soup.new_tag('td')
                td.string = row.text.strip()
                td['colspan'] = '5'
                td['style'] = 'border: 1px solid #ddd; padding: 8px; font-style: italic; background-color: #f9f9f9;'
                new_row.append(td)
            elif 'skill-row' in row.get('class', []):
                cells = [
                    row.select_one('.skill-name-and-permacode span'),
                    row.select_one('.permacode'),
                    row.select_one('.skill-time'),
                    row.select_one('.skill-questions'),
                    row.select('.skill-improvement .score')
                ]
                
                for i, cell in enumerate(cells):
                    td = soup.new_tag('td')
                    td['style'] = 'border: 1px solid #ddd; padding: 8px;'
                    if i == 4 and cell:  # Score Improvement
                        td.string = f"{cell[0].text} to {cell[1].text}" if len(cell) == 2 else "N/A"
                    elif cell:
                        td.string = cell.text.strip()
                    else:
                        td.string = "N/A"
                    new_row.append(td)
            
            new_table.append(new_row)

        return str(new_table)

    def send_email(self):
        gmail_user = os.environ.get('GMAIL_USER')
        gmail_app_password = os.environ.get('GMAIL_APP_PASSWORD')
        recipients = os.environ.get('RECIPIENT_EMAILS', '').split(',')

        if not all([gmail_user, gmail_app_password, recipients]):
            self.logger.error("Email configuration is incomplete. Skipping email send.")
            return

        message = MIMEMultipart("alternative")
        message["Subject"] = "IXL Stats Report"
        message["From"] = gmail_user
        message["To"] = ", ".join(recipients)

        html_content = "<html><body>"

        for student, data in self.student_data.items():
            html_content += f"<h2>{student}</h2>"
            html_content += f"<p>{data['stats']}</p>"
            html_content += f"<h3>Progress and Improvement</h3>"
            html_content += self.process_table_html(data['progress_table'])
            html_content += "<hr>"

        html_content += "</body></html>"

        message.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(gmail_user, gmail_app_password)
                server.sendmail(gmail_user, recipients, message.as_string())
            self.logger.info(f"Email sent successfully to {', '.join(recipients)}")
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
       
    def get_stats(self, send_email=False):
        try:
            username = os.environ.get('IXL_USERNAME')
            password = os.environ.get('IXL_PASSWORD')
            if not username or not password:
                raise ValueError("IXL credentials not set in environment variables")

            self.login(username, password)
            self.select_date_range("Today")
            self.select_students()

            if send_email:
                self.send_email()
        except Exception as e:
            self.logger.error(f"An error occurred during stats collection: {str(e)}")
        finally:
            self.driver.quit()
            self.logger.info("WebDriver closed")

if __name__ == "__main__":
    scraper = IXLStatsScraper()
    send_email = os.environ.get('SEND_EMAIL', 'false').lower() == 'true'
    scraper.get_stats(send_email=send_email)