from requests import Response

from clients.api_client import APIClient, build_http_session
from clients.users.users_schema import (
    CreateUserRequestSchema,
    CreateUserResponseSchema,
    UserSchema,
)

BASE_URL = "https://jsonplaceholder.typicode.com"


class UsersClient(APIClient):
    """
    Клиент для работы с /users публичного демо-API JSONPlaceholder.
    """

    def get_users_api(self) -> Response:
        return self.get("/users")

    def get_user_api(self, user_id: int) -> Response:
        return self.get(f"/users/{user_id}")

    def create_user_api(self, request: CreateUserRequestSchema) -> Response:
        return self.post("/users", json=request.model_dump())

    def delete_user_api(self, user_id: int) -> Response:
        return self.delete(f"/users/{user_id}")

    def get_user(self, user_id: int) -> UserSchema:
        response = self.get_user_api(user_id)
        return UserSchema.model_validate_json(response.text)

    def create_user(self, request: CreateUserRequestSchema) -> CreateUserResponseSchema:
        response = self.create_user_api(request)
        return CreateUserResponseSchema.model_validate_json(response.text)


def get_users_client() -> UsersClient:
    """
    Собирает готовый к использованию UsersClient с настроенной HTTP-сессией.
    """
    return UsersClient(session=build_http_session(base_url=BASE_URL))
