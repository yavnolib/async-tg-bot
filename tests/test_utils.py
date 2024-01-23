from unittest.mock import AsyncMock, patch

import numpy as np
import pytest
from telegram import InlineKeyboardButton

from src import utils


def test_fname():
    assert isinstance(utils.get_fname(), str)


def test_default():
    assert len(utils.get_default_state()) == 3
    assert [3, 3, 3] == [len(utils.get_default_state()[i]) for i in range(3)]


def test_generate_keyboard():
    gen_key = utils.generate_keyboard(utils.get_default_state())
    assert np.all(
        np.array(
            [
                [
                    isinstance(gen_key[i][j], InlineKeyboardButton)
                    for j in range(3)
                ]
                for i in range(3)
            ]
        )
    )


pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_start():
    returned = []

    async def print_format(text, reply_markup=None):
        returned.append(text + str(reply_markup))

    context = AsyncMock()
    update = AsyncMock()
    update.message.reply_text = print_format
    update.message.from_user.first_name = "abc"
    assert await utils.start(update, context) == 0
    assert len(returned) > 0 and ("abc" in returned[0])


@pytest.mark.asyncio
async def test_process_keyboard():
    result = []

    async def some_editor(
        chat_id=None, message_id=None, reply_markup=None, text=None
    ):
        result.append(f"{chat_id}, {message_id}, {reply_markup}, {text}")

    context = AsyncMock()
    update = AsyncMock()
    query = AsyncMock()

    # FIRST TEST
    # test if double-click on an occupied cell
    query.data = "01"
    context.user_data = {"keyboard_state": [["."] * 3] * 3}
    context.user_data["keyboard_state"][0][1] = "a"
    update.callback_query.message.text = "blah occupied cell blah"
    assert (
        await utils.process_keyboard(update, context, query)
        == utils.FINISH_GAME
    ), "Smth went wrong when double click on an occupied cell"

    # SECOND TEST
    # test if click on an occupied cell
    query.data = "01"
    update.callback_query.message.text = "blah blah"
    update.callback_query.message.chat.id = "1"
    update.callback_query.message.id = "2"
    query.message.reply_markup = "3"
    context.bot.edit_message_text = some_editor

    assert (
        await utils.process_keyboard(update, context, query)
        == utils.FINISH_GAME
    ), "Smth went wrong after click on an occupied cell"

    assert (
        result[0] == "1, 2, 3,"
        " You have placed a cross in an occupied cell."
        " Place in the free one."
    ), "Smth went wrong after click on an occupied cell"

    # THIRD TEST
    # test if click on a free cell
    context.user_data["keyboard_state"][0][1] = utils.FREE_SPACE
    assert (
        await utils.process_keyboard(update, context, query)
        == utils.CONTINUE_GAME
    ), "smth went wrong after click on a free cell"
    assert (
        context.user_data["keyboard_state"][0][1] == utils.CROSS
    ), "The cross was not placed"


@pytest.mark.asyncio
async def test_game_over():
    update = AsyncMock()
    context = AsyncMock()
    who = "a"
    with patch("src.utils.before_end") as mocked_bend, patch(
        "src.utils.end"
    ) as mocked_end:
        mocked_end.return_value = 0
        assert await utils.game_over(update, context, who) == 0
        mocked_bend.assert_awaited_once()
        mocked_end.assert_awaited_once()


@pytest.mark.asyncio
async def test_game_1():
    async def get_answer():
        return True

    update = AsyncMock()
    context = AsyncMock()
    update.callback_query = AsyncMock()
    update.callback_query.answer = get_answer

    with patch("src.utils.process_keyboard") as mocked:
        mocked.return_value = True
        assert await utils.game(update, context) == utils.CONTINUE_GAME
        mocked.assert_awaited_once()

    with patch("src.utils.process_keyboard") as mocked, patch(
        "src.utils.get_winner_or_continue"
    ) as cont_mocked:
        cont_mocked.return_value = 2
        mocked.return_value = False
        assert await utils.game(update, context) == 2
        mocked.assert_awaited_once()


@pytest.mark.asyncio
async def test_game_2():
    async def get_answer():
        return False

    update = AsyncMock()
    context = AsyncMock()
    update.callback_query = AsyncMock()
    update.callback_query.answer = get_answer

    with patch("logging.info"):
        assert await utils.game(update, context) == utils.CONTINUE_GAME
