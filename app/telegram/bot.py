from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup

from app.config import settings
from app.telegram.dao import TelegramUsersDAO
from app.users.dao import UsersDAO


storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class VerificationState(StatesGroup):
    waiting_for_token = State()


@dp.message(CommandStart())
async def command_start_handler(message: Message):
    await message.answer(
        f"Привет, {hbold(message.from_user.full_name)}! "
        "Этот бот предназначен для напоминания о пропущенных сообщениях из приложения mychat.\n\n"
        "Для верификации введите команду /verification и введите персональный токен верификации, "
        "полученный на почту при регистрации."
    )


@dp.message(F.text == "/verification")
async def command_verification_handler(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, введите токен, который вы получили на почте.")
    await state.set_state(VerificationState.waiting_for_token)


@dp.message(VerificationState.waiting_for_token)
async def handle_token_input(message: Message, state: FSMContext):
    token = message.text
    tg_user = await TelegramUsersDAO.find_one_or_none(token=token)

    if not tg_user:
        await message.answer(
            "Неверный токен или срок действия токена истек. Пожалуйста, попробуйте снова."
        )
        await state.finish()
        return

    tg_user.telegram_id = message.chat.id
    await TelegramUsersDAO.update(tg_user)

    user = await UsersDAO.find_one_or_none(email=tg_user.email)
    if user:
        user.is_verified = True
        await UsersDAO.update(user)

        await message.answer(
            "Вы успешно верифицированы! Теперь вы можете использовать приложение Mychat."
        )
    else:
        await message.answer("Пользователь не найден.")

    await state.finish()


@dp.message()
async def default_message_handler(message: Message):
    await message.answer("Этот бот не предназначен для общения.")


async def start_telegram_bot():
    bot = Bot(
        token=settings.TG_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    await dp.start_polling(bot)
