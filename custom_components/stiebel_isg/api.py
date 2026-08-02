"""Narrowly scoped Modbus client for STIEBEL ISG."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import OPERATING_MODE_FROM_VALUE, UNAVAILABLE_RAW
from .registers import OFFSET_PROBES, REGISTER_BY_KEY, REGISTERS, Register

WRITABLE_NUMBER_SPECS = {
    "hc1_comfort_temperature": (1502, 10, 5.0, 30.0, 1),
    "hc1_eco_temperature": (1503, 10, 5.0, 30.0, 1),
    "hc1_heating_curve": (1504, 100, 0.0, 3.0, 1),
    "dhw_comfort_temperature": (1510, 10, 10.0, 60.0, 5),
    "dhw_eco_temperature": (1511, 10, 10.0, 60.0, 5),
}


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
    """Client supporting reads and explicitly allow-listed parameter writes."""

    def __init__(self, host: str, port: int, unit_id: int, timeout: float) -> None:
        self._host, self._port, self._unit_id, self._timeout = (
            host,
            port,
            unit_id,
            timeout,
        )
        self._operation_lock = asyncio.Lock()

    def _read_raw(
        self, client: ModbusTcpClient, register: Register, offset: int
    ) -> int:
        # Keep the load on the embedded gateway deliberately low.
        time.sleep(0.05)
        method = (
            client.read_input_registers
            if register.kind == "input"
            else client.read_holding_registers
        )
        response = method(register.address + offset, count=1, device_id=self._unit_id)
        if response.isError() or not getattr(response, "registers", None):
            raise ModbusException(str(response))
        return int(response.registers[0])

    def _detect_offset_sync(self) -> int:
        scores: dict[int, int] = {}
        client = ModbusTcpClient(
            self._host, port=self._port, timeout=self._timeout, retries=1
        )
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
        async with self._operation_lock:
            return await asyncio.to_thread(self._detect_offset_sync)

    def _read_all_sync(self, offset: int) -> dict[str, Value]:
        values: dict[str, Value] = {}
        client = ModbusTcpClient(
            self._host, port=self._port, timeout=self._timeout, retries=1
        )
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
                    values[register.key] = Value(
                        value, raw, True, _plausible(register, value)
                    )
                except (ModbusException, OSError):
                    values[register.key] = Value(None, None, False, False)
        finally:
            client.close()
        return values

    async def read_all(self, offset: int) -> dict[str, Value]:
        async with self._operation_lock:
            return await asyncio.to_thread(self._read_all_sync, offset)

    def _set_operating_mode_sync(self, mode: int, offset: int) -> None:
        """Write and verify only WPMsystem operating mode register 1501 (FC06)."""
        if mode not in OPERATING_MODE_FROM_VALUE:
            raise ValueError(f"Unsupported operating mode: {mode}")
        if offset not in (-1, 0):
            raise ValueError(f"Unsupported address offset: {offset}")

        register = REGISTER_BY_KEY["operating_mode"]
        if register.address != 1501 or register.kind != "holding":
            raise StiebelIsgError("Operating-mode register definition is unsafe")

        client = ModbusTcpClient(
            self._host, port=self._port, timeout=self._timeout, retries=1
        )
        try:
            if not client.connect():
                raise StiebelIsgError("Connection failed")
            time.sleep(0.05)
            response = client.write_register(
                register.address + offset, mode, device_id=self._unit_id
            )
            if response.isError():
                raise ModbusException(str(response))
            raw = self._read_raw(client, register, offset)
            if raw != mode:
                raise StiebelIsgError(
                    f"Operating-mode verification failed: wrote {mode}, read {raw}"
                )
        except (ModbusException, OSError) as error:
            raise StiebelIsgError(str(error)) from error
        finally:
            client.close()

    async def set_operating_mode(self, mode: int, offset: int) -> None:
        """Set one documented operating mode and verify the resulting register."""
        async with self._operation_lock:
            await asyncio.to_thread(self._set_operating_mode_sync, mode, offset)

    def _set_number_parameter_sync(
        self, register_key: str, value: float, offset: int
    ) -> None:
        """Write and verify one explicitly allow-listed numeric parameter."""
        if register_key not in WRITABLE_NUMBER_SPECS:
            raise ValueError(f"Unsupported writable parameter: {register_key}")
        if offset not in (-1, 0):
            raise ValueError(f"Unsupported address offset: {offset}")

        expected_address, multiplier, minimum, maximum, raw_step = (
            WRITABLE_NUMBER_SPECS[register_key]
        )
        if not minimum <= value <= maximum:
            raise ValueError(f"Unsupported {register_key} value: {value}")
        raw = round(value * multiplier)
        if abs(raw / multiplier - value) > 1e-9 or raw % raw_step:
            raise ValueError(f"Unsupported {register_key} increment: {value}")

        register = REGISTER_BY_KEY[register_key]
        if (
            register.address != expected_address
            or register.kind != "holding"
            or register.data_type not in (2, 7)
        ):
            raise StiebelIsgError(f"{register_key} register definition is unsafe")

        client = ModbusTcpClient(
            self._host, port=self._port, timeout=self._timeout, retries=1
        )
        try:
            if not client.connect():
                raise StiebelIsgError("Connection failed")
            time.sleep(0.05)
            response = client.write_register(
                register.address + offset, raw, device_id=self._unit_id
            )
            if response.isError():
                raise ModbusException(str(response))
            read_raw = self._read_raw(client, register, offset)
            if read_raw != raw:
                raise StiebelIsgError(
                    f"{register_key} verification failed: wrote {raw}, read {read_raw}"
                )
        except (ModbusException, OSError) as error:
            raise StiebelIsgError(str(error)) from error
        finally:
            client.close()

    async def set_number_parameter(
        self, register_key: str, value: float, offset: int
    ) -> None:
        """Set one allow-listed numeric parameter and verify it."""
        async with self._operation_lock:
            await asyncio.to_thread(
                self._set_number_parameter_sync, register_key, value, offset
            )


def _plausible(register: Register, value: float | int) -> bool:
    return (register.minimum is None or value >= register.minimum) and (
        register.maximum is None or value <= register.maximum
    )
