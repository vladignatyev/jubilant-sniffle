from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import List, Literal, Union

Blockchain = Literal[
    "BTC",
    "BCH",
    "LTC",
    "XRP",
    "ETC",
    "ADA",
    "ETH",
    "TRX",
    "ALGO",
    "XLM",
    "MATIC",
    "OP",
    "BASE",
    "ZEC",
    "DOGE",
    "SOL",
    "BSV",
    "AVAX",
    "DOT",
    "TON",
    "XTZ",
    "TetherOMNI",
    "NEAR",
    "APT",
]


@dataclass(slots=True)
class ImmediateResponse:
    content: str
    detail: str | None = None


@dataclass(slots=True)
class PostponedResponse:
    uid: str
    address: str
    blockchain: Blockchain


CheckAddressResponse = Union[ImmediateResponse, PostponedResponse]


async def check_address(addresses: List[str], blockchain: Blockchain) -> CheckAddressResponse:
    """Stub check that alternates between immediate and postponed results.

    If the first address contains the word "wait" (case-insensitive), the response
    will be postponed to exercise the polling flow. Otherwise, an immediate stub
    response is returned.
    """

    primary = addresses[0]
    if "wait" in primary.lower():
        return PostponedResponse(
            uid=str(random.randint(1000, 9999)),
            address=primary,
            blockchain=blockchain,
        )
    return ImmediateResponse(content="immediate_response", detail="stub_detail")


async def poll_recheck_address(
    uid: str, address: str, blockchain: Blockchain
) -> ImmediateResponse | None:
    """Stub poller that pretends to finish processing."""

    await asyncio.sleep(0)  # allow context switching
    return ImmediateResponse(content="immediate_response", detail="stub_detail")
