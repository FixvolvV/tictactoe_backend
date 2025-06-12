from fastapi import APIRouter, Request, Security
from fastapi.responses import JSONResponse, StreamingResponse

import asyncio
import json

from pydantic import create_model

from src.scemas.user_scemas import User
from src.scemas.lobby_scemas import LobbyWithId

from src.routers.security import Authorization

from src.databaseM.methods.select_methods import get_all_users, get_user_by_id, get_all_lobbies

from src.utils.enums import lobbystage


"""
Роутер который отвечает на все попытки получения данных, для отрисовки приложения

Для этого мы используем API роутер что бы не засорять main файл.
"""

# Константы
MESSAGE_STREAM_DELAY = 3 #second

# Функция реализующая sse для вывода активных лобби
async def lobbies_stream():

    Model = create_model('Model', stage=(lobbystage, ...))
    filters = Model(stage=lobbystage.WAITING)

    last_lobbies = []

    while True:
        
        lobbies = await get_all_lobbies(filters=filters) #pyright: ignore
        validated_list = [LobbyWithId.model_validate(lobby) for lobby in lobbies]
        current_lobbies = [lobby.model_dump() for lobby in validated_list]

        if current_lobbies != last_lobbies:
            data = {"event": "update_lobbies", "data": current_lobbies}

            yield f"data: {json.dumps(data)}\n\n"
            last_lobbies = current_lobbies
            
        await asyncio.sleep(MESSAGE_STREAM_DELAY)


#Определение роутера
gets = APIRouter(prefix="/get")


#Получение глобальных данных сайта
@gets.get("/global", status_code=200)
async def get_globaldata(request: Request):

    Model = create_model('Model', stage=(lobbystage, ...))
    filters = Model(stage=lobbystage.ACTIVE)

    active_lobbies = await get_all_lobbies(filters=filters) #pyright: ignore
    all_lobbies = await get_all_lobbies(filters=None) #pyright: ignore

    return {"now":len(active_lobbies), "total":len(all_lobbies)}

# Получение списка лобби
@gets.get("/lobbylist", status_code=200)
async def get_lobbylist(request: Request, api_key: str = Security(Authorization)):
        
    return StreamingResponse(lobbies_stream(), media_type="text/event-stream")

#Получение собственных данных, для вывода на страницах
@gets.get("/self", status_code=200)
async def get_self_data(request: Request, api_key: str = Security(Authorization)):

    place: int = 0
    user_data: User = User.model_validate( await get_user_by_id(id=request.user.username) ) #pyright: ignore

    players_list = await get_all_users(filters=None) #pyright: ignore
    leaders_list = sorted(players_list, key=lambda player: player.games["wins"], reverse=True)

    for i in leaders_list:
        place += 1
        if str(i.id) == str(request.user.username):
            break

    return {"user_data": user_data.model_dump(exclude={"password"}), "leaders_place": place}

#Получение списка лидеров
@gets.get("/leaderslist", status_code=200)
async def get_leaderslist(request: Request, list_size: int = 50, api_key: str = Security(Authorization)):


    players_list = await get_all_users(filters=None) #pyright: ignore
    leaders_list = sorted(players_list, key=lambda player: player.games["wins"], reverse=True)[:list_size]
    validated_list = [User.model_validate(user) for user in leaders_list]


    return [user.model_dump(exclude={"password"}) for user in validated_list]

#Получение профиля игрока
@gets.get("/profile/{userid}")
async def get_userprofile(userid: str, request: Request, api_key: str = Security(Authorization)):
    
    place = 0

    try: 

        user_data: User = User.model_validate( await get_user_by_id(id=userid) ) #pyright: ignore

        players_list = await get_all_users(filters=None) #pyright: ignore
        leaders_list = sorted(players_list, key=lambda player: player.games["wins"], reverse=True)

        for i in leaders_list:
            place += 1
            if str(i.id) == str(userid):
                break

        return {"user_data": user_data.model_dump(exclude={"password"}), "leaders_place": place}

    except:
        return JSONResponse(status_code=404, content={"msg":"User not found"})