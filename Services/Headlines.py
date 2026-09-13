from playwright.async_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from Constants import Constants
from Helper import Helpers


class Headlines:

    def __init__(self, page: Page):

        self.page = page

    # ========================================================
    # LOGIN
    # ========================================================

    async def login(self):

        await self.page.goto(
            Constants.BASE_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        await self.page.wait_for_timeout(3000)

        # ----------------------------------------------------
        # Already logged in
        # ----------------------------------------------------

        if await Helpers.is_authenticated(
            self.page
        ):

            print("Already authenticated.")

            return

        # ----------------------------------------------------
        # Credentials
        # ----------------------------------------------------

        if (
            not Constants.NAUKRI_EMAIL
            or not Constants.NAUKRI_PASSWORD
        ):

            raise RuntimeError(
                "NAUKRI_EMAIL and NAUKRI_PASSWORD "
                "environment variables are required."
            )

        # ----------------------------------------------------
        # Login button
        # ----------------------------------------------------

        login_button = await Helpers.find_visible(
            self.page,
            [
                'a:has-text("Login")',
                'button:has-text("Login")',
                '[role="button"]:has-text("Login")',
                'text=Login',
            ],
        )

        if login_button is None:

            raise RuntimeError(
                "Could not find Naukri Login button."
            )

        await login_button.click()

        await self.page.wait_for_timeout(2500)

        # ----------------------------------------------------
        # Email
        # ----------------------------------------------------

        email_input = await Helpers.find_visible(
            self.page,
            [
                'input[type="email"]',
                'input[placeholder*="Email" i]',
                'input[name*="email" i]',
            ],
        )

        if email_input is None:

            raise RuntimeError(
                "Could not find Naukri email field."
            )

        # ----------------------------------------------------
        # Password
        # ----------------------------------------------------

        password_input = self.page.locator(
            'input[type="password"]'
        ).first

        await password_input.wait_for(
            state="visible",
            timeout=5000,
        )

        await email_input.fill(
            Constants.NAUKRI_EMAIL
        )

        await password_input.fill(
            Constants.NAUKRI_PASSWORD
        )

        # ----------------------------------------------------
        # Submit
        # ----------------------------------------------------

        submit_button = await Helpers.find_visible(
            self.page,
            [
                'button:has-text("Login")',
                'button[type="submit"]',
                'input[type="submit"]',
                '[role="button"]:has-text("Login")',
            ],
        )

        if submit_button is None:

            raise RuntimeError(
                "Could not find Login submit button."
            )

        await submit_button.click()

        try:

            await self.page.wait_for_url(
                lambda url: "/nlogin/" not in url,
                timeout=30000,
            )

        except PlaywrightTimeoutError:

            pass

        await self.page.wait_for_timeout(5000)

        if not await Helpers.is_authenticated(
            self.page
        ):

            raise RuntimeError(
                "Naukri login was not confirmed."
            )

        print("Login successful.")
        print("Current URL:", self.page.url)

    # ========================================================
    # OPEN PROFILE
    # ========================================================

    async def open_profile(self):

        await self.page.goto(
            Constants.PROFILE_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        await self.page.wait_for_timeout(5000)

        if await Helpers.is_login_page(
            self.page
        ):

            raise RuntimeError(
                "Naukri redirected to login."
            )

        if (
            "/mnjuser/profile"
            not in self.page.url.lower()
        ):

            if not await Helpers.is_authenticated(
                self.page
            ):

                raise RuntimeError(
                    "Could not confirm Naukri profile."
                )

        print("Profile opened.")
        print("Profile URL:", self.page.url)

    # ========================================================
    # UPDATE HEADLINE
    # ========================================================

    async def update_headline(
        self,
        headline: str = Constants.NEW_HEADLINE,
    ):

        headline_section = self.page.locator(
            "#lazyResumeHead"
        )

        await headline_section.wait_for(
            timeout=15000
        )

        print(
            "Resume headline section found."
        )

        # ----------------------------------------------------
        # Edit
        # ----------------------------------------------------

        edit_button = headline_section.locator(
            "button, [role='button'], [class*='edit']"
        ).first

        await edit_button.wait_for(
            timeout=10000
        )

        await edit_button.click()

        await self.page.wait_for_timeout(
            1500
        )

        print(
            "Resume headline editor opened."
        )

        # ----------------------------------------------------
        # Textarea
        # ----------------------------------------------------

        headline_input = self.page.locator(
            "textarea:visible"
        )

        await headline_input.wait_for(
            timeout=10000
        )

        await headline_input.fill(
            headline
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        save_button = self.page.get_by_role(
            "button",
            name="Save",
            exact=True,
        )

        await save_button.wait_for(
            timeout=10000
        )

        await save_button.click()

        await self.page.wait_for_timeout(
            3000
        )

        print(
            "Headline save button clicked."
        )

        # ----------------------------------------------------
        # Verify
        # ----------------------------------------------------

        updated_headline = (
            headline_section.get_by_text(
                headline,
                exact=True,
            )
        )

        if await updated_headline.count() > 0:

            print(
                "Resume headline updated successfully."
            )

            return True

        print(
            "Headline save completed, "
            "but verification failed."
        )

        return False