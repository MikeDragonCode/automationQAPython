from playwright.sync_api import Page, expect


class BasePage:
    """
    Общая функциональность для всех страниц приложения: хранение объекта page,
    открытие страницы по URL, проверка текущего адреса.
    Конкретные страницы (RegistrationPage, DashboardPage, ...) наследуются от него.
    """

    def __init__(self, page: Page):
        self.page = page

    def open(self, url: str) -> None:
        self.page.goto(url)

    def check_current_url(self, expected_url: str) -> None:
        expect(self.page).to_have_url(expected_url)
