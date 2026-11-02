
import json
import logging
import os

from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from skill_check import SkillCheck


# ============================================================
# CONFIGURAÇÃO INICIAL
# ============================================================

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GAME_URL = os.getenv("GAME_URL")


def env_int(name, default):
    """
    Lê uma variável de ambiente como inteiro.
    Retorna o valor padrão caso não esteja configurada.
    """

    value = os.getenv(name)

    if value is None or value.strip() == "":
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(
            f"A variável {name} precisa ser um número inteiro."
        ) from exc


# ============================================================
# VALIDAÇÃO DAS CONFIGURAÇÕES
# ============================================================

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN não foi configurado no arquivo .env."
    )

if not GAME_URL:
    raise RuntimeError(
        "GAME_URL não foi configurada no arquivo .env."
    )

CONFIG = {
    "number_min": env_int("NUMBER_MIN", 1),
    "number_max": env_int("NUMBER_MAX", 100),
    "sequence_length": env_int("SEQUENCE_LENGTH", 5),
    "sequence_time_limit": env_int("SEQUENCE_TIME_LIMIT", 15000),
}

if CONFIG["number_min"] > CONFIG["number_max"]:
    raise ValueError(
        "NUMBER_MIN não pode ser maior que NUMBER_MAX."
    )

if not 1 <= CONFIG["sequence_length"] <= 100:
    raise ValueError(
        "SEQUENCE_LENGTH precisa estar entre 1 e 100."
    )

if not 1 <= CONFIG["sequence_time_limit"] <= 3600000:
    raise ValueError(
        "SEQUENCE_TIME_LIMIT precisa estar entre 1 e 3600000."
    )


# ============================================================
# SISTEMA DE TESTES
# ============================================================

skill_check = SkillCheck(
    game_url=GAME_URL,
    config=CONFIG,
)


# ============================================================
# MENU PRINCIPAL
# ============================================================

async def send_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    minimum=None,
    maximum=None,
    sequence_length=None,
    sequence_time_limit=None,
):
    """
    Envia o teclado com as opções de teste.
    """

    user = update.effective_user

    if user is None or update.effective_message is None:
        return

    keyboard = skill_check.keyboard(
        user_id=user.id,
        minimum=minimum,
        maximum=maximum,
        sequence_length=sequence_length,
        sequence_time_limit=sequence_time_limit,
    )

    await update.effective_message.reply_text(
        "Escolha o teste de habilidade:",
        reply_markup=keyboard,
    )


# ============================================================
# COMANDO /START
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Abre o menu principal.
    """

    await send_menu(update, context)


# ============================================================
# COMANDO /BASICO
# ============================================================

async def basico(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Permite configurar o intervalo do teste numérico.

    Exemplos:
        /basico
        /basico 10 50
    """

    minimum = CONFIG["number_min"]
    maximum = CONFIG["number_max"]

    if len(context.args) not in (0, 2):
        await update.effective_message.reply_text(
            "Uso correto:\n"
            "/basico\n"
            "/basico 10 50\n\n"
            "Informe o valor mínimo e o valor máximo."
        )
        return

    if len(context.args) == 2:
        try:
            minimum = int(context.args[0])
            maximum = int(context.args[1])
        except ValueError:
            await update.effective_message.reply_text(
                "Os valores precisam ser números inteiros."
            )
            return

    if minimum > maximum:
        await update.effective_message.reply_text(
            "O valor mínimo não pode ser maior que o máximo."
        )
        return

    await send_menu(
        update,
        context,
        minimum=minimum,
        maximum=maximum,
    )


# ============================================================
# COMANDO /SEQUENCIA
# ============================================================

