from uuid import uuid4

from faker import Faker

fake = Faker()


def get_random_email() -> str:
    return f"{uuid4()}.{fake.email()}"


def get_random_username() -> str:
    return fake.user_name()


def get_random_password(length: int = 12) -> str:
    return fake.password(length=length)
