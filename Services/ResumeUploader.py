from pathlib import Path

from playwright.async_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from Constants import Constants


class ResumeUploader:

    def __init__(
        self,
        page: Page,
        resume_path: Path = Constants.RESUME_PDF_PATH,
    ):

        self.page = page
        self.resume_path = Path(resume_path)

    # ========================================================
    # FIND UPDATE RESUME CONTROL
    # ========================================================

    async def find_update_resume_control(self):

        # ----------------------------------------------------
        # Exact input
        # ----------------------------------------------------

        locator = self.page.locator(
            'input[value="Update resume"]'
        )

        count = await locator.count()

        for i in range(count):

            candidate = locator.nth(i)

            try:

                if await candidate.is_visible(
                    timeout=1000
                ):

                    return candidate

            except Exception:
                pass

        # ----------------------------------------------------
        # Fallback inputs
        # ----------------------------------------------------

        selectors = [
            'input[value*="Update resume" i]',
            'input[type="button"][value*="Update" i]',
            'input[type="submit"][value*="Update" i]',
        ]

        for selector in selectors:

            locator = self.page.locator(
                selector
            )

            count = await locator.count()

            for i in range(count):

                candidate = locator.nth(i)

                try:

                    if await candidate.is_visible(
                        timeout=1000
                    ):

                        return candidate

                except Exception:
                    pass

        # ----------------------------------------------------
        # Text fallback
        # ----------------------------------------------------

        selectors = [
            'button:has-text("Update resume")',
            'button:has-text("Update Resume")',
            '[role="button"]:has-text("Update resume")',
            '[role="button"]:has-text("Update Resume")',
            'a:has-text("Update resume")',
            'a:has-text("Update Resume")',
        ]

        for selector in selectors:

            try:

                locator = self.page.locator(
                    selector
                )

                count = await locator.count()

                for i in range(
                    count - 1,
                    -1,
                    -1,
                ):

                    candidate = locator.nth(i)

                    try:

                        if await candidate.is_visible(
                            timeout=1000
                        ):

                            return candidate

                    except Exception:
                        pass

            except Exception:
                pass

        return None

    # ========================================================
    # UPLOAD
    # ========================================================

    async def upload_resume(self):

        if not self.resume_path.exists():

            raise FileNotFoundError(
                f"Resume not found:\n"
                f"{self.resume_path}"
            )

        if (
            self.resume_path.suffix.lower()
            != ".pdf"
        ):

            raise ValueError(
                "The resume file must be a PDF."
            )

        update_button = (
            await self.find_update_resume_control()
        )

        if update_button is None:

            raise RuntimeError(
                "Could not find 'Update resume'."
            )

        # ----------------------------------------------------
        # File chooser
        # ----------------------------------------------------

        try:

            async with self.page.expect_file_chooser(
                timeout=10000
            ) as chooser_info:

                await update_button.click(
                    force=True
                )

            chooser = await chooser_info.value

            await chooser.set_files(
                str(self.resume_path)
            )

        except PlaywrightTimeoutError:

            await self.page.wait_for_timeout(
                2000
            )

            file_inputs = self.page.locator(
                'input[type="file"]'
            )

            count = await file_inputs.count()

            if count == 0:

                raise RuntimeError(
                    "Naukri did not expose a "
                    "file chooser or file input."
                )

            uploaded = False

            for i in range(count):

                try:

                    await file_inputs.nth(
                        i
                    ).set_input_files(
                        str(self.resume_path)
                    )

                    uploaded = True

                    break

                except Exception:
                    pass

            if not uploaded:

                raise RuntimeError(
                    "Could not attach resume PDF."
                )

        # ----------------------------------------------------
        # Processing
        # ----------------------------------------------------

        await self.page.wait_for_timeout(
            5000
        )

        # ----------------------------------------------------
        # Confirmation
        # ----------------------------------------------------

        confirmation_selectors = [
            'button:has-text("Upload")',
            'button:has-text("Save")',
            '[role="button"]:has-text("Upload")',
            '[role="button"]:has-text("Save")',
        ]

        for selector in confirmation_selectors:

            try:

                buttons = self.page.locator(
                    selector
                )

                count = await buttons.count()

                for i in range(
                    count - 1,
                    -1,
                    -1,
                ):

                    button = buttons.nth(i)

                    if await button.is_visible(
                        timeout=500
                    ):

                        await button.click()

                        await self.page.wait_for_timeout(
                            5000
                        )

                        break

                else:
                    continue

                break

            except Exception:
                pass

        await self.page.wait_for_timeout(
            8000
        )

        # ----------------------------------------------------
        # Reload
        # ----------------------------------------------------

        await self.page.goto(
            Constants.PROFILE_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        await self.page.wait_for_timeout(
            5000
        )

        print(
            "Resume upload completed."
        )

    # ========================================================
    # VERIFY
    # ========================================================

    async def verify_resume(self):

        expected_name = (
            self.resume_path.name.lower()
        )

        expected_stem = (
            self.resume_path.stem.lower()
        )

        body_text = (
            await self.page
            .locator("body")
            .inner_text()
        ).lower()

        if expected_name in body_text:
            return True

        if expected_stem in body_text:
            return True

        return False