from playwright.async_api import Page


class Helpers:

    # ========================================================
    # LOGIN PAGE DETECTION
    # ========================================================

    @staticmethod
    async def is_login_page(page: Page) -> bool:

        try:

            url = page.url.lower()

            if "/nlogin/" in url:
                return True

            email_visible = False
            password_visible = False

            for selector in [
                'input[type="email"]',
                'input[placeholder*="email" i]',
                'input[name*="email" i]',
            ]:

                try:

                    if await page.locator(
                        selector
                    ).first.is_visible(timeout=1000):

                        email_visible = True
                        break

                except Exception:
                    pass

            try:

                password_visible = await page.locator(
                    'input[type="password"]'
                ).first.is_visible(
                    timeout=1000
                )

            except Exception:
                pass

            return (
                email_visible
                and password_visible
            )

        except Exception:

            return False

    # ========================================================
    # AUTHENTICATION DETECTION
    # ========================================================

    @staticmethod
    async def is_authenticated(
        page: Page,
    ) -> bool:

        await page.wait_for_timeout(2000)

        url = page.url.lower()

        if "/nlogin/" in url:
            return False

        if await Helpers.is_login_page(page):
            return False

        authenticated_paths = [
            "/mnjuser/homepage",
            "/mnjuser/profile",
            "/mnjuser/",
        ]

        for path in authenticated_paths:

            if path in url:
                return True

        for selector in [
            'a[href*="/mnjuser/profile"]',
            'a[href*="/mnjuser/homepage"]',
            'a[href*="logout"]',
        ]:

            try:

                if await page.locator(
                    selector
                ).first.is_visible(
                    timeout=1500
                ):

                    return True

            except Exception:
                pass

        return False

    # ========================================================
    # FIND VISIBLE ELEMENT
    # ========================================================

    @staticmethod
    async def find_visible(
        page: Page,
        selectors: list[str],
        timeout: int = 2000,
    ):

        for selector in selectors:

            try:

                locator = page.locator(
                    selector
                ).first

                if await locator.is_visible(
                    timeout=timeout
                ):

                    return locator

            except Exception:
                pass

        return None