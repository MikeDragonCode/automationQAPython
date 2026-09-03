import allure
import pytest

from clients.users.users_client import UsersClient
from clients.users.users_schema import CreateUserRequestSchema
from utils.fakers import get_random_email, get_random_username


@allure.epic("API")
@allure.feature("Users")
@pytest.mark.api
class TestUsers:

    @allure.title("Получение пользователя по id")
    def test_get_user(self, users_client: UsersClient):
        with allure.step("Запрашиваем пользователя с id=1"):
            user = users_client.get_user(user_id=1)

        with allure.step("Проверяем, что данные пользователя корректны"):
            assert user.id == 1
            assert "@" in user.email

    @allure.title("Получение несуществующего пользователя возвращает 404")
    def test_get_user_not_found(self, users_client: UsersClient):
        with allure.step("Запрашиваем заведомо несуществующего пользователя"):
            response = users_client.get_user_api(user_id=999)

        with allure.step("Проверяем статус-код ответа"):
            assert response.status_code == 404

    @allure.title("Создание пользователя")
    def test_create_user(self, users_client: UsersClient):
        request = CreateUserRequestSchema(
            name="QA Student",
            username=get_random_username(),
            email=get_random_email(),
        )

        with allure.step("Отправляем запрос на создание пользователя"):
            created_user = users_client.create_user(request)

        with allure.step("Проверяем, что вернулись переданные данные"):
            assert created_user.name == request.name
            assert created_user.username == request.username
            assert created_user.email == request.email
