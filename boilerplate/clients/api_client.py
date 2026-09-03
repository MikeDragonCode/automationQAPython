from typing import Any

import requests
from requests import Response, Session


class BaseUrlSession(Session):
    """
    requests.Session не умеет работать с base_url "из коробки" (в отличие от httpx.Client).
    Этот небольшой класс добавляет такое поведение: во все запросы подставляется base_url,
    а тесты/клиенты дальше работают только с относительными путями.
    """

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, url: str | bytes, *args: Any, **kwargs: Any) -> Response:
        full_url = f"{self.base_url}/{str(url).lstrip('/')}"
        return super().request(method, full_url, *args, **kwargs)


class APIClient:
    """
    Базовый API-клиент. Инкапсулирует транспорт (requests.Session) и даёт
    единый интерфейс HTTP-методов, на основе которого строятся все специализированные
    клиенты (UsersClient, PostsClient и т. д.).
    """

    def __init__(self, session: Session):
        self.session = session

    def get(self, url: str, params: dict | None = None) -> Response:
        return self.session.get(url, params=params)

    def post(
            self,
            url: str,
            json: Any | None = None,
            data: Any | None = None,
            files: Any | None = None,
    ) -> Response:
        return self.session.post(url, json=json, data=data, files=files)

    def put(self, url: str, json: Any | None = None) -> Response:
        return self.session.put(url, json=json)

    def patch(self, url: str, json: Any | None = None) -> Response:
        return self.session.patch(url, json=json)

    def delete(self, url: str) -> Response:
        return self.session.delete(url)


def build_http_session(base_url: str, timeout: int = 10) -> Session:
    """
    Собирает готовую к работе сессию: base_url + таймаут по умолчанию для всех запросов.
    """
    session = BaseUrlSession(base_url=base_url)
    session.request = _with_default_timeout(session.request, timeout)
    return session


def _with_default_timeout(request_func, timeout: int):
    def wrapper(method: str, url: str, *args: Any, **kwargs: Any) -> Response:
        kwargs.setdefault("timeout", timeout)
        return request_func(method, url, *args, **kwargs)

    return wrapper
