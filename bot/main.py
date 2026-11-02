
import json
import logging
import os

from dotenv import load_dotenv
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from skill_check import SkillCheck


load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GAME_URL = os.getenv("GAME_URL")

if not BOT_TOKEN or not GAME_URL:
    raise RuntimeError("Configure BOT_TOKEN e GAME_URL no arquivo .env")


def env_int(name, default):
    try:
        return int(os.getenv(name, default))
    except ValueError:
        raise RuntimeError(f"Valor inválido para {name}")



config = {
    "number_min": env_int("NUMBER_MIN", 1),
    "number_max": env_int("NUMBER_MAX", 100),
    "sequence_length": env_int("SEQUENCE_LENGTH", 5),
    "sequence_time_limit": env_int("SEQUENCE_TIME_LIMIT", 15000),
}

if config["number_min"] > config["number_max"]:
    raise RuntimeError("NUMBER_MIN não pode ser maior que NUMBER_MAX")

if not 1 <= config["sequence_length"] <= 100:
    raise RuntimeError("SEQUENCE_LENGTH deve estar entre 1 e 100")

if not 1 <= config["sequence_time_limit"] <= 3600000:
    raise RuntimeError("SEQUENCE_TIME_LIMIT deve estar entre 1 e 3600000 ms")



skill_check = SkillCheck(GAME_URL, config)


async def send_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    minimum=None,
    maximum=None,
    sequence_length=None,
    sequence_time_limit=None,
):
    user_id = update.effective_user.id

    keyboard = skill_check.keyboard(
        user_id=user_id,
        minimum=minimum,
        maximum=maximum,
        sequence_length=sequence_length,
        sequence_time_limit=sequence_time_limit,
    )

    await update.effective_message.reply_text(
        "Escolha o teste de habilidade:",
        reply_markup=keyboard,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_menu(update, context)


async def basic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    minimum = None
    maximum = None

    try:
        if len(context.args) == 1:
            raise ValueError
        if len(context.args) >= 2:
            minimum = int(context.args[0])
            maximum = int(context.args[1])

        if minimum is not None and minimum > maximum:
            raise ValueError

    except ValueError:
        await update.effective_message.reply_text(
            "Uso: /basico ou /basico 10 50"
        )
        return

    await send_menu(update, context, minimum=minimum, maximum=maximum)


async def sequence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    length = None
    time_limit = None

    try:
        if len(context.args) == 1:
            length = int(context.args[0])
        elif len(context.args) >= 2:
            length = int(context.args[0])
            time_limit = int(context.args[1])

        if length is not None and length < 1:
            raise ValueError
        if time_limit is not None and time_limit <= 0:
            raise ValueError

    except ValueError:
        await update.effective_message.reply_text(
            "Uso: /sequencia ou /sequencia 7 20000"
        )
        return

    await send_menu(
        update,
        context,
        sequence_length=length,
        sequence_time_limit=time_limit,
    )


async def receive_web_app_data(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message
    user = update.effective_user

    try:
        data = json.loads(message.web_app_data.data)

        if not isinstance(data, dict):
            raise ValueError("Formato inválido")

        method = data.get("method")

        if data.get("type") != "skill_check":
            raise ValueError("Tipo de desafio inválido")

        if method == "number":
            minimum = data.get("minimum")
            maximum = data.get("maximum")
            result = data.get("result")

            values = (minimum, maximum, result)
            if not all(
                isinstance(value, int) and not isinstance(value, bool)
                for value in values
            ):
                raise ValueError("Resultado numérico inválido")

            if minimum > maximum or not minimum <= result <= maximum:
                raise ValueError("Resultado fora do intervalo")

            print(
                f"[BÁSICO] Jogador: {user.full_name} "
                f"(ID: {user.id}) | Resultado: {result} "
                f"| Intervalo: {minimum}-{maximum}"
            )

            await message.reply_text(
                f"🎲 Resultado: {result}\n"
                f"Intervalo: {minimum} a {maximum}"
            )

        elif method == "sequence":
            result = skill_check.validate_sequence_result(user.id, data)

            if not result["valid"]:
                await message.reply_text(
                    f"Não foi possível validar o desafio: {result['message']}"
                )
                await send_menu(update, context)
                return

            status = "SUCESSO" if result["success"] else "FALHA"

            print(
                f"[SEQUÊNCIA] Jogador: {user.full_name} "
                f"(ID: {user.id}) | Resultado: {status} "
                f"| Acertos: {result['completed']}/{result['total']} "
                f"| Tempo: {result['time_ms']}ms"
            )

            if result["success"]:
                text = (
                    "✅ Sequência concluída!\n"
                    f"Tempo: {result['time_ms']} ms"
                )
            else:
                text = (
                    "❌ Falha no desafio.\n"
                    f"Direções corretas: {result['completed']}/"
                    f"{result['total']}\n"
                    f"Tempo: {result['time_ms']} ms"
                )

            await message.reply_text(text)

        else:
            raise ValueError("Método desconhecido")

    except (ValueError, TypeError, json.JSONDecodeError) as error:
        logging.warning("Dados recebidos inválidos: %s", error)
        await message.reply_text("Não foi possível processar o resultado.")

    await send_menu(update, context)


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("basico", basic))
    application.add_handler(CommandHandler("sequencia", sequence))

    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.WEB_APP_DATA,
            receive_web_app_data,
        )
    )

    print("Bot iniciado.")
    application.run_polling()


if __name__ == "__main__":
    main()
