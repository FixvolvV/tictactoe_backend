from fastapi import APIRouter, Request, Security, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from typing import List, Dict

import json

import jwt

from src.utils.config import settings

from src.routers.security import Authorization

from src.scemas.user_scemas import User
from src.scemas.lobby_scemas import Lobby, LobbyWithId
from src.scemas.token_shemas import Token

from src.databaseM.methods.add_methods import add_one_lobby
from src.databaseM.methods.select_methods import get_lobby_by_id, get_user_by_id
from src.databaseM.methods.update_methods import update_lobbyplayers, update_lobbystage, update_lobbywinner, update_usergames

from src.utils.enums import lobbystage, winners

from src.logics.gameClass import InfiniteTicTacToe

"""
Файл отвечающий за за логику игровой части сайта в целом, он кооперирует все другие файлы


"""

CONF_JWT_DATA = Token.model_validate((settings.get_jwt_conf())) 

# КАКОЙ ЖЕ ЭТО ЛЮТЕЙШИЙ ГОВНОКОД ВЫ БЫ ЗНАЛИ. Я ОБЯЗАТЕЛЬНО ЭТО ПЕРЕПИШУ... КОГДА НИБУТЬ.
# Если кто сможет разобраться в нём, и дать дельные советы по его адаптации то я жду...
class GameManager:
    def __init__(self):
        self.game: InfiniteTicTacToe
        self.players = {}

    async def connect(self, websocket: WebSocket): # Обработка подключений

        await websocket.accept() # принимаем подключение

        if len(self.players) >= 2: # Гениальная проверка на заполненость лобби
            await websocket.send_json({"type": "Error", "message": "Лобби заполнено"})
            await websocket.close()

        # если всё норм...
        await websocket.send_json({"type": "Init", "message": "Успешно подключено"})

    # Проверка токена игрока
    async def auth(self, token, userid, websocket):

        if not token or not token.startswith("Bearer "): # Если токен не пришёл или не начинаеться с Bearer
            await websocket.send_json({"type":"Error", "message":"Не подтверждённое подключение"})
            await websocket.close()

        _token = token.split(" ")[1] #Получаем сам токен

        payload = jwt.decode(_token, CONF_JWT_DATA.token, algorithms=[CONF_JWT_DATA.token_type]) # Декод, и получение айди пользователя
        userid = payload.get("id")

        if (not userid) or (userid != userid): # Если токен не раскодирован верно, или юзернем не совпадает
            await websocket.send_json({"type":"Error", "message":"Не подтверждённое подключение"})
            await websocket.close()

        if len(self.players) != 0: # Если вдруг один и тот же игрок решит зайти мы его опрокидываем...
            if self.players["X"]["user_id"] == userid:
                await websocket.send_json({"type":"Error", "message":"Вы уже есть в лобби"})
                await websocket.close()

        # Если всё норм
        await websocket.send_json({"type":"Auth", "message": "Подключение защищено"})

        return True

    # Стадия инициализации игры. МОЛИТЕСЬ!!!
    async def stateInit(self, user_data, lobby_id: str, websocket: WebSocket):

        playernumber = ""

        await self.auth(user_data['token'], user_data['user_id'], websocket) # Тут короче аунтифекация, дл проверки валидности игрока

        # Далее if для того что бы занести данные игроков в список, для лучшей их обработки + Сохраняем вебсокет что бы не убежал
        if len(self.players) < 1: # это для крестика
            playernumber = "player1"
            await websocket.send_json({"type":"Init", "symbol": "X"})
            self.players["X"] = {"user_id":user_data['user_id'], "username":user_data['username'], "wins":user_data['wins'], "connect": websocket}

        elif len(self.players) == 1: # а это для нолика
            playernumber = "player2"
            await websocket.send_json({"type":"Init", "symbol": "O"})
            self.players["O"] = {"user_id":user_data['user_id'], "username":user_data['username'], "wins":user_data['wins'], "connect": websocket}

        # Это работа с базой данных, ДА Я ЗНАЮ ЭТО КРИНЖ ЗАНОСИТЬ ДИНАМИЧЕСКИЕ ОБЪЕКТЫ В БАЗУ. НЕ ЗАДАВАЙТЕ ВОПРОСОВ
        lobby: LobbyWithId = LobbyWithId.model_validate( await get_lobby_by_id(id=lobby_id) ) #pyright:ignore
        data = lobby.players
        data[playernumber] = user_data['user_id']
        await update_lobbyplayers(lobby_id=lobby_id, newvalues=data) #pyright:ignore

        # Бродкаст данных всем. Что бы все всё знали...
        for conn in self.players:
            connect = self.players[conn]['connect']
            await connect.send_json({"type":"Init", "data": dict({key: {k: v for k, v in value.items() if k != "connect"} for key, value in self.players.items()})})

        #Тут же и заинитим саму игру, классный код да?
        if len(self.players) == 2:

            self.game = InfiniteTicTacToe()
            await update_lobbystage(lobby_id=lobby_id, newstage=lobbystage.ACTIVE) #pyright:ignore

            for conn in self.players:
                connect = self.players[conn]['connect']

                if conn == 'X':
                    await connect.send_json({"type":"Active", "turn": True})
                    continue

                await connect.send_json({"type":"Active", "turn": False})

    #Функция самой игры... СТРАДАНИЕ ПРОДОЛЖАЕТЬСЯ АХХАХАХАХАХХАХАХАХАХХА
    async def stateActive(self, turn_data, lobby_id: str, websocket: WebSocket):

        current_player = {}
        #Зафиксируем ход и отправим данные обратно.
        try:

            current_player = self.game.make_move(turn_data['row'], turn_data['col']) #ddd

            if "winner" in current_player:
                for conn in self.players:
                    connect = self.players[conn]['connect']
                    await connect.send_json({"type":"Active", "board": self.game.get_board(), "turn": False})

                await self.stateEnd(current_player['winner'], lobby_id)

            if "turn" in current_player: # ну тут мы отправляем обновлённое поле, и переназначаем ходы игроков. СЛОЖНА СЛОЖНА
                for conn in self.players:
                    connect = self.players[conn]['connect']

                    if conn == current_player['turn']:
                        await connect.send_json({"type":"Active", "board": self.game.get_board(), "turn": True})
                        continue

                    await connect.send_json({"type":"Active", "board": self.game.get_board(), "turn": False})
                
                return

        except ValueError as e:
            await websocket.send_json({"type": "Warning", "message": str(e)})
            return

    async def set_lobbywinner(self, lobby_id, symbol):
        await update_lobbystage(lobby_id=lobby_id, newstage=lobbystage.COMPLETED) #pyright:ignore

        if symbol == "X":
            await update_lobbywinner(lobby_id=lobby_id, winner=winners.PLAYER1) #pyright:ignore
        elif symbol == "O":
            await update_lobbywinner(lobby_id=lobby_id, winner=winners.PLAYER2) #pyright:ignore

    async def winner_awarding(self, winner):
        user: User = User.model_validate( await get_user_by_id(id=winner['user_id']) ) #pyright:ignore
        data = user.games
        data['total'] += 1
        data['wins'] += 1
        await update_usergames(user_id=winner['user_id'], newvalues=data) #pyright:ignore

    async def loser_awarding(self, loser):
        user: User = User.model_validate( await get_user_by_id(id=loser['user_id']) ) #pyright:ignore
        data = user.games
        data['total'] += 1
        data['loses'] += 1

        await update_usergames(user_id=loser['user_id'], newvalues=data) #pyright:ignore

    async def stateEnd(self, winner, lobby_id: str):

        await self.set_lobbywinner(lobby_id, winner)

        for player in self.players:
            await self.players[player]['connect'].send_json({"type":"Complete", "message": f"Игрок {self.players[winner]['username']} победил"})

        player = self.players.pop(winner)
        await self.winner_awarding(player)
        await player['connect'].close()

        player = self.players.pop( list( self.players.keys() )[-1] ) 
        await self.loser_awarding(player)
        await player['connect'].close()

        #CАМОУНИЧТОЖЕНИЕ ЧЕРЕЗ 3.. 2.. 1.. БУУУУУУУУУУУУУМ
        del self.game 
        del active_lobbies[lobby_id]

    async def disconnect(self, lobby_id: str, websocket: WebSocket): #Да Я ПРОСТО ВЗЯЛ ФУНКЦИЮ ВЫШЕ ВСТАВИЛ СЮДА И УДАЛИЛ ОДНУ СТРОЧКУ. А ЧЁ ВЫ МНЕ СДЕЛАЕТЕ?

        player = {}
        winner = ""

        for conn in self.players:
            if self.players[conn]['connect'] != websocket:
                winner = conn
                player = self.players.pop(conn)
                break

        await self.set_lobbywinner(lobby_id, winner)

        print(player)

        await player['connect'].send_json({"type":"Complete", "message": f"Игрок {player['username']} победил"})
        await self.winner_awarding(player)
        await player['connect'].close()

        player = self.players.pop( list( self.players.keys() )[-1] ) 

        print(player)

        await self.loser_awarding(player)

        #CАМОУНИЧТОЖЕНИЕ ЧЕРЕЗ 3.. 2.. 1.. БУУУУУУУУУУУУУМ
        del self.game 
        del active_lobbies[lobby_id]

