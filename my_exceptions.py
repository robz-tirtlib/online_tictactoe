class MoveError(Exception):
    """Base class for move related exceptions"""
    pass


class InvalidMoveTypeError(MoveError):
    """Exception raised if user's move type is incorrect"""

    def __init__(self, *args) -> None:
        self.message = "Ход прислан в некорректном виде."
        super().__init__(self.message)


class MoveOutOfBoundsError(MoveError):
    """Exception raised if user's move exceeds bounds of gamepole"""

    def __init__(self, *args) -> None:
        self.message = "Введены координаты не существующей клетки."
        super().__init__(self.message)


class CellIsUsedError(MoveError):
    """Exception raised if user tries to use already used cell"""

    def __init__(self, *args) -> None:
        self.message = "Клетка уже занята."
        super().__init__(self.message)


class EnemyTurnError(MoveError):
    """Exception raised if user tries to make move on opponents turn"""

    def __init__(self, *args) -> None:
        self.message = "Сейчас не ваш ход."
        super().__init__(self.message)
