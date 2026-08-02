"""Strictly read-only Modbus client for STIEBEL ISG."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import UNAVAILABLE_RAW
from .registers import OFFSET_PROBES, REGISTERS, REGISTER_BY_KEY, Register


class StiebelIsgError(Exception):
    """Base communication or decoding error."""


@dataclass(frozen=True, slots=True)
class Value:
    value: float | int | None
    raw: int | None
    available: bool
    plausible: bool


def decode(raw: int, data_type: int) -> float | int:
    scale = {2: 0.1, 6: 1.0, 7: 0.01, 8: 1.0}[data_type]
    number = raw - 0x10000 if data_type in (2, 7) and raw & 0x8000 else raw
    result = number * scale
    return int(result) if scale == 1 else round(result, 4)


class StiebelIsgClient:
    """Client whose public surface contains read operations only (FC03/FC04)."""

    def __init__(self, host: str, port: int, unit_id: int, timeout: float) -> None:
        self._host, self._port, self._unit_id, self._timeout = host, port, unit_id, timeout

    def _read_raw(self, client: ModbusTcpClient, register: Register, offset: int) -> int:
        # Keep the load on the embedded gateway deliberately low.
        time.sleep(0.05)
        method = client.read_input_registers if register.kind == "input" else client.read_holding_registers
        response = method(register.address + offset, count=1, device_id=self._unit_id)
        if response.isError() or not getattr(response, "registers", None):
            raise ModbusException(str(response))
        return int(response.registers[0])

    def _detect_offset_sync(self) -> int:
        scores: dict[int, int] = {}
        client = ModbusTcpClient(self._host, port=self._port, timeout=self._timeout, retries=1)
        try:
            if not client.connect():
                raise StiebelIsgError("Connection failed")
            for offset in (-1, 0):
                score = 0
                for key in OFFSET_PROBES:
                    register = REGISTER_BY_KEY[key]
                    try:
                        raw = self._read_raw(client, register, offset)
                        if raw != UNAVAILABLE_RAW:
                            value = decode(raw, register.data_type)
                            score += 3 if _plausible(register, value) else -2
                    except (ModbusException, OSError):
                        score -= 1
                scores[offset] = score
        finally:
            client.close()
        winner = max(scores, key=scores.get)
        if scores[winner] <= 0 or list(scores.values()).count(scores[winner]) > 1:
            raise StiebelIsgError(f"Address offset is ambiguous: {scores}")
        return winner

    async def detect_offset(self) -> int:
        return await asyncio.to_thread(self._detect_offset_sync)

    def _read_all_sync(self, offset: int) -> dict[str, Value]:
        values: dict[str, Value] = {}
        client = ModbusTcpClient(self._host, port=self._port, timeout=self._timeout, retries=1)
        try:
            if not client.connect():
                raise StiebelIsgError("Connection failed")
            for register in REGISTERS:
                try:
                    raw = self._read_raw(client, register, offset)
                    if raw == UNAVAILABLE_RAW:
                        values[register.key] = Value(None, raw, False, True)
                        continue
                    value = decode(raw, register.data_type)
                    values[register.key] = Value(value, raw, True, _plausible(register, value))
                except (ModbusException, OSError):
                    values[register.key] = Value(None, None, False, False)
        finally:
            client.close()
        return values

    async def read_all(self, offset: int) -> dict[str, Value]:
        return await asyncio.to_thread(self._read_all_sync, offset)


def _plausible(register: Register, value: float | int) -> bool:
    return ((register.minimum is None or value >= register.minimum)
            and (register.maximum is None or value <= register.maximum))