active_lobbies: Dict[str, GameManager] = {}

game = APIRouter(prefix="/game")


@game.post("/createlobby")
async def createlobby(lobby_name: str, request: Request, api_key: str = Security(Authorization)):

    lobby: Lobby = Lobby(lobbyname=lobby_name, stage=lobbystage.WAITING, winner=winners.NODEFINED)

    lobby_id = await add_one_lobby(lobby_data=lobby) #pyright:ignore

    return lobby_id


@game.websocket("/{lobby_id}")
async def connect_to_gamesession(lobby_id: str, websocket: WebSocket):

    print(active_lobbies)

    lobby: LobbyWithId = await get_lobby_by_id(id=lobby_id) #pyright:ignore

    if not lobby or lobby.stage == lobbystage.COMPLETED: #pyright:ignore
        await websocket.accept()
        await websocket.send_json({"type":"Error", "message":"Такого лобби нет, или игра там закончена"})
        await websocket.close()
        return 
    
    if not (lobby_id in active_lobbies):
        active_lobbies[lobby_id] = GameManager()

    manager = active_lobbies[lobby_id]

    await manager.connect(websocket)
    try:
        while True:

            data = json.loads(await websocket.receive_text())

            if data['type'] == "Init":

                await manager.stateInit(data, lobby_id, websocket)

            if data['type'] == "Active":

                await manager.stateActive(data, lobby_id, websocket)

    except WebSocketDisconnect:
        await manager.disconnect(lobby_id, websocket)
    
    except KeyError:
        return


