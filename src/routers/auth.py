import json
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from starlette.responses import Content

from src.scemas.user_scemas import UserOnlyUsername, UserOnlyDataAuth, User, UserOnlyUP
from src.scemas.token_shemas import Token

from src.databaseM.methods.add_methods import add_one_user
from src.databaseM.methods.select_methods import get_user_by_id, get_user_by_username

from src.utils.hashing import get_password_hash, verify_password
from src.utils.jwt import get_access_token

"""
Роутер который отвечает на все попытки аутентификации и авторизации на сайте

Для этого мы используем API роутер что бы не засорять main файл.
"""

# Определение роутера
authe = APIRouter(prefix="/auth")

#path регистрации сюда приходят данные пользователей с приложения, которые хотят зарегистрироваться.
@authe.post('/register')
async def get_register_data(userdata: UserOnlyUP): # Оборачиваем в схему User от Pydantic

    register_exception = JSONResponse(
            status_code=401,
            content=f"{userdata.username} уже используеться",
            headers={"Authorization": "Bearer"}
        )
    #Проверка никнейма на наличие в BD (Да да ник уникален)

    if await get_user_by_username(filters=UserOnlyUsername(username=userdata.username)): #pyright: ignore
        return register_exception

    #Хеш пароля, Добавление в датабазу
    #P.S. pyright:ignore это норма :)
    hashed_userdata: User = User.model_validate(userdata.model_copy(update={"password": get_password_hash(userdata.password) }))
    user_id = await add_one_user(user_data=hashed_userdata) #pyright:ignore 

    #Dыдача JWT токена для авторизации
    user: UserOnlyDataAuth = UserOnlyDataAuth.model_validate(await get_user_by_id(id=user_id)) #pyright:ignore
    token: Token = get_access_token(user)

    return JSONResponse(status_code=200, content={"msg": "OK", "token_data": token.model_dump(), "user": user.id}, headers={"Authorization": "Bearer"})

#path аунтификации сюда приходят данные пользователей с приложения, которые хотят залогиниться.
@authe.post('/login')
async def get_login_data(userdata: UserOnlyUP): # Оборачиваем в схему User от Pydantic
 
    # Создадим переменную с ошибкой, что бы было удобнее использовать дальше
    auth_exception = JSONResponse(
                status_code=401,
                content="Incorrect username or password",
                headers={"Authorization": "Bearer"},
            )

        # Пытался максимально сократить код, поэтому тут блок try..except. Пытаемся закрузить пользователя, и если его в датабазе нету то вылетает ошибка
    try: 
        _userdataDB: UserOnlyDataAuth = UserOnlyDataAuth.model_validate (
            await get_user_by_username (
                filters=UserOnlyUsername (
                    username=userdata.username
                )
            ) #pyright: ignore 
        )
    except:
        return auth_exception

    # Проверяем верность введённого пароля
    if not verify_password(userdata.password, _userdataDB.password):
        return auth_exception

    # Выдача JWT токена для авторизации
    token: Token = get_access_token(_userdataDB)
    
    return JSONResponse(status_code=200, content={"msg": "OK", "token_data": token.model_dump(), "user": _userdataDB.id}, headers={"Authorization": "Bearer"})
