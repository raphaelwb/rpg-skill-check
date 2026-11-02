
import os
import json
import logging

from pathlib import Path
from dotenv import load_dotenv

from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)


# Carrega o .env localizado na raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
GAME_URL = os.getenv("GAME_URL")


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    button = KeyboardButton(
        text="🎲 Rolar habilidade",
        web_app=WebAppInfo(url=GAME_URL)
    )

    keyboard = ReplyKeyboardMarkup(
        [[button]],
        resize_keyboard=True
    )

    await update.message.reply_text(
        "Bem-vindo ao Skill Roll!\n\n"
        "Clique no botão abaixo para fazer sua rolagem.",
        reply_markup=keyboard
    )


async def receive_roll(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = update.effective_message

    try:
        data = json.loads(message.web_app_data.data)

        if data.get("type") != "skill_roll":
            raise ValueError("Tipo de resultado inválido")

        result = data.get("result")
        minimum = data.get("min")
        maximum = data.get("max")

        values = (result, minimum, maximum)

        if not all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in values
        ):
            raise ValueError("Os valores precisam ser inteiros")

        if minimum > maximum:
            raise ValueError("Faixa inválida")

        if maximum - minimum > 1000000:
            raise ValueError("Faixa muito grande")

        if not minimum <= result <= maximum:
            raise ValueError("Resultado fora da faixa")

        await message.reply_text(
            f"🎲 Resultado da rolagem: {result}\n"
            f"Faixa: {minimum}–{maximum}"
        )

    except (ValueError, TypeError, json.JSONDecodeError):
        await message.reply_text(
            "Não foi possível validar a rolagem."
        )


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN não encontrado no arquivo .env"
        )

    if not GAME_URL:
        raise RuntimeError(
            "GAME_URL não encontrado no arquivo .env"
        )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.WEB_APP_DATA,
            receive_roll
        )
    )

    print("RPG Skill Roll iniciado.")

    application.run_polling()


if __name__ == "__main__":
    main()
