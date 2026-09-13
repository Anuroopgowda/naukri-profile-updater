import asyncio

from playwright.async_api import async_playwright

from Constants import Constants
from Services.Headlines import Headlines
from Services.ResumeUploader import ResumeUploader


async def main():

    print("=" * 60)
    print("NAUKRI AUTOMATION STARTED")
    print("=" * 60)

    async with async_playwright() as playwright:

        browser = await playwright.chromium.launch(
            headless=Constants.HEADLESS,
            args=[
                "--start-maximized",
            ],
        )

        context = await browser.new_context(
            viewport={
                "width": Constants.BROWSER_WIDTH,
                "height": Constants.BROWSER_HEIGHT,
            },
        )

        page = (
            context.pages[0]
            if context.pages
            else await context.new_page()
        )
        page = (
            context.pages[0]
            if context.pages
            else await context.new_page()
        )
        try:
            # ==================================================
            # NAUKRI
            # ==================================================

            naukri = Headlines(page)

            await naukri.login()

            await naukri.open_profile()

            # ==================================================
            # RESUME
            # ==================================================

            resume = ResumeUploader(page)
            await resume.upload_resume()
            verified = await resume.verify_resume()
            if verified:
                print("Resume uploaded successfully.")
            else:
                print("Resume upload could not be verified.")

            # ==================================================
            # HEADLINE
            # ==================================================

            await naukri.update_headline()

            # ==================================================
            # COMPLETE
            # ==================================================

            print()
            print("=" * 60)
            print("NAUKRI AUTOMATION COMPLETED")
            print("=" * 60)

            await page.wait_for_timeout(
                3000
            )
        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())