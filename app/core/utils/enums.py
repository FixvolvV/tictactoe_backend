import enum

class roles(str, enum.Enum):
    USER = 'Пользователь'
    ADMIN = 'Администратор'

class lobbystage(str, enum.Enum):
    WAITING = 'Ожидание'
    ACTIVE = 'Активно'
    COMPLETED = 'Завершено'

class gametype(str, enum.Enum):
    INFINITY_TIC_TAC_TOE = "Бесконечные крестики нолики"

class ConnectionState(str, enum.Enum):
    WAITING = "waiting"
    READY = "ready"
    PLAYING = "playing"
    FINISHED = "finished"