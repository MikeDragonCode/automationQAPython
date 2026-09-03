from pydantic import BaseModel, EmailStr


class GeoSchema(BaseModel):
    lat: str
    lng: str


class AddressSchema(BaseModel):
    street: str
    suite: str
    city: str
    zipcode: str
    geo: GeoSchema


class CompanySchema(BaseModel):
    name: str
    catchPhrase: str
    bs: str


class UserSchema(BaseModel):
    """
    Описание структуры пользователя из https://jsonplaceholder.typicode.com/users.
    """
    id: int
    name: str
    username: str
    email: EmailStr
    address: AddressSchema
    phone: str
    website: str
    company: CompanySchema


class CreateUserRequestSchema(BaseModel):
    """
    Описание структуры запроса на создание пользователя.
    JSONPlaceholder — фейковый REST API: запись реально не сохраняется,
    но эндпоинт валидно отвечает, что удобно для учебных тестов.
    """
    name: str
    username: str
    email: EmailStr


class CreateUserResponseSchema(BaseModel):
    """
    Описание структуры ответа на создание пользователя.
    """
    id: int
    name: str
    username: str
    email: EmailStr
