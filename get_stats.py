import logging

from ixl_scraper import IXLStatsScraper
from math_academy_scraper import MathAcademyStatsScraper
from progress import IXLStudentProgress, MathAcademyStudentProgress
from report import build_report
from runtime import env_enabled, require_csv_env, require_env, send_email, setup_driver

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    logger = logging.getLogger(__name__)

    ixl_username = require_env("IXL_USERNAME")
    ixl_password = require_env("IXL_PASSWORD")
    mathacademy_username = require_env("MATHACADEMY_USERNAME")
    mathacademy_password = require_env("MATHACADEMY_PASSWORD")
    mathacademy_student_ids = require_csv_env(
        "MATHACADEMY_STUDENT_IDS", "MATHACADEMY_STUDENT_IDS must contain at least one ID"
    )
    gmail_user = require_env("GMAIL_USER")
    gmail_app_password = require_env("GMAIL_APP_PASSWORD")
    recipients = require_csv_env(
        "RECIPIENT_EMAILS", "RECIPIENT_EMAILS must contain at least one address"
    )
    send_email_enabled = env_enabled("SEND_EMAIL")

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
