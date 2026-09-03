from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class RegistrationPage(BasePage):
    URL = "https://nikita-filonov.github.io/qa-automation-engineer-ui-course/#/auth/registration"

    def __init__(self, page: Page):
        super().__init__(page)

        self.email_input = page.locator("[data-testid='registration-form-email-input'] input")
        self.username_input = page.locator("[data-testid='registration-form-username-input'] input")
        self.password_input = page.locator("[data-testid='registration-form-password-input'] input")
        self.registration_button = page.locator("[data-testid='registration-page-registration-button']")

    def open_page(self) -> None:
        super().open(self.URL)

    def fill_registration_form(self, email: str, username: str, password: str) -> None:
        self.email_input.fill(email)
        self.username_input.fill(username)
        self.password_input.fill(password)

    def click_registration_button(self) -> None:
        self.registration_button.click()

    def check_visible_registration_form(self) -> None:
        expect(self.email_input).to_be_visible()
        expect(self.username_input).to_be_visible()
        expect(self.password_input).to_be_visible()
        expect(self.registration_button).to_be_visible()
