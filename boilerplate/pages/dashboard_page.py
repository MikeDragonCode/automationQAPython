from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class DashboardPage(BasePage):
    URL = "https://nikita-filonov.github.io/qa-automation-engineer-ui-course/#/dashboard"

    def __init__(self, page: Page):
        super().__init__(page)

        self.toolbar_title = page.locator("[data-testid='dashboard-toolbar-title-text']")

    def check_opened(self) -> None:
        self.check_current_url(self.URL)

    def check_visible_toolbar_title(self) -> None:
        expect(self.toolbar_title).to_be_visible()
        expect(self.toolbar_title).to_have_text("Dashboard")
