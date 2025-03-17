import jwt
from jwt.exceptions import PyJWTError

from pydantic import BaseModel

from src.utils.config import settings

from src.scemas.token_shemas import Token



"""
Здесь я писал методы для генерации, получения и проверки токена JWT.
Убийственный код.

"""


# Сохраняем данные полученные с конфига в Pydantic схему Token предназначенную для токенов юзеров.
CONF_JWT_DATA = Token.model_validate((settings.get_jwt_conf())) 

# Функция создания токена. Всё крайне просто. Создаётся бесконечный токен.
def create_access_token(user_data: dict):  
    to_encode = user_data.copy()
    encoded_jwt = jwt.encode(to_encode, CONF_JWT_DATA.token, algorithm=CONF_JWT_DATA.token_type)
    return encoded_jwt

# Тута мы инициализируем токен. Так скажем обвёртываем его в красивую оболочку Pydantic и схемы Token и отдаем.
def get_access_token(data: BaseModel):
    token = create_access_token(data.model_dump(include={'id'}))
    return Token(token=token, token_type="bearer")
