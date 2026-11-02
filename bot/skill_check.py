
import secrets
import uuid
from urllib.parse import urlencode

from telegram import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo


class SkillCheck:
    DIRECTIONS = {"UP", "DOWN", "LEFT", "RIGHT"}

    def __init__(self, game_url, config):
        self.game_url = game_url.rstrip("/")
        self.config = config

        # Desafios pendentes por usuário e identificador.
        self.pending_challenges = {}

    def _url(self, params):
        """
        Monta a URL do Mini App com os parâmetros do desafio.
        """
        return f"{self.game_url}/?{urlencode(params)}"

    def _sequence_button(
        self,
        user_id,
        length=None,
        time_limit=None
    ):
        """
        Cria um desafio de sequência e retorna o botão do Telegram.
        """

        if length is None:
            length = self.config["sequence_length"]

        if time_limit is None:
            time_limit = self.config["sequence_time_limit"]

        if (
            isinstance(length, bool)
            or not isinstance(length, int)
            or not 1 <= length <= 100
        ):
            raise ValueError(
                "O tamanho da sequência deve estar entre 1 e 100."
            )

        if (
            isinstance(time_limit, bool)
            or not isinstance(time_limit, int)
            or not 1 <= time_limit <= 3600000
        ):
            raise ValueError(
                "O tempo deve estar entre 1 e 3600000 milissegundos."
            )

        directions = ("UP", "DOWN", "LEFT", "RIGHT")

        # A sequência é criada exclusivamente no servidor.
        sequence = [
            secrets.choice(directions)
            for _ in range(length)
        ]

        challenge_id = uuid.uuid4().hex

        # Guarda os dados originais para validação posterior.
        self.pending_challenges[(user_id, challenge_id)] = {
            "sequence": sequence,
            "time_limit": time_limit,
        }

        params = {
            "method": "sequence",
            "sequence": ",".join(sequence),
            "challenge_id": challenge_id,
            "time_limit": time_limit,
        }

        url = self._url(params)

        return KeyboardButton(
            text="Teste de sequência",
            web_app=WebAppInfo(url=url)
        )

    def keyboard(
        self,
        user_id,
        minimum=None,
        maximum=None,
        sequence_length=None,
        sequence_time_limit=None
    ):
        """
        Cria o teclado principal com os dois testes.
        """

        if minimum is None:
            minimum = self.config["number_min"]

        if maximum is None:
            maximum = self.config["number_max"]

        if (
            isinstance(minimum, bool)
            or not isinstance(minimum, int)
            or isinstance(maximum, bool)
            or not isinstance(maximum, int)
        ):
            raise ValueError("O intervalo numérico precisa usar inteiros.")

        if minimum > maximum:
            raise ValueError(
                "O valor mínimo não pode ser maior que o máximo."
            )

        number_params = {
            "method": "number",
            "minimum": minimum,
            "maximum": maximum,
        }

        number_url = self._url(number_params)

        number_button = KeyboardButton(
            text="Teste básico",
            web_app=WebAppInfo(url=number_url)
        )

        sequence_button = self._sequence_button(
            user_id=user_id,
            length=sequence_length,
            time_limit=sequence_time_limit
        )

        keyboard = [
            [number_button],
            [sequence_button],
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            is_persistent=True
        )

    def validate_sequence_result(self, user_id, data):
        """
        Valida o resultado do teste de sequência.

        O servidor não confia nos contadores enviados pelo navegador.
        Ele recalcula acertos e erros usando a sequência original.

        Uma entrada incorreta soma um erro, mas não avança o índice.
        Uma entrada correta soma um acerto e avança o índice.
        """

        if not isinstance(data, dict):
            return {
                "valid": False,
                "message": "Dados do desafio inválidos."
            }

        challenge_id = data.get("challenge_id")

        if (
            not isinstance(challenge_id, str)
            or not challenge_id
            or len(challenge_id) > 100
        ):
            return {
                "valid": False,
                "message": "Identificador do desafio inválido."
            }

        challenge_key = (user_id, challenge_id)

        challenge = self.pending_challenges.get(challenge_key)

        if challenge is None:
            return {
                "valid": False,
                "message": "Desafio não encontrado ou já utilizado."
            }

        # Verifica a estrutura básica antes de consumir o desafio.
        inputs = data.get("inputs")
        time_ms = data.get("time_ms")

        if not isinstance(inputs, list):
            return {
                "valid": False,
                "message": "Lista de entradas inválida."
            }

        if len(inputs) > 10000:
            return {
                "valid": False,
                "message": "Quantidade de entradas excede o limite."
            }

        if (
            isinstance(time_ms, bool)
            or not isinstance(time_ms, int)
        ):
            return {
                "valid": False,
                "message": "Tempo informado inválido."
            }

        time_limit = challenge["time_limit"]

        if time_ms < 0 or time_ms > time_limit:
            return {
                "valid": False,
                "message": "Tempo informado fora do limite do desafio."
            }

        if any(
            not isinstance(direction, str)
            or direction not in self.DIRECTIONS
            for direction in inputs
        ):
            return {
                "valid": False,
                "message": "Uma ou mais direções são inválidas."
            }

        expected = challenge["sequence"]

        # Reproduz a lógica do jogo no servidor.
        index = 0
        hits = 0
        errors = 0

        for direction in inputs:

            # Não aceita entradas adicionais depois de completar
            # toda a sequência.
            if index >= len(expected):
                return {
                    "valid": False,
                    "message": "Foram recebidas entradas após a conclusão."
                }

            if direction == expected[index]:
                hits += 1
                index += 1
            else:
                errors += 1

        completed = index == len(expected)

        attempts = hits + errors

        accuracy = (
            (hits / attempts) * 100
            if attempts > 0
            else 0
        )

        # Confere os campos enviados pelo cliente, quando presentes.
        client_hits = data.get("hits")
        client_errors = data.get("errors")
        client_attempts = data.get("attempts")
        client_completed = data.get("completed")

        if (
            client_hits is not None
            and (
                isinstance(client_hits, bool)
                or not isinstance(client_hits, int)
                or client_hits != hits
            )
        ):
            return {
                "valid": False,
                "message": "Contagem de acertos inconsistente."
            }

        if (
            client_errors is not None
            and (
                isinstance(client_errors, bool)
                or not isinstance(client_errors, int)
                or client_errors != errors
            )
        ):
            return {
                "valid": False,
                "message": "Contagem de erros inconsistente."
            }

        if (
            client_attempts is not None
            and (
                isinstance(client_attempts, bool)
                or not isinstance(client_attempts, int)
                or client_attempts != attempts
            )
        ):
            return {
                "valid": False,
                "message": "Quantidade de tentativas inconsistente."
            }

        if (
            client_completed is not None
            and (
                not isinstance(client_completed, bool)
                or client_completed != completed
            )
        ):
            return {
                "valid": False,
                "message": "Estado de conclusão inconsistente."
            }

        # O motivo também precisa ser compatível com o resultado.
        reason = data.get("reason")

        if reason is not None:
            if reason not in ("success", "timeout"):
                return {
                    "valid": False,
                    "message": "Motivo de encerramento inválido."
                }

            if reason == "success" and not completed:
                return {
                    "valid": False,
                    "message": "Desafio marcado como concluído sem completar a sequência."
                }

            if reason == "timeout" and completed:
                return {
                    "valid": False,
                    "message": "Desafio concluído foi enviado como tempo esgotado."
                }

        # Só consome o desafio depois da validação.
        # Assim, um payload inválido não inutiliza o desafio.
        self.pending_challenges.pop(challenge_key, None)

        return {
            "valid": True,
            "success": completed,
            "completed": completed,
            "total": len(expected),
            "hits": hits,
            "errors": errors,
            "attempts": attempts,
            "accuracy": round(accuracy, 2),
            "time_ms": time_ms,
            "reason": reason or (
                "success" if completed else "timeout"
            ),
        }
