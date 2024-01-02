#!/usr/bin/python3.12
"""
Bot for playing tic tac toe game with multiple CallbackQueryHandlers.
"""
import datetime
import logging
import os
from copy import deepcopy

import numpy as np
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

TOKEN = os.getenv("TG_TOKEN")

CONTINUE_GAME, FINISH_GAME = range(2)

FREE_SPACE = "."
CROSS = "✖"
ZERO = "O"


DEFAULT_STATE = [[FREE_SPACE for _ in range(3)] for _ in range(3)]


def get_fname():
    """Get filename for new log file"""
    return datetime.datetime.now().strftime("%d:%m:%Y_%H:%M:%S")


def get_default_state():
    """Helper function to get default state of the game"""
    return deepcopy(DEFAULT_STATE)


def generate_keyboard(
    state: list[list[str]],
) -> list[list[InlineKeyboardButton]]:
    """Generate tic tac toe keyboard 3x3 (telegram buttons)"""
    return [
        [
            InlineKeyboardButton(state[r][c], callback_data=f"{r}{c}")
            for c in range(3)
        ]
        for r in range(3)
    ]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    context.user_data["keyboard_state"] = get_default_state()
    keyboard = generate_keyboard(context.user_data["keyboard_state"])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"{update.message.from_user.first_name}, your turn! Please, put X to the free place",
        reply_markup=reply_markup,
    )
    return CONTINUE_GAME


async def process_keyboard(update, context, query) -> int:
    """Function for handling inline keyboard presses"""
    keyboard = list(context.user_data["keyboard_state"])
    keyboard = [list(i) for i in keyboard]

    r, c = map(int, query.data)
    if keyboard[r][c] != FREE_SPACE:
        if "occupied cell" in update.callback_query.message.text:
            return FINISH_GAME
        await context.bot.edit_message_text(
            chat_id=update.callback_query.message.chat.id,
            message_id=update.callback_query.message.id,
            text="You have placed a cross in an occupied cell. Place in the free one.",
            reply_markup=query.message.reply_markup,
        )
        return FINISH_GAME

    new_val = CROSS
    keyboard[r][c] = new_val
    # keyboard = tuple(tuple(i for i in keyboard) for _ in keyboard)
    context.user_data["keyboard_state"] = keyboard
    return CONTINUE_GAME


async def game_over(update, context, who: str) -> int:
    """Function to end the game"""
    await before_end(update, context, who)
    return await end(update, context)


async def decide_end(update, context) -> int:
    """Function that decides who wins"""
    if won(context.user_data["keyboard_state"]):
        # выиграл игрок
        logging.info("player won")
        return await game_over(update, context, "player")
    else:
        # ! Последний ход за игроком !
        # Если игрок не выиграл, то ход ИИ
        # Если ИИ сходил, то проверить won, если won, То выиграл ИИ
        # Если ИИ не смог сходить, то ничья.
        if ai_move(context.user_data["keyboard_state"]):
            if won(context.user_data["keyboard_state"]):
                logging.info("ai won")
                return await game_over(update, context, "ai")
        else:
            logging.info("happy won")
            return await game_over(update, context, "happy")
    return CONTINUE_GAME


async def get_winner_or_continue(update, context, query) -> int:
    """A function that decides whether to end the game"""
    if not await decide_end(update, context):
        await context.bot.delete_message(
            chat_id=update.callback_query.message.chat.id,
            message_id=update.callback_query.message.id,
        )

        keyboard = generate_keyboard(context.user_data["keyboard_state"])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.application.bot.sendMessage(
            text=f"{query.from_user.first_name}, your turn! Please, put X to the free place",
            chat_id=update.callback_query.message.chat.id,
            reply_markup=reply_markup,
        )
        return CONTINUE_GAME
    else:
        return FINISH_GAME


async def game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Main processing of the game"""
    query = update.callback_query
    if await query.answer():
        if await process_keyboard(update, context, query):
            return CONTINUE_GAME

        return await get_winner_or_continue(update, context, query)
    else:
        logging.info("smth go wrong")
    return CONTINUE_GAME


def ai_move(fields: list[list[str]]) -> bool:
    """
    Randomly get one cell with '.' and puts a zero in this cell

    ! INPLACE OPERATION !

    :return: - Artificial intelligence has made its move or not.
    """

    cells_for_choice = []
    for i, row in enumerate(fields):
        for j, cell in enumerate(row):
            if cell == FREE_SPACE:
                cells_for_choice.append(str(i) + str(j))
    if not cells_for_choice:
        return False
    i, j = map(int, np.random.choice(cells_for_choice))

    fields[i][j] = ZERO
    return True


def won(fields: list[list[str]]) -> bool:
    """Check if crosses or zeros have won the game"""
    num_fields = [
        [
            1 if fields[r][c] == CROSS else (2 if fields[r][c] == ZERO else 20)
            for c in range(3)
        ]
        for r in range(3)
    ]

    num_fields = np.array(num_fields)

    if (
        np.any(np.logical_or((a := num_fields.sum(axis=0)) == 3, a == 6))
        or np.any(np.logical_or((b := num_fields.sum(axis=1)) == 3, b == 6))
        or np.logical_or((c := (np.diag(num_fields).sum())) == 3, c == 6)
        or np.logical_or(
            (d := (np.diag(num_fields[:, ::-1]).sum())) == 3, d == 6
        )
    ):
        return True
    logging.debug(f"{a=}, {b=}, {c=}, {d=}")
    return False


async def before_end(
    update: Update, context: ContextTypes.DEFAULT_TYPE, who: str
) -> None:
    """Function to prepare for the end of the game"""
    keyboard = generate_keyboard(context.user_data["keyboard_state"])
    reply_markup = InlineKeyboardMarkup(keyboard)
    play_again = "Play again with /start"
    await context.bot.edit_message_reply_markup(
        chat_id=update.callback_query.message.chat.id,
        message_id=update.callback_query.message.id,
        reply_markup=reply_markup,
    )
    if who == "player":
        text = "Congratulations! You won! X to the free place. "
    elif who == "ai":
        text = "Oh :( Unfortunately you lost. "
    elif who == "happy":
        text = "We ended up in a draw! X to the free place. "
    await context.application.bot.sendMessage(
        text=text + play_again,
        chat_id=update.callback_query.message.chat.id,
    )


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    # reset state to default so you can play again with /start
    context.user_data["keyboard_state"] = get_default_state()
    return ConversationHandler.END


def main() -> None:
    """Run the bot"""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Setup conversation handler with the states CONTINUE_GAME and FINISH_GAME
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CONTINUE_GAME: [
                CallbackQueryHandler(game, pattern="^" + f"{r}{c}" + "$")
                for r in range(3)
                for c in range(3)
            ],
            FINISH_GAME: [
                CallbackQueryHandler(end, pattern="^" + f"{r}{c}" + "$")
                for r in range(3)
                for c in range(3)
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
