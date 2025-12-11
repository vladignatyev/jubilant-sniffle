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

    await message.answer(
        "Which blockchain to check this address across?",
        reply_markup=keyboard,
        reply_to_message_id=message.message_id,
    )


def _reply_target_message_id(callback: CallbackQuery) -> int:
    if callback.message.reply_to_message:
        return callback.message.reply_to_message.message_id
    return callback.message.message_id


async def _show_working_status(
    callback: CallbackQuery, *, address: str, blockchain: str
) -> None:
    status_text = f"Checking the address {address} on blockchain {blockchain}"
    try:
        await callback.message.edit_text(status_text, reply_markup=None)
    except Exception:
        await callback.message.answer(status_text)


async def _handle_check_result(
    *,
    callback: CallbackQuery,
    request_id: str,
    result: CheckAddressResponse,
    address: str,
    blockchain: str,
) -> None:
    reply_to_message_id = _reply_target_message_id(callback)
    if isinstance(result, PostponedResponse):
        await _show_working_status(callback, address=address, blockchain=blockchain)

        async def _poll() -> None:
            try:
                while True:
                    response = await poll_recheck_address(
                        result.uid, result.address, result.blockchain
                    )
                    if response:
                        await callback.message.reply(
                            response.content,
                            reply_to_message_id=reply_to_message_id,
                        )
                        break
                    await asyncio.sleep(30)
            finally:
                _pending_requests.pop(request_id, None)

        asyncio.create_task(_poll())
        return

    if isinstance(result, ImmediateResponse):
        await callback.message.reply(
            result.content,
            reply_to_message_id=reply_to_message_id,
        )
    else:
        await callback.message.reply(
            str(result),
            reply_to_message_id=reply_to_message_id,
        )
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
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await _handle_check_result(
        callback=callback,
        request_id=request_id,
        result=result,
        address=address,
        blockchain=blockchain,
    )


async def main() -> None:  # noqa: N802
    settings = Settings()
    bot = Bot(
        token=settings.telegram_api_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await dp.start_polling(bot)
