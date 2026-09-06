import os
import sys
import threading
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from playwright.sync_api import sync_playwright


# ============================================================
# CONFIGURATION
# ============================================================

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

IST = ZoneInfo("Asia/Kolkata")


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Naukri Profile Automation"
)


# ============================================================
# STATE
# ============================================================

automation_lock = threading.Lock()

last_run_status = "NOT_RUN"
last_run_time = None
last_run_error = None


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(message: str):

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram is not configured.")
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
            timeout=15
        )

        response.raise_for_status()

        print("Telegram notification sent.")

    except Exception as exc:

        print(
            f"Telegram notification failed: {exc}"
        )


# ============================================================
# VALIDATION
# ============================================================

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

    file_size_mb = (
        RESUME_PATH.stat().st_size
        / (1024 * 1024)
    )

    if file_size_mb > 2:

        raise RuntimeError(
            f"Resume is {file_size_mb:.2f} MB. "
            "Naukri allows maximum 2 MB."
        )

    print("Configuration validated.")


# ============================================================
# BROWSER
# ============================================================

def create_browser(playwright):

    browser = playwright.chromium.launch(
        headless=HEADLESS
    )

    page = browser.new_page()

    page.set_default_timeout(15000)

    return browser, page


# ============================================================
# LOGIN
# ============================================================

def login(page):

    print("Opening Naukri...")

    page.goto(
        NAUKRI_URL,
        wait_until="domcontentloaded"
    )

    page.wait_for_timeout(3000)

    print("Current URL:", page.url)
    print("Page title:", page.title())

    # Check whether Naukri returned an access-denied page
    body_text = page.locator("body").inner_text()

    if "Access Denied" in body_text:

        raise RuntimeError(
            "Naukri returned 'Access Denied'. "
            "The current network/IP may be blocked."
        )

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

    print("Current URL after login:", page.url)

    if "login" in page.url.lower():

        raise RuntimeError(
            "Naukri login appears to have failed."
        )

    print("Logged in successfully.")


# ============================================================
# PROFILE
# ============================================================

def open_profile(page):

    print("Opening profile...")

    page.goto(
        PROFILE_URL,
        wait_until="domcontentloaded"
    )

    page.wait_for_timeout(3000)

    print(
        "Profile URL:",
        page.url
    )


# ============================================================
# UPDATE HEADLINE
# ============================================================

def update_resume_headline(page):

    print("Updating resume headline...")

    headline_section = page.locator(
        "#lazyResumeHead"
    )

    headline_section.wait_for(
        state="visible",
        timeout=15000
    )

    edit_button = headline_section.locator(
        "button, [role='button'], [class*='edit']"
    ).first

    edit_button.click()

    page.wait_for_timeout(1000)

    textarea = page.locator(
        "textarea:visible"
    ).last

    textarea.fill(
        NEW_HEADLINE
    )

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

    print(
        "Headline updated successfully."
    )


# ============================================================
# RESUME UPLOAD
# ============================================================

def upload_resume(page):

    print("Uploading resume...")

    resume_file_input = page.locator(
        "#attachCV"
    )

    resume_file_input.wait_for(
        state="attached",
        timeout=15000
    )

    print(
        "Selecting resume file..."
    )

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

    print(
        "Clicking Update resume..."
    )

    update_resume_button.click()

    page.wait_for_timeout(8000)

    filename = page.locator(
        '.resume-name-inline[title="Anuroop_gowda_c_resume.pdf"]'
    )

    filename.wait_for(
        state="visible",
        timeout=15000
    )

    print(
        "Resume filename verified."
    )

    uploaded_date = page.locator(
        ".cvPreview .updateOn"
    ).first

    if uploaded_date.is_visible():

        date_text = uploaded_date.inner_text()

        print(
            "Resume upload information:",
            date_text
        )

    print(
        "Resume uploaded successfully."
    )


# ============================================================
# ACTUAL AUTOMATION
# ============================================================

def run_automation():

    global last_run_status
    global last_run_time
    global last_run_error

    # Prevent two automation runs at the same time
    if not automation_lock.acquire(
        blocking=False
    ):

        print(
            "Automation is already running."
        )

        return

    try:

        started_at = datetime.now(IST)

        last_run_status = "RUNNING"
        last_run_time = started_at
        last_run_error = None

        print("=" * 60)
        print("NAUKRI AUTOMATION STARTED")
        print("=" * 60)

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

            finally:

                if browser:

                    browser.close()

        finished_at = datetime.now(IST)

        last_run_status = "SUCCESS"

        print("=" * 60)
        print("AUTOMATION COMPLETED SUCCESSFULLY")
        print("=" * 60)

        message = (
            "🤖 Naukri Automation\n\n"
            "✅ SUCCESS\n\n"
            "Resume: Updated\n"
            "Headline: Updated\n\n"
            f"Time: "
            f"{finished_at.strftime('%d %b %Y %I:%M %p')}"
        )

        send_telegram(message)

    except Exception as exc:

        finished_at = datetime.now(IST)

        last_run_status = "FAILED"
        last_run_error = str(exc)

        print("=" * 60)
        print("AUTOMATION FAILED")
        print("=" * 60)

        print(
            "ERROR:",
            str(exc)
        )

        message = (
            "🤖 Naukri Automation\n\n"
            "❌ FAILED\n\n"
            f"Error: {str(exc)}\n\n"
            f"Time: "
            f"{finished_at.strftime('%d %b %Y %I:%M %p')}\n\n"
            "Check Render logs."
        )

        send_telegram(message)

    finally:

        automation_lock.release()


# ============================================================
# SCHEDULER
# ============================================================

scheduler = BackgroundScheduler(
    timezone=IST
)


def start_scheduler():

    scheduler.add_job(
        run_automation,
        trigger=CronTrigger(
            hour=8,
            minute=0,
            timezone=IST
        ),
        id="naukri_daily_automation",
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )

    scheduler.start()

    print(
        "Scheduler started."
    )

    print(
        "Naukri automation scheduled "
        "for 8:00 AM IST every day."
    )


# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/")
def health_check():

    return {
        "service": "Naukri Profile Automation",
        "status": "running",
        "scheduled_time": "08:00 AM IST",
        "last_run_status": last_run_status,
        "last_run_time": (
            last_run_time.isoformat()
            if last_run_time
            else None
        ),
        "last_run_error": last_run_error
    }


@app.get("/run")
def manual_run():

    if automation_lock.locked():

        return {
            "status": "already_running"
        }

    thread = threading.Thread(
        target=run_automation,
        daemon=True
    )

    thread.start()

    return {
        "status": "started",
        "message": (
            "Naukri automation started."
        )
    }


# ============================================================
# START SCHEDULER
# ============================================================

start_scheduler()