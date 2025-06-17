import enum

class roles(str, enum.Enum):
    USER = 'Пользователь'
    ADMIN = 'Администратор'

class gametype(str, enum.Enum):
    INFINITY_TIC_TAC_TOE = "Infinity Tic Tac Toe"

class connectionstate(str, enum.Enum):
    WAITING = "waiting"
    READY = "ready"
    PLAYING = "playing"
    FINISHED = "finished"