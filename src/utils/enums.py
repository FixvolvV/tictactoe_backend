import enum


class lobbystage(str, enum.Enum):
    WAITING = 'Ожидание'
    ACTIVE = 'Активно'
    COMPLETED = 'Завершено'

class winners(str, enum.Enum):
    NODEFINED = "No defined"
    DRAW = "Draw"
    PLAYER1 = "Игрок 1"
    PLAYER2 = "Игрок 2"