import logging

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
from app.telegram.schemas import TelegramUserUpdate
from app.users.schemas import UserUpdate


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class VerificationState(StatesGroup):
    waiting_for_token = State()


@dp.message(CommandStart())
async def command_start_handler(message: Message):
    logger.info(f"User {message.from_user.id} started the bot.")
    await message.answer(
        f"Привет, {hbold(message.from_user.full_name)}! "
        "Этот бот предназначен для напоминания о пропущенных сообщениях из приложения mychat.\n\n"
        "Для верификации введите команду /verification и введите персональный токен верификации, "
        "полученный на почту при регистрации."
    )


@dp.message(F.text == "/verification")
async def command_verification_handler(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} started verification.")
    await message.answer("Пожалуйста, введите токен, который вы получили на почте.")
    await state.set_state(VerificationState.waiting_for_token)


@dp.message(VerificationState.waiting_for_token)
async def handle_token_input(message: Message, state: FSMContext):
    token = message.text
    logger.info(f"User {message.from_user.id} entered token: {token}")

    tg_user = await TelegramUsersDAO.find_one_or_none(token=token)

    if not tg_user:
        logger.warning(f"Invalid token attempt by user {message.from_user.id}")
        await message.answer(
            "Неверный токен или срок действия токена истек. Пожалуйста, попробуйте снова."
        )
        await state.clear()
        return

    tg_update_data = TelegramUserUpdate(telegram_id=message.chat.id)
    await TelegramUsersDAO.update(
        {"id": tg_user.id}, **tg_update_data.model_dump(exclude_unset=True)
    )

    user = await UsersDAO.find_one_or_none(email=tg_user.email)
    if user:
        user_update_data = UserUpdate(is_verified=True)
        await UsersDAO.update(
            {"id": user.id}, **user_update_data.model_dump(exclude_unset=True)
        )

        logger.info(f"User {message.from_user.id} successfully verified.")
        await message.answer(
            "Вы успешно верифицированы! Теперь вы можете использовать приложение Mychat. "
            "Авторизуйтесь на сайте."
        )
    else:
        logger.error(f"User {message.from_user.id} not found in system.")
        await message.answer("Пользователь не найден.")

    await state.clear()


@dp.message()
async def default_message_handler(message: Message):
    logger.info(f"User {message.from_user.id} sent an unsupported message.")
    await message.answer("Этот бот не предназначен для общения.")


async def start_telegram_bot():
    bot = Bot(
        token=settings.TG_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    logger.info("Bot is starting...")
    await dp.start_polling(bot)
