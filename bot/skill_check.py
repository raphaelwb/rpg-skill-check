
import secrets
import uuid
from urllib.parse import urlencode

from telegram import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo


class SkillCheck:
    def __init__(self, game_url, config):
        self.game_url = game_url.rstrip("/")
        self.config = config
        self.pending_challenges = {}

    def _url(self, params):
        return f"{self.game_url}/?{urlencode(params)}"

    def _sequence_button(self, user_id, length=None, time_limit=None):
        length = length or self.config["sequence_length"]
        time_limit = time_limit or self.config["sequence_time_limit"]
        display_time = self.config["sequence_display_time"]

        symbols = ["UP", "DOWN", "LEFT", "RIGHT"]
        sequence = [secrets.choice(symbols) for _ in range(length)]
        challenge_id = uuid.uuid4().hex

        self.pending_challenges[(user_id, challenge_id)] = {
            "sequence": sequence,
            "time_limit": time_limit,
        }

        url = self._url({
            "method": "sequence",
            "sequence": ",".join(sequence),
            "challenge_id": challenge_id,
            "display_time": display_time,
            "time_limit": time_limit,
        })

        return KeyboardButton(
            "Teste de sequência",
            web_app=WebAppInfo(url=url)
        )

    def keyboard(
        self,
        user_id,
        minimum=None,
        maximum=None,
        sequence_length=None,
        sequence_time_limit=None,
    ):
        minimum = (
            self.config["number_min"]
            if minimum is None else minimum
        )
        maximum = (
            self.config["number_max"]
            if maximum is None else maximum
        )

        number_url = self._url({
            "method": "number",
            "minimum": minimum,
            "maximum": maximum,
        })

        number_button = KeyboardButton(
            "Teste básico",
            web_app=WebAppInfo(url=number_url)
        )

        sequence_button = self._sequence_button(
            user_id,
            length=sequence_length,
            time_limit=sequence_time_limit,
        )

        return ReplyKeyboardMarkup(
            [[number_button], [sequence_button]],
            resize_keyboard=True,
            is_persistent=True,
        )

    def validate_sequence_result(self, user_id, data):
        challenge_id = data.get("challenge_id")
        key = (user_id, challenge_id)

        challenge = self.pending_challenges.pop(key, None)

        if challenge is None:
            return {
                "valid": False,
                "message": "Desafio inexistente ou já utilizado.",
            }

        expected = challenge["sequence"]
        inputs = data.get("inputs")
        time_ms = data.get("time_ms")
        time_limit = challenge["time_limit"]

        if not isinstance(inputs, list):
            return {"valid": False, "message": "Entradas inválidas."}

        if not isinstance(time_ms, int) or isinstance(time_ms, bool):
            return {"valid": False, "message": "Tempo inválido."}

        if time_ms < 0 or time_ms > time_limit:
            return {"valid": False, "message": "Tempo fora do limite."}

        if len(inputs) > len(expected):
            return {"valid": False, "message": "Quantidade de entradas inválida."}

        valid_symbols = {"UP", "DOWN", "LEFT", "RIGHT"}
        if not all(item in valid_symbols for item in inputs):
            return {"valid": False, "message": "Símbolos inválidos."}

        completed = 0
        for actual, wanted in zip(inputs, expected):
            if actual != wanted:
                break
            completed += 1

        success = (
            inputs == expected
            and len(inputs) == len(expected)
        )

        return {
            "valid": True,
            "success": success,
            "completed": completed,
            "total": len(expected),
            "time_ms": time_ms,
        }
