from typing import Dict, Any, List

class InfiniteTicTacToe:
    def __init__(self):
        """Инициализация игры."""
        self.board: Dict[str, str] = {}  # Храним только занятые клетки: {"row,col": symbol}
        self.current_player: str = "X"  # Первый ход за "X"

    def make_move(self, row: int, col: int) -> Dict[str, Any]:
        """Совершает ход в указанную клетку."""
        coord_str = f"{row},{col}"
        if coord_str in self.board:
            raise ValueError("Эта клетка уже занята!")

        self.board[coord_str] = self.current_player
        
        # Проверяем победу и получаем выигрышную линию
        win_info = self._check_winner_and_line(row, col)
        if win_info["is_win"]:
            return {"winner": self.current_player, "win_line": win_info["win_line"]}

        # Меняем игрока
        self.current_player = "O" if self.current_player == "X" else "X"
        return {"turn": self.current_player}  # Игра продолжается

    def get_board(self) -> Dict[str, str]:
        """Возвращает текущее состояние доски в формате { "row,col": symbol }."""
        return self.board

    def _check_winner_and_line(self, row: int, col: int) -> Dict[str, Any]:
        """
        Проверяет, есть ли победа после последнего хода и возвращает выигрышную линию.
        Возвращает: {"is_win": bool, "win_line": List[Dict[str, int]]}
        """
        player_symbol = self.board.get(f"{row},{col}")
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]  # Направления: (вниз, вправо, по диагонали вправо-вниз, по диагонали влево-вниз)

        for dr, dc in directions:
            # Считаем в одном направлении и в противоположном
            line1, count1 = self._count_in_direction_and_line(row, col, dr, dc, player_symbol) #pyright:ignore
            line2, count2 = self._count_in_direction_and_line(row, col, -dr, -dc, player_symbol) #pyright:ignore
            
            # Объединяем линии и убираем дубликаты (центральная клетка посчитана дважды)
            full_line_set = set(tuple(sorted(d.items())) for d in line1 + line2)
            full_line = [dict(t) for t in full_line_set] # Преобразуем обратно в список словарей

            if (count1 + count2 - 1) >= 5: # -1 потому что начальная клетка (row,col) посчитана дважды
                return {"is_win": True, "win_line": full_line}
        return {"is_win": False, "win_line": []}

    def _count_in_direction_and_line(self, row: int, col: int, dr: int, dc: int, symbol: str) -> tuple[List[Dict[str, int]], int]:
        """
        Считает количество одинаковых символов в одном направлении и возвращает клетки, входящие в линию.
        """
        count = 0
        r, c = row, col
        line_cells = []
        while self.board.get(f"{r},{c}") == symbol:
            count += 1
            line_cells.append({"x": r, "y": c})
            r += dr
            c += dc
        return line_cells, count