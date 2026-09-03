import allure
import pytest

from pages.dashboard_page import DashboardPage
from pages.registration_page import RegistrationPage


@allure.epic("UI")
@allure.feature("Registration")
@pytest.mark.ui
class TestRegistration:

    @allure.title("Успешная регистрация нового пользователя")
    def test_successful_registration(
            self,
            user_data: dict[str, str],
            registration_page: RegistrationPage,
            dashboard_page: DashboardPage,
    ):
        with allure.step("Открываем страницу регистрации"):
            registration_page.open_page()
            registration_page.check_visible_registration_form()

        with allure.step("Заполняем форму и регистрируемся"):
            registration_page.fill_registration_form(**user_data)
            registration_page.click_registration_button()

        with allure.step("Проверяем, что попали на Dashboard"):
            dashboard_page.check_opened()
            dashboard_page.check_visible_toolbar_title()
