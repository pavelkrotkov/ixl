import os
import sys


def check_credentials():
    required_vars = [
        "IXL_USERNAME",
        "IXL_PASSWORD",
        "MATHACADEMY_USERNAME",
        "MATHACADEMY_PASSWORD",
        "MATHACADEMY_STUDENT_IDS",
        "GMAIL_USER",
        "GMAIL_APP_PASSWORD",
        "RECIPIENT_EMAILS",
    ]

    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
        else:
            print(f"{var} is set")

    if missing_vars:
        print("The following required environment variables are missing:")
        for var in missing_vars:
            print(f"- {var}")
        sys.exit(1)
    else:
        print("All required environment variables are set.")
        sys.exit(0)


if __name__ == "__main__":
    check_credentials()
