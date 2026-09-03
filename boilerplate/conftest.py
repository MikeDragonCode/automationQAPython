import allure
import pytest
from playwright.sync_api import Page

from clients.users.users_client import UsersClient, get_users_client
from pages.dashboard_page import DashboardPage
from pages.registration_page import RegistrationPage
from utils.fakers import get_random_email, get_random_password, get_random_username


# --- UI-фикстуры (модуль 4) ---

@pytest.fixture
def user_data() -> dict[str, str]:
    return {
        "email": get_random_email(),
        "username": get_random_username(),
        "password": get_random_password(),
    }


@pytest.fixture
def registration_page(page: Page) -> RegistrationPage:
    return RegistrationPage(page)


@pytest.fixture
def dashboard_page(page: Page) -> DashboardPage:
    return DashboardPage(page)


# --- API-фикстуры (модуль 3) ---

@pytest.fixture(scope="session")
def users_client() -> UsersClient:
    return get_users_client()


# --- Allure: скриншот при падении UI-теста (модуль 5) ---

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        page: Page | None = item.funcargs.get("page")
        if page is not None:
            allure.attach(
                page.screenshot(),
                name="screenshot-on-failure",
                attachment_type=allure.attachment_type.PNG,
            )
