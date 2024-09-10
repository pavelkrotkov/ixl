# IXL and Math Academy Web Scraper

This repository contains a Python script that automates the process of scraping student progress data from IXL and Math Academy websites. It collects statistics, progress reports, and activity data for multiple students and sends a combined report via email.

## Features

- Scrapes data from both IXL and Math Academy
- Handles multiple students
- Collects daily and weekly progress
- Generates a combined HTML report
- Sends the report via email
- Can be run on a schedule using GitHub Actions

## How It Works

The script uses Selenium WebDriver to automate web browsers and BeautifulSoup for parsing HTML. Here's a high-level overview of the process:

1. Log in to IXL and Math Academy using provided credentials
2. Navigate to the relevant pages for each student
3. Extract progress data, statistics, and recent activity
4. Parse and format the collected data
5. Generate an HTML report combining data from both platforms
6. Send the report via email

## Setup

### Prerequisites

- Python 3.7+
- Chrome or Chromium browser
- ChromeDriver (installed automatically by the script)

### Environment Variables

The script uses several environment variables for configuration. When running on GitHub Actions, these should be set as repository secrets. For local development, you can use a `.env` file.

Required variables:

- `IXL_USERNAME`: Your IXL account username
- `IXL_PASSWORD`: Your IXL account password
- `MATHACADEMY_USERNAME`: Your Math Academy account username
- `MATHACADEMY_PASSWORD`: Your Math Academy account password
- `MATHACADEMY_STUDENT_IDS`: Comma-separated list of student IDs for Math Academy
- `GMAIL_USER`: Gmail address to send the report from
- `GMAIL_APP_PASSWORD`: Gmail app password (not your regular Gmail password)
- `RECIPIENT_EMAILS`: Comma-separated list of email addresses to receive the report

Optional variables:

- `HEADLESS`: Set to 'true' to run the browser in headless mode (default is 'true')
- `SEND_EMAIL`: Set to 'true' to send the email report (default is 'false')

### Running Locally

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (use a `.env` file or export them in your shell)
4. Run the script: `python scraper.py`

## GitHub Actions Setup

This repository includes a GitHub Actions workflow to run the scraper on a schedule. To set it up:

1. Go to your repository's Settings > Secrets and add all the required environment variables as repository secrets.

2. The workflow file (`.github/workflows/scraper.yml`) is already set up to run daily. You can adjust the schedule by modifying the cron expression in the workflow file.

3. The workflow will use the secrets you've set to run the scraper and send the email report.

## Customization

- To add or remove students from the Math Academy scraper, update the `MATHACADEMY_STUDENT_IDS` secret.
- To change the report recipients, update the `RECIPIENT_EMAILS` secret.
- To modify the scraping behavior or report format, edit the `scraper.py` file.

## Troubleshooting

- If you encounter issues with the Chrome browser, try updating to the latest version of Chrome and ChromeDriver.
- Check the GitHub Actions logs for any error messages if the scheduled run fails.
- Ensure that your Gmail account has "Less secure app access" enabled or use an app-specific password.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