async def sequencia(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Permite configurar o tamanho e o tempo do teste de sequência.

    Exemplos:
        /sequencia
        /sequencia 7
        /sequencia 7 20000
    """

    length = CONFIG["sequence_length"]
    time_limit = CONFIG["sequence_time_limit"]

    if len(context.args) not in (0, 1, 2):
        await update.effective_message.reply_text(
            "Uso correto:\n"
            "/sequencia\n"
            "/sequencia 7\n"
            "/sequencia 7 20000\n\n"
            "O primeiro valor define o tamanho da sequência.\n"
            "O segundo valor define o tempo em milissegundos."
        )
        return

    try:
        if len(context.args) >= 1:
            length = int(context.args[0])

        if len(context.args) == 2:
            time_limit = int(context.args[1])

    except ValueError:
        await update.effective_message.reply_text(
            "Os parâmetros precisam ser números inteiros."
        )
        return

    if not 1 <= length <= 100:
        await update.effective_message.reply_text(
            "O tamanho da sequência deve estar entre 1 e 100."
        )
        return

    if not 1 <= time_limit <= 3600000:
        await update.effective_message.reply_text(
            "O tempo deve estar entre 1 e 3600000 milissegundos."
        )
        return

    await send_menu(
        update,
        context,
        sequence_length=length,
        sequence_time_limit=time_limit,
    )


# ============================================================
# RECEBIMENTO DOS DADOS DO MINI APP
# ============================================================

async def receive_web_app_data(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Recebe os resultados enviados pelo Telegram Mini App.
    """

    message = update.effective_message
    user = update.effective_user

    if message is None or user is None:
        return

    if message.web_app_data is None:
        return

    raw_data = message.web_app_data.data

    try:
        data = json.loads(raw_data)

        if not isinstance(data, dict):
            raise ValueError("O conteúdo recebido não é um objeto JSON.")

        if data.get("type") != "skill_check":
            raise ValueError("Tipo de resultado desconhecido.")

        method = data.get("method")

        # ----------------------------------------------------
        # TESTE NUMÉRICO
        # ----------------------------------------------------

        if method == "number":
            minimum = data.get("minimum")
            maximum = data.get("maximum")
            result = data.get("result")

            values = (minimum, maximum, result)

            if any(
                isinstance(value, bool)
                or not isinstance(value, int)
                for value in values
            ):
                raise ValueError(
                    "Os valores do teste numérico são inválidos."
                )

            if minimum > maximum:
                raise ValueError(
                    "O intervalo numérico recebido é inválido."
                )

            if not minimum <= result <= maximum:
                raise ValueError(
                    "O resultado está fora do intervalo permitido."
                )

            logger.info(
                "Teste numérico: usuário=%s resultado=%s intervalo=%s-%s",
                user.id,
                result,
                minimum,
                maximum,
            )

            await message.reply_text(
                "✧ **Teste numérico concluído!**\n\n"
                f"Resultado: **{result}/{maximum}**\n"
                f"Intervalo: {minimum} a {maximum}",
                parse_mode="Markdown",
            )

            await send_menu(update, context)
            return

        # ----------------------------------------------------
        # TESTE DE SEQUÊNCIA
        # ----------------------------------------------------

        if method == "sequence":

            validation = skill_check.validate_sequence_result(
                user_id=user.id,
                data=data,
            )

            if not validation["valid"]:
                logger.warning(
                    "Resultado de sequência inválido: usuário=%s motivo=%s",
                    user.id,
                    validation.get("message"),
                )

                await message.reply_text(
                    "Não foi possível validar o resultado do desafio.\n"
                    f"Motivo: {validation['message']}"
                )

                await send_menu(update, context)
                return

            hits = validation["hits"]
            errors = validation["errors"]
            attempts = validation["attempts"]
            accuracy = validation["accuracy"]
            time_ms = validation["time_ms"]
            total = validation["total"]

            success = validation["success"]

            logger.info(
                (
                    "Teste de sequência: usuário=%s "
                    "sucesso=%s acertos=%s erros=%s "
                    "tentativas=%s precisão=%.2f%% tempo=%sms"
                ),
                user.id,
                success,
                hits,
                errors,
                attempts,
                accuracy,
                time_ms,
            )

            if success:
                status = "🏆 **Sequência concluída!**"
            else:
                status = "⏱️ **Tempo esgotado!**"

            result_text = (
                f"{status}\n\n"
                f"Acertos: **{hits}/{total}**\n"
                f"Erros: **{errors}**\n"
                f"Tentativas: **{attempts}**\n"
                f"Precisão: **{accuracy:.1f}%**\n"
                f"Tempo: **{time_ms / 1000:.2f} segundos**"
            )

            await message.reply_text(
                result_text,
                parse_mode="Markdown",
            )

            await send_menu(update, context)
            return

        # ----------------------------------------------------
        # MÉTODO DESCONHECIDO
        # ----------------------------------------------------

        raise ValueError("Método de teste desconhecido.")

    except (
        json.JSONDecodeError,
        ValueError,
        TypeError,
        KeyError,
    ) as exc:

        logger.warning(
            "Dados inválidos recebidos do Mini App: usuário=%s erro=%s",
            user.id,
            exc,
        )

        await message.reply_text(
            "Ocorreu um problema ao processar o resultado do teste.\n"
            "Tente iniciar um novo desafio."
        )

        await send_menu(update, context)

    except Exception:
        logger.exception(
            "Erro inesperado ao processar dados do Mini App."
        )

        await message.reply_text(
            "Ocorreu um erro interno ao processar o resultado."
        )


# ============================================================
# INICIALIZAÇÃO DO BOT
# ============================================================

def main():
    """
    Inicializa o bot e registra os comandos.
    """

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("basico", basico)
    )

    application.add_handler(
        CommandHandler("sequencia", sequencia)
    )

    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.WEB_APP_DATA,
            receive_web_app_data,
        )
    )

    logger.info("Skill Check Bot iniciado.")

    application.run_polling()


if __name__ == "__main__":
    main()
