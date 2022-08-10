from my_exceptions import (InvalidMoveTypeError, CellIsUsedError,
                           EnemyTurnError, MoveOutOfBoundsError)


class Player:

    def __init__(self, user_id: int, sign: str):
        self.id = user_id
        self.sign = sign


class GamePole:

    def __init__(self):
        self.init_pole()

    def init_pole(self):
        self.pole = [
            ['.', '1', '2', '3'],
            ['1', '_', '_', '_'],
            ['2', '_', '_', '_'],
            ['3', '_', '_', '_'],
        ]

    def get_pole(self):
        return '\n'.join([' '.join(row) for row in self.pole])

    def cell_is_free(self, x: int, y: int):
        return self.pole[y][x] == '_'

    def get_winner(self, player1: Player, player2: Player):

        for player in player1, player2:
            sign = player.sign

            # rows and cols
            for i in range(1, 4):
                if (self.pole[i][1] == self.pole[i][2] == self.pole[i][3] == sign or
                        self.pole[1][i] == self.pole[2][i] == self.pole[3][i] == sign):
                    return player.id

            # diagonals
            if self.pole[1][1] == self.pole[2][2] == self.pole[3][3] == sign:
                return player.id

            if self.pole[1][3] == self.pole[2][2] == self.pole[3][1] == sign:
                return player.id

        return None

    def check_draw(self):
        if not any(['_' in row for row in self.pole]):
            return True
        return False


class Game:

    def __init__(self, user1_id: int, user2_id: int):
        self.gamepole = GamePole()
        self.players = {
            user1_id: Player(user1_id, 'x'),
            user2_id: Player(user2_id, 'o')
        }
        self.turn = user1_id
        self.winner = None
        self.draw = False

    def move(self, user_id: int, move: str):
        self.__validate_move(user_id, move)
        y, x = map(int, list(move))
        self.__make_move(user_id, x, y)
        self.__switch_turn()
        self.__check_game_for_end()

    def get_pole(self):
        return self.gamepole.get_pole()

    def __check_game_for_end(self):
        self.winner = self.gamepole.get_winner(*self.players.values())
        self.draw = self.gamepole.check_draw()

    def __validate_move(self, user_id: int, move: str):
        self.__check_turn(user_id)
        self.__validate_move_type(move)
        y, x = map(int, list(move))
        self.__validate_move_bounds(x, y)
        self.__validate_cell_availability(x, y)

    def __validate_move_bounds(self, x: int, y: int):
        if not all([1 <= x <= 3, 1 <= y <= 3]):
            raise MoveOutOfBoundsError

    def __validate_move_type(self, move: str):
        if len(move) != 2 or not move.isdigit():
            raise InvalidMoveTypeError

    def __validate_cell_availability(self, x: int, y: int):
        if not self.gamepole.cell_is_free(x, y):
            raise CellIsUsedError

    def __make_move(self, user_id: int, x: int, y: int):
        self.gamepole.pole[y][x] = self.players[user_id].sign

    def __check_turn(self, user_id: int):
        if self.turn != user_id:
            raise EnemyTurnError

    def __switch_turn(self):
        player1, player2 = self.players.values()
        self.turn = player1.id if self.turn == player2.id else player2.id
