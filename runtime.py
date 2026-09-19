import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def require_env(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"{name} not set in environment variables")
    return value


def require_csv_env(name, empty_message):
    values = [value.strip() for value in require_env(name).split(",") if value.strip()]
    if not values:
        raise ValueError(empty_message)
    return values


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
