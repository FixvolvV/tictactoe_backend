


#Тут у нас чистейшая логика класса игры. 


class InfiniteTicTacToe:
    def __init__(self):
        """Инициализация игры."""
        self.board = {}  # Храним только занятые клетки
        self.current_player = "X"  # Первый ход за "X"

    def make_move(self, row, col):
        """Совершает ход в указанную клетку."""

        if f"{row},{col}" in self.board:
            raise ValueError("Эта клетка уже занята!")

        self.board[f"{row},{col}"] = self.current_player  # Записываем ход
        if self.check_winner(row, col):  # Проверяем победу
            return {"winner": self.current_player}  # Игра завершена

        self.current_player = "O" if self.current_player == "X" else "X"  # Меняем игрока
        return {"turn": self.current_player}  # Игра продолжается

    def get_board(self):
        """Возвращает значение доски."""
        return self.board

    def check_winner(self, row, col):
        """
        Проверяет, есть ли победа после последнего хода.
        Победа — это 5 символов в ряд (по горизонтали, вертикали или диагоналям).
        """
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]  # Варианты направлений (↓, →, ↘, ↙)

        for dr, dc in directions:
            if self.count_in_direction(row, col, dr, dc) + self.count_in_direction(row, col, -dr, -dc) - 1 >= 5:
                return True
        return False

    def count_in_direction(self, row, col, dr, dc):
        """
        Считает количество одинаковых символов в одном направлении.
        dr, dc — шаги по вертикали и горизонтали.
        """
        symbol = self.board.get(f"{row},{col}")
        count = 0
        r, c = row, col

        while self.board.get(f"{r},{c}") == symbol:
            count += 1
            r += dr
            c += dc

        return count