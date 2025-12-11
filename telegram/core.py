from __future__ import annotations

import asyncio
import re
import uuid
from collections.abc import Mapping
from typing import Final

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from telegram.api import (
    CheckAddressResponse,
    ImmediateResponse,
    PostponedResponse,
    check_address,
    poll_recheck_address,
)
from telegram.config import Settings


dp = Dispatcher()
_pending_requests: dict[str, str] = {}

BLOCKCHAIN_OPTIONS: Final[Mapping[str, str]] = {
    "Bitcoin": "BTC",
    "Ethereum": "ETH",
    "Tron": "TRX",
    "Solana": "SOL",
    "Dogecoin": "DOGE",
    "Zcash": "ZEC",
    "Binance Smart Chain": "ETH",
    "Litecoin": "LTC",
    "Bitcoin Cash": "BCH",
    "Ethereum Classic": "ETC",
    "Ripple": "XRP",
    "Stellar": "XLM",
    "Polygon": "MATIC",
    "Cardano": "ADA",
    "Base": "BASE",
    "Optimism": "OP",
    "Arbitrum": "OP",
    "Omni": "TetherOMNI",
    "Bitcoin SV": "BSV",
    "Avalanche": "AVAX",
    "Polkadot": "DOT",
    "TON": "TON",
    "NEAR": "NEAR",
    "Tezos": "XTZ",
    "Aptos": "APT",
    "Algorand": "ALGO",
}


@dp.message(CommandStart())
async def welcome(message: Message) -> None:
    await message.answer(f"Welcome, {html.bold(message.from_user.full_name)}!")


def _is_valid_address(value: str | None) -> bool:
    if not value:
        return False
    candidate = value.strip()
    return bool(re.fullmatch(r"[A-Za-z0-9]{26,64}", candidate))


def _build_blockchain_keyboard(request_id: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=name, callback_data=f"{request_id}:{code}")
        for name, code in BLOCKCHAIN_OPTIONS.items()
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message()
async def just_address(message: Message) -> None:
    address = message.text or ""
    if not _is_valid_address(address):
        await message.answer("The address you provided isn't recognized")
        return

    request_id = uuid.uuid4().hex
    _pending_requests[request_id] = address.strip()
    keyboard = _build_blockchain_keyboard(request_id)

    await message.answer("Which blockchain to check this address across?", reply_markup=keyboard)


async def _handle_check_result(
    *,
    callback: CallbackQuery,
    request_id: str,
    working_message: Message | None,
    result: CheckAddressResponse,
) -> None:
    if isinstance(result, PostponedResponse):
        if not working_message:
            return

        async def _poll() -> None:
            try:
                while True:
                    response = await poll_recheck_address(
                        result.uid, result.address, result.blockchain
                    )
                    if response:
                        try:
                            await working_message.delete()
                        except Exception:
                            pass
                        await callback.message.answer(response.content)
                        break
                    await asyncio.sleep(30)
            finally:
                _pending_requests.pop(request_id, None)

        asyncio.create_task(_poll())
        return

    if working_message:
        try:
            await working_message.delete()
        except Exception:
            pass
    if isinstance(result, ImmediateResponse):
        await callback.message.answer(result.content)
    else:
        await callback.message.answer(str(result))
    _pending_requests.pop(request_id, None)


@dp.callback_query()
async def blockchain_selected(callback: CallbackQuery) -> None:
    if not callback.data:
        await callback.answer()
        return

    try:
        request_id, blockchain = callback.data.split(":", 1)
    except ValueError:
        await callback.answer()
        return

    address = _pending_requests.get(request_id)
    if not address:
        await callback.answer("Request expired", show_alert=False)
        return

    await callback.answer()
    result = await check_address([address], blockchain)  # type: ignore[arg-type]

    if isinstance(result, PostponedResponse):
        working_message = await callback.message.answer("Working on your request...")
    else:
        working_message = None

    await _handle_check_result(
        callback=callback,
        request_id=request_id,
        working_message=working_message,
        result=result,
    )


async def main() -> None:  # noqa: N802
    settings = Settings()
    bot = Bot(
        token=settings.telegram_api_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await dp.start_polling(bot)
