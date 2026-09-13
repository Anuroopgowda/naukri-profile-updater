import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Constants:


    BASE_DIR = Path(__file__).resolve().parent

    RESUME_DIR = BASE_DIR / "resumes"



    BASE_URL = "https://www.naukri.com/"

    PROFILE_URL = (
        "https://www.naukri.com/mnjuser/profile"
    )

    NAUKRI_EMAIL = os.getenv("NAUKRI_EMAIL")
    NAUKRI_PASSWORD = os.getenv("NAUKRI_PASSWORD")

    RESUME_PDF_PATH = Path(
        os.getenv(
            "RESUME_PDF_PATH",
            str(
                RESUME_DIR /
                "Anuroop_gowda_c_resume.pdf"
            ),
        )
    )

    NEW_HEADLINE = (
        "1.9 Yrs Software Engineer | "
        "Python FastAPI Backend | "
        "REST APIs Microservices Docker | "
        "PostgreSQL AWS | LLM & Automation | "
        "Bengaluru | 1 Month Notice"
    )


    BROWSER_WIDTH = 1280

    BROWSER_HEIGHT = 800

    HEADLESS = False