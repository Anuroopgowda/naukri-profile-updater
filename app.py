import os
import sys
import time
from pathlib import Path
from datetime import datetime

import requests
from playwright.sync_api import sync_playwright


NAUKRI_URL = "https://www.naukri.com/"
PROFILE_URL = "https://www.naukri.com/mnjuser/profile"

EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")

NEW_HEADLINE = (
    "1.9 Yrs Software Engineer | Python FastAPI Backend | REST APIs "
    "Microservices Docker | PostgreSQL AWS | LLM & Automation | "
    "Bengaluru | 1 Month Notice"
)

HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

BASE_DIR = Path(__file__).resolve().parent
RESUME_PATH = BASE_DIR / "Anuroop_gowda_c_resume.pdf"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram(message):
    """
    Send notification to Telegram.
    If Telegram configuration is missing, simply skip notification.
    """

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram notification is not configured.")
        return

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=15,
        )

        response.raise_for_status()

        print("Telegram notification sent.")

    except Exception as exc:
        print(f"Telegram notification failed: {exc}")


def validate_configuration():

    if not EMAIL:
        raise RuntimeError(
            "NAUKRI_EMAIL environment variable is missing."
        )

    if not PASSWORD:
        raise RuntimeError(
            "NAUKRI_PASSWORD environment variable is missing."
        )

    if not RESUME_PATH.exists():
        raise RuntimeError(
            f"Resume file not found: {RESUME_PATH}"
        )

    file_size_mb = RESUME_PATH.stat().st_size / (1024 * 1024)

    if file_size_mb > 2:
        raise RuntimeError(
            f"Resume is {file_size_mb:.2f} MB. "
            "Naukri allows maximum 2 MB."
        )

    print("Configuration validated.")


def create_browser(playwright):

    browser = playwright.chromium.launch(
        headless=HEADLESS
    )

    page = browser.new_page()

    page.set_default_timeout(15000)

    return browser, page


def login(page):

    print("Opening Naukri...")

    page.goto(
        NAUKRI_URL,
        wait_until="domcontentloaded"
    )

    print("Current URL:", page.url)
    print("Page title:", page.title())

    page.screenshot(
        path="naukri_login_debug.png",
        full_page=True
    )

    print("Page HTML:")
    print(page.locator("body").inner_text()[:5000])

    print("Clicking Login...")

    page.get_by_role(
        "button",
        name="Login"
    ).click()

    page.wait_for_timeout(2000)

    print("Entering credentials...")

    page.locator(
        'input[placeholder="Enter Email ID / Username"]'
    ).fill(EMAIL)

    page.locator(
        'input[placeholder="Enter Password"]'
    ).fill(PASSWORD)

    page.get_by_role(
        "button",
        name="Login"
    ).click()

    page.wait_for_timeout(5000)

    print("Current URL:", page.url)

    if "login" in page.url.lower():
        raise RuntimeError(
            "Naukri login appears to have failed."
        )

    print("Logged in successfully.")


def open_profile(page):

    print("Opening profile...")

    page.goto(
        PROFILE_URL,
        wait_until="domcontentloaded"
    )

    page.wait_for_timeout(3000)

    print("Profile URL:", page.url)


def update_resume_headline(page):

    print("Updating resume headline...")

    headline_section = page.locator(
        "#lazyResumeHead"
    )

    headline_section.wait_for(
        state="visible",
        timeout=15000
    )

    # Find edit button inside headline section
    edit_button = headline_section.locator(
        "button, [role='button'], [class*='edit']"
    ).first

    edit_button.click()

    page.wait_for_timeout(1000)

    textarea = page.locator(
        "textarea:visible"
    ).last

    textarea.fill(NEW_HEADLINE)

    save_button = page.get_by_role(
        "button",
        name="Save",
        exact=True
    ).last

    save_button.click()

    page.wait_for_timeout(2000)

    if not page.get_by_text(
        NEW_HEADLINE,
        exact=True
    ).is_visible():

        raise RuntimeError(
            "Headline update could not be verified."
        )

    print("Headline updated successfully.")


def upload_resume(page):

    print("Uploading resume...")

    resume_file_input = page.locator(
        "#attachCV"
    )

    resume_file_input.wait_for(
        state="attached",
        timeout=15000
    )

    print("Selecting resume file...")

    resume_file_input.set_input_files(
        str(RESUME_PATH)
    )

    update_resume_button = page.locator(
        'input.dummyUpload[value="Update resume"]'
    )

    update_resume_button.wait_for(
        state="visible",
        timeout=10000
    )

    print("Clicking Update resume...")

    update_resume_button.click()

    page.wait_for_timeout(8000)

    filename = page.locator(
        '.resume-name-inline[title="Anuroop_gowda_c_resume.pdf"]'
    )

    filename.wait_for(
        state="visible",
        timeout=15000
    )

    print("Resume filename verified.")

    uploaded_date = page.locator(
        ".cvPreview .updateOn"
    ).first

    if uploaded_date.is_visible():

        date_text = uploaded_date.inner_text()

        print(
            "Resume upload information:",
            date_text
        )

    print("Resume uploaded successfully.")


def run_automation():

    validate_configuration()

    with sync_playwright() as playwright:

        browser = None

        try:

            browser, page = create_browser(
                playwright
            )

            login(page)

            open_profile(page)

            update_resume_headline(page)

            upload_resume(page)

            return True

        finally:

            if browser:

                browser.close()


def main():

    started_at = datetime.now()

    try:

        print("=" * 60)
        print("NAUKRI AUTOMATION STARTED")
        print("=" * 60)

        run_automation()

        finished_at = datetime.now()

        message = (
            "🤖 Naukri Automation\n\n"
            "✅ SUCCESS\n\n"
            "Resume: Updated\n"
            "Headline: Updated\n"
            f"Started: {started_at.strftime('%d %b %Y %I:%M %p')}\n"
            f"Finished: {finished_at.strftime('%d %b %Y %I:%M %p')}"
        )

        print(message)

        send_telegram(message)

        print("=" * 60)
        print("AUTOMATION COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as exc:

        finished_at = datetime.now()

        print("=" * 60)
        print("AUTOMATION FAILED")
        print("=" * 60)

        print("ERROR:", str(exc))

        message = (
            "🤖 Naukri Automation\n\n"
            "❌ FAILED\n\n"
            f"Error: {str(exc)}\n\n"
            f"Time: {finished_at.strftime('%d %b %Y %I:%M %p')}\n\n"
            "Check Render logs for details."
        )

        send_telegram(message)

        sys.exit(1)


if __name__ == "__main__":
    main()