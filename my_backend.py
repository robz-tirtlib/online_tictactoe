from typing import List

from tictactoe import Game, GamePole

from my_exceptions import (InvalidMoveTypeError, CellIsUsedError,
                           EnemyTurnError, MoveOutOfBoundsError)


class DBInterface:

    def __init__(self, db) -> None:
        self.db = db

    def add_user(self, user_id: int):
        self.db.set(f"{user_id}:ready", user_id)

    def change_state_user(self, user_id: int, partner: int):
        self.remove_user(user_id)
        self.db.set(f"{user_id}:playing", partner)

    def remove_user(self, user_id: int):
        for key in self.db.keys(f"{user_id}*"):
            self.db.delete(key)

    def ready_users_count(self):
        return len(self.db.keys("*:ready"))

    def get_playing_users_ids(self) -> List[int]:
        return [int(key.split(':')[0]) for key in self.db.keys("*:playing")]

    def get_ready_users_ids(self) -> List[int]:
        return [int(key.split(':')[0]) for key in self.db.keys("*:ready")]

    def get_user_partner(self, user_id: int) -> int:
        return int(self.db.get(f"{user_id}:playing"))

    def get_pair_delete(self) -> List[int]:
        player1, player2 = self.db.keys("*:ready")[:2]

        for player in player1, player2:
            self.db.delete(player)

        player1, player2 = int(player1.split(":")[0]), int(player2.split(":")[0])

        return player1, player2


class Notifier:

    def __init__(self, bot):
        self.bot = bot

    def notify_start(self, user_id: int, partner: int, pole: str):
        """Notify pair game is started"""

        self.bot.send_message(
            user_id,
            f"Игра началась. Напарник - {partner}")

        self.bot.send_message(
            partner,
            f"Игра началась. Напарник - {user_id}")

        for user in user_id, partner:
            self.bot.send_message(user, pole)

    def notify_end(self, game: Game, draw: bool, game_winner):
        """
        Notify pair game is ended providing personal message
        with game's outcome
        """

        player1, player2 = game.players

        if draw:
            for user in player1, player2:
                self.bot.send_message(user, "Игра окончена ничьёй.")
            return

        game_loser = player1 if player1 != game_winner else player2

        self.bot.send_message(game_winner, "Игра окончена. Вы победили.")
        self.bot.send_message(game_loser, "Игра окончена. Вы проиграли.")

    def notify_move(self, user_id: int, partner: int, pole: GamePole):
        """Send pair new gamepole after move"""

        for user in user_id, partner:
            self.bot.send_message(user, pole)

    def notify_stop(self, user_id: int):
        """Notify user game is interrupted"""

        self.bot.send_message(user_id, "Игра прервана.")

    def notify_user_in_queue(self, user_id: int):
        """Notify user he is in queue"""

        self.bot.send_message(user_id, "Вы в очереди.")

    def notify_user_is_playing(self, user_id: int, partner: int):
        """Notify user he is in game with partner"""

        self.bot.send_message(
            user_id,
            f"Вы в игре с {partner}"
            )

    def notify_move_error(self, user_id: int, error: str):
        """Notify user there is an issue with his move"""

        self.bot.send_message(user_id, error)

    def notify_to_make_move(self, user_id: int):
        """Notify user to make move"""

        self.bot.send_message(user_id, "Сейчас ваш ход.")


class Back:

    def __init__(self, dbi: DBInterface, bot) -> None:
        self.dbi = dbi
        self.games = {}
        self.notifier = Notifier(bot)

    def register_user(self, user_id: int):
        """Add user to queue if he is not playing and notify state"""

        if self.user_is_ready(user_id):
            self.notifier.notify_user_in_queue(user_id)
        elif self.user_is_playing(user_id):
            self.notifier.notify_user_is_playing(
                user_id,
                self.get_user_partner(user_id)
                )
        else:
            self.dbi.add_user(user_id)
            self.notifier.notify_user_in_queue(user_id)

    def start_ready_users(self):
        """Launch games for ready user and notify"""

        while self.dbi.ready_users_count() > 1:
            player1, player2 = self.dbi.get_pair_delete()
            self.start_pair(player1, player2)

            self.create_game(player1, player2)
            game = self.game_by_user_id(player1)

            self.notifier.notify_start(player1, player2, game.get_pole())
            self.notifier.notify_to_make_move(game.turn)

    def start_pair(self, user1_id: int, user2_id: int):
        """Change states of users in DB"""

        self.dbi.change_state_user(user1_id, user2_id)
        self.dbi.change_state_user(user2_id, user1_id)

    def unregister_user(self, user_id: int):
        """Delete user from both ready and playing states"""
        self.dbi.remove_user(user_id)

    def create_game(self, user1_id: int, user2_id: int):
        """Create Game instance for pair"""

        self.games[f"{user1_id}:{user2_id}"] = Game(user1_id, user2_id)
        self.games[f"{user2_id}:{user1_id}"] = self.games[f"{user1_id}:{user2_id}"]

    def delete_game(self, user1_id: int, user2_id: int):
        """Delete Game instance of pair"""

        del self.games[f"{user1_id}:{user2_id}"]
        del self.games[f"{user2_id}:{user1_id}"]

    def user_interrupt(self, user_id: int):
        """Handle user interruption"""

        if self.user_is_playing(user_id):
            partner = self.get_user_partner(user_id)
            self.notifier.notify_stop(partner)
            self.unregister_user(partner)
        self.notifier.notify_stop(user_id)
        self.unregister_user(user_id)

    def check_game_for_end(self, user_id: int):
        """Check if someone has won or game has ended with draw"""

        game = self.game_by_user_id(user_id)

        if game.winner is None and not game.draw:
            return False

        if game.winner is not None:
            self.notifier.notify_end(game, False, game.winner)
        else:
            self.notifier.notify_end(game, True, None)

        partner = self.get_user_partner(user_id)
        self.delete_game(user_id, partner)
        self.unregister_user(user_id)
        self.unregister_user(partner)

        return True

    def user_move(self, user_id: int, move: str):
        """Try to make move, catch errors and notify user"""

        game = self.game_by_user_id(user_id)

        try:
            game.move(user_id, move)
        except (InvalidMoveTypeError, CellIsUsedError,
                EnemyTurnError, MoveOutOfBoundsError) as error:
            self.notifier.notify_move_error(user_id, error)
            return

        partner = self.get_user_partner(user_id)
        self.notifier.notify_move(
            user_id,
            partner,
            self.get_pole(user_id)
            )
        if not self.check_game_for_end(user_id):
            self.notifier.notify_to_make_move(partner)

    def game_by_user_id(self, user_id: int) -> Game:
        for pair, game in self.games.items():
            if str(user_id) in pair:
                return game

    def get_pole(self, user_id: int):
        partner = self.get_user_partner(user_id)
        return self.games[f"{user_id}:{partner}"].get_pole()

    def get_user_partner(self, user_id: int):
        return self.dbi.get_user_partner(user_id)

    def user_is_playing(self, user_id: int):
        return user_id in self.dbi.get_playing_users_ids()

    def user_is_ready(self, user_id: int):
        return user_id in self.dbi.get_ready_users_ids()
