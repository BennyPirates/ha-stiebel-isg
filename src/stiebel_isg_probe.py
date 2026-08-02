#!/usr/bin/env python3
"""Strictly read-only STIEBEL ELTRON ISG Modbus TCP diagnostic probe."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import socket
import sys
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

UNAVAILABLE = 0x8000
DOC_URL = (
    "https://www.stiebel-eltron.de/static/ste/docportal/manual/DM0000040850-hqy.pdf"
)


@dataclass(frozen=True)
class Register:
    address: int
    kind: str
    name: str
    data_type: int
    unit: str = ""
    minimum: float | None = None
    maximum: float | None = None
    meaning: str = "documented"


@dataclass
class Result:
    address: int
    pdu_address: int
    register_type: str
    function_code: int
    name: str
    raw_value: int | None
    raw_hex: str | None
    data_type: int | None
    scaling: float | None
    decoded_value: float | int | str | None
    unit: str
    availability: str
    plausibility: str
    meaning: str
    error: str | None = None


# Official WPMsystem core registers. Names are concise English renderings of
# chapter 6; addresses, types, units and bounds follow the official table.
REGISTERS = [
    Register(501, "input", "FE7 actual temperature", 2, "°C", -40, 60),
    Register(502, "input", "FE7 set temperature", 2, "°C", 5, 35),
    Register(507, "input", "Outside temperature", 2, "°C", -60, 80),
    Register(508, "input", "HC1 actual temperature", 2, "°C", 0, 40),
    Register(510, "input", "HC1 set temperature", 2, "°C", 0, 40),
    Register(511, "input", "HC2 actual temperature", 2, "°C", 0, 90),
    Register(512, "input", "HC2 set temperature", 2, "°C", 0, 65),
    Register(513, "input", "HP actual flow temperature", 2, "°C", -20, 120),
    Register(514, "input", "Backup heater flow temperature", 2, "°C", -20, 120),
    Register(515, "input", "Actual flow temperature", 2, "°C", -20, 120),
    Register(516, "input", "Actual return temperature", 2, "°C", 0, 90),
    Register(518, "input", "Actual buffer temperature", 2, "°C", 0, 90),
    Register(519, "input", "Set buffer temperature", 2, "°C", 0, 90),
    Register(520, "input", "Heating pressure", 7, "bar", 0, 10),
    Register(521, "input", "Flow rate", 2, "l/min", 0, 150),
    Register(522, "input", "DHW actual temperature", 2, "°C", 10, 65),
    Register(523, "input", "DHW set temperature", 2, "°C", 10, 65),
    Register(524, "input", "Fan cooling actual delta", 2, "K", -30, 30),
    Register(525, "input", "Fan cooling set delta", 2, "K", 7, 25),
    Register(526, "input", "Area cooling actual delta", 2, "K", -30, 30),
    Register(527, "input", "Area cooling set delta", 2, "K", -30, 30),
    Register(533, "input", "Heating application limit", 2, "°C", -40, 40),
    Register(534, "input", "DHW application limit", 2, "°C", -40, 40),
    Register(536, "input", "Source temperature", 2, "°C", -50, 80),
    Register(542, "input", "HP1 return temperature", 2, "°C", -20, 120),
    Register(543, "input", "HP1 flow temperature", 2, "°C", -20, 120),
    Register(544, "input", "HP1 hot gas temperature", 2, "°C", -50, 200),
    Register(545, "input", "HP1 low pressure", 7, "bar", 0, 50),
    Register(547, "input", "HP1 high pressure", 7, "bar", 0, 80),
    Register(548, "input", "HP1 water flow rate", 2, "l/min", 0, 150),
    Register(584, "input", "HC1 room actual temperature", 2, "°C", -10, 50),
    Register(585, "input", "HC1 room set temperature", 2, "°C", 5, 35),
    Register(586, "input", "HC1 relative humidity", 2, "%", 0, 100),
    Register(587, "input", "HC1 dew point", 2, "°C", -40, 40),
    Register(604, "input", "Cooling circuit 1 room set temperature", 2, "°C", 5, 35),
    Register(1501, "holding", "Operating mode", 8, "", 0, 5),
    Register(1502, "holding", "HC1 comfort temperature", 2, "°C", 5, 30),
    Register(1503, "holding", "HC1 eco temperature", 2, "°C", 5, 30),
    Register(1504, "holding", "HC1 heating curve rise", 7, "", 0, 3),
    Register(1505, "holding", "HC2 comfort temperature", 2, "°C", 5, 30),
    Register(1506, "holding", "HC2 eco temperature", 2, "°C", 5, 30),
    Register(1507, "holding", "HC2 heating curve rise", 7, "", 0, 3),
    Register(1508, "holding", "Fixed value operation", 2, "°C", 20, 70),
    Register(1509, "holding", "Heating dual mode temperature", 2, "°C", -40, 40),
    Register(1510, "holding", "DHW comfort temperature", 2, "°C", 10, 60),
    Register(1511, "holding", "DHW eco temperature", 2, "°C", 10, 60),
    Register(1512, "holding", "DHW stages", 8, "", 0, 6),
    Register(1513, "holding", "DHW dual mode temperature", 2, "°C", -40, 40),
    Register(1514, "holding", "Area cooling set flow temperature", 2, "°C", 7, 25),
    Register(1515, "holding", "Area cooling flow hysteresis", 2, "K", 1, 5),
    Register(1516, "holding", "Area cooling room set temperature", 2, "°C", 20, 30),
    Register(1517, "holding", "Fan cooling set flow temperature", 2, "°C", 7, 25),
    Register(1518, "holding", "Fan cooling flow hysteresis", 2, "K", 1, 5),
    Register(1519, "holding", "Fan cooling room set temperature", 2, "°C", 20, 30),
    Register(2501, "input", "Operating status bitfield", 6),
    Register(2502, "input", "Power-off bitfield", 8),
    Register(2504, "input", "Fault status", 6, "", 0, 1),
    Register(2505, "input", "Bus status", 6, "", -4, 0),
    Register(2506, "input", "Defrost initiated", 6, "", 0, 1),
    Register(2507, "input", "Active error number", 6, "", 0, 65535),
    Register(5001, "input", "SG Ready operating state", 6, "", 1, 4),
    Register(5002, "input", "Controller identification", 6, "", 0, 65535),
]

# Official energy block. Keep generic rows explicit enough for an audit while
# avoiding invented semantics beyond the table.
for address, name, unit, maximum in [
    (3501, "Heat output heating today (all HP)", "kWh", 65535),
    (3502, "Heat output heating total remainder (all HP)", "kWh", 999),
    (3503, "Heat output heating total (all HP)", "MWh", 65535),
    (3504, "Heat output DHW today (all HP)", "kWh", 65535),
    (3505, "Heat output DHW total remainder (all HP)", "kWh", 999),
    (3506, "Heat output DHW total (all HP)", "MWh", 65535),
    (3511, "Electricity heating today (all HP)", "kWh", 65535),
    (3512, "Electricity heating total remainder (all HP)", "kWh", 999),
    (3513, "Electricity heating total (all HP)", "MWh", 65535),
    (3514, "Electricity DHW today (all HP)", "kWh", 65535),
    (3515, "Electricity DHW total remainder (all HP)", "kWh", 999),
    (3516, "Electricity DHW total (all HP)", "MWh", 65535),
    (3523, "Heat output heating today HP1", "kWh", 65535),
    (3524, "Heat output heating total remainder HP1", "kWh", 999),
    (3525, "Heat output heating total HP1", "MWh", 65535),
    (3526, "Heat output DHW today HP1", "kWh", 65535),
    (3527, "Heat output DHW total remainder HP1", "kWh", 999),
    (3528, "Heat output DHW total HP1", "MWh", 65535),
    (3533, "Electricity heating today HP1", "kWh", 65535),
    (3534, "Electricity heating total remainder HP1", "kWh", 999),
    (3535, "Electricity heating total HP1", "MWh", 65535),
    (3536, "Electricity DHW today HP1", "kWh", 65535),
    (3537, "Electricity DHW total remainder HP1", "kWh", 999),
    (3538, "Electricity DHW total HP1", "MWh", 65535),
    (3539, "Compressor 1 heating runtime HP1", "h", 65535),
    (3542, "Compressor 1 DHW runtime HP1", "h", 65535),
    (3545, "Cooling runtime HP1", "h", 65535),
    (3644, "Heating runtime HP1 (WPMsystem)", "h", 65535),
    (3645, "DHW runtime HP1 (WPMsystem)", "h", 65535),
]:
    REGISTERS.append(Register(address, "input", name, 6, unit, 0, maximum))

# Cover every address in the four official WPM blocks, including entries not
# prioritised above. Their datatype follows the official table; a deliberately
# generic label is preferable to inventing a more specific meaning.
_existing = {(r.kind, r.address) for r in REGISTERS}
for address in range(501, 609):
    if ("input", address) not in _existing:
        data_type = (
            7
            if address
            in {
                538,
                540,
                541,
                545,
                546,
                547,
                552,
                553,
                554,
                559,
                560,
                561,
                566,
                567,
                568,
                573,
                574,
                575,
                580,
                581,
                582,
            }
            else (6 if address in {530, 535} else 2)
        )
        REGISTERS.append(
            Register(
                address,
                "input",
                "Documented WPM system value",
                data_type,
                meaning="documented_unlabelled",
            )
        )
for start, end in ((2501, 2547), (3501, 3655)):
    for address in range(start, end + 1):
        if ("input", address) not in _existing:
            REGISTERS.append(
                Register(
                    address,
                    "input",
                    "Documented WPM status/energy value",
                    6,
                    meaning="documented_unlabelled",
                )
            )

REGISTERS.sort(key=lambda r: (r.address, r.kind))

REGISTER_MAP = {(r.kind, r.address): r for r in REGISTERS}
TYPE_SCALE = {2: 0.1, 6: 1.0, 7: 0.01, 8: 1.0}
SIGNED_TYPES = {2, 7}
OFFSET_PROBES = [507, 508, 516, 522, 2504]
STATUS_BITS = {
    0: "HC1 pump",
    1: "HC2 pump",
    2: "heat-up program",
    3: "backup heater",
    4: "heating",
    5: "DHW",
    6: "compressor",
    7: "summer mode",
    8: "cooling",
    9: "defrost",
    10: "silent 1",
    11: "silent 2",
}


def signed16(raw: int) -> int:
    return raw - 0x10000 if raw & 0x8000 else raw


def decode(raw: int, data_type: int) -> float | int:
    value = signed16(raw) if data_type in SIGNED_TYPES else raw
    scaled = value * TYPE_SCALE[data_type]
    return int(scaled) if TYPE_SCALE[data_type] == 1 else round(scaled, 4)


def plausible(reg: Register, value: float | int) -> bool:
    return (reg.minimum is None or value >= reg.minimum) and (
        reg.maximum is None or value <= reg.maximum
    )


class ReadOnlyProbe:
    """Small wrapper exposing only Modbus read calls (FC03 and FC04)."""

    def __init__(self, host: str, port: int, unit: int, timeout: float, delay: float):
        self.client = ModbusTcpClient(host, port=port, timeout=timeout, retries=1)
        self.unit = unit
        self.delay = delay

    def connect(self) -> bool:
        return self.client.connect()

    def close(self) -> None:
        self.client.close()

    def read_one(self, kind: str, pdu_address: int) -> int:
        time.sleep(self.delay)
        method = (
            self.client.read_input_registers
            if kind == "input"
            else self.client.read_holding_registers
        )
        response = method(pdu_address, count=1, device_id=self.unit)
        if response.isError():
            raise ModbusException(str(response))
        if not getattr(response, "registers", None):
            raise ModbusException("response contains no registers")
        return int(response.registers[0])


def score_offset(probe: ReadOnlyProbe, offset: int) -> tuple[int, list[str]]:
    score, notes = 0, []
    for address in OFFSET_PROBES:
        reg = REGISTER_MAP[("input", address)]
        try:
            raw = probe.read_one("input", address + offset)
            if raw == UNAVAILABLE:
                notes.append(f"{address}: unavailable")
                continue
            value = decode(raw, reg.data_type)
            ok = plausible(reg, value)
            score += 3 if ok else -2
            notes.append(
                f"{address}: {value} {reg.unit} ({'ok' if ok else 'implausible'})"
            )
        except Exception as exc:  # network/protocol failures belong in diagnostics
            score -= 3
            notes.append(f"{address}: error: {exc}")
    return score, notes


def make_result(
    reg: Register, offset: int, raw: int | None, error: str | None = None
) -> Result:
    if error:
        return Result(
            reg.address,
            reg.address + offset,
            reg.kind,
            4 if reg.kind == "input" else 3,
            reg.name,
            None,
            None,
            reg.data_type,
            TYPE_SCALE.get(reg.data_type),
            None,
            reg.unit,
            "error",
            "unknown",
            reg.meaning,
            error,
        )
    assert raw is not None
    if raw == UNAVAILABLE:
        return Result(
            reg.address,
            reg.address + offset,
            reg.kind,
            4 if reg.kind == "input" else 3,
            reg.name,
            raw,
            f"0x{raw:04X}",
            reg.data_type,
            TYPE_SCALE.get(reg.data_type),
            None,
            reg.unit,
            "unavailable",
            "not_applicable",
            reg.meaning,
        )
    if reg.address in {517, 1508} and raw == 0x9000:
        return Result(
            reg.address,
            reg.address + offset,
            reg.kind,
            4 if reg.kind == "input" else 3,
            reg.name,
            raw,
            f"0x{raw:04X}",
            reg.data_type,
            TYPE_SCALE.get(reg.data_type),
            "off",
            reg.unit,
            "available",
            "plausible",
            reg.meaning,
        )
    value = decode(raw, reg.data_type)
    return Result(
        reg.address,
        reg.address + offset,
        reg.kind,
        4 if reg.kind == "input" else 3,
        reg.name,
        raw,
        f"0x{raw:04X}",
        reg.data_type,
        TYPE_SCALE[reg.data_type],
        value,
        reg.unit,
        "available",
        "plausible" if plausible(reg, value) else "implausible",
        reg.meaning,
    )


def candidate_registers() -> Iterable[Register]:
    # Narrow gaps/edges next to official WPM blocks; semantics deliberately unknown.
    for start, end, kind in [
        (609, 620, "input"),
        (1522, 1530, "holding"),
        (2548, 2560, "input"),
        (3656, 3670, "input"),
    ]:
        for address in range(start, end + 1):
            yield Register(
                address,
                kind,
                "Unknown responding register candidate",
                6,
                meaning="candidate",
            )


def write_outputs(
    results: list[Result], metadata: dict, output_dir: Path
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"stiebel_probe_{stamp}.json"
    csv_path = output_dir / f"stiebel_probe_{stamp}.csv"
    json_path.write_text(
        json.dumps(
            {"metadata": metadata, "registers": [asdict(r) for r in results]},
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(r) for r in results)
    return json_path, csv_path


def print_results(results: list[Result]) -> None:
    print(
        "\nAddr  Art      Rohwert  Wert          Einheit  Verfügbarkeit  "
        "Plausibilität  Bezeichnung"
    )
    print("-" * 112)
    for r in results:
        raw = "-" if r.raw_value is None else str(r.raw_value)
        value = "-" if r.decoded_value is None else str(r.decoded_value)
        print(
            f"{r.address:5}  {r.register_type:7}  {raw:7}  {value:12}  {r.unit:7}  "
            f"{r.availability:14} {r.plausibility:15} {r.name}"
        )
        if r.address == 2501 and isinstance(r.decoded_value, int):
            active = [
                name
                for bit, name in STATUS_BITS.items()
                if r.decoded_value & (1 << bit)
            ]
            print("       Aktive Statusbits: " + (", ".join(active) or "keine"))
    counts = {
        state: sum(r.availability == state for r in results)
        for state in ("available", "unavailable", "error")
    }
    implausible = sum(r.plausibility == "implausible" for r in results)
    print(
        f"\nZusammenfassung: {counts['available']} verfügbar, "
        f"{counts['unavailable']} nicht verfügbar, "
        f"{counts['error']} Fehler, {implausible} unplausibel"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only STIEBEL ISG Modbus diagnostic probe"
    )
    parser.add_argument("host", help="ISG IPv4 address or hostname")
    parser.add_argument("--port", type=int, default=502)
    parser.add_argument("--unit", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument(
        "--delay",
        type=float,
        default=0.08,
        help="delay before every request in seconds (minimum 0.05)",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument(
        "--scan-candidates",
        action="store_true",
        help="scan only four small adjacent ranges; unknown meanings stay candidates",
    )
    parser.add_argument(
        "--offset",
        type=int,
        choices=(-1, 0),
        help="override automatic offset detection",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.delay < 0.05:
        raise SystemExit("--delay must be at least 0.05 seconds")
    try:
        socket.getaddrinfo(args.host, args.port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise SystemExit(f"Invalid/unresolvable host {args.host!r}: {exc}") from exc
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)
    probe = ReadOnlyProbe(args.host, args.port, args.unit, args.timeout, args.delay)
    if not probe.connect():
        raise SystemExit(f"Connection to {args.host}:{args.port} failed")
    try:
        scores: dict[int, int | str] = {}
        notes: dict[int, list[str]] = {}
        if args.offset is None:
            for candidate in (-1, 0):
                scores[candidate], notes[candidate] = score_offset(probe, candidate)
            print("Offset-Erkennung:")
            for candidate in (-1, 0):
                print(
                    f"  Offset {candidate:+}: score {scores[candidate]} — "
                    + "; ".join(notes[candidate])
                )
            numeric_scores = {key: int(value) for key, value in scores.items()}
            if (
                numeric_scores[-1] == numeric_scores[0]
                or max(numeric_scores.values()) <= 0
            ):
                raise SystemExit(
                    "Offset cannot be determined safely; use --offset only after "
                    "reviewing readings"
                )
            offset = max(
                numeric_scores, key=lambda candidate: numeric_scores[candidate]
            )
        else:
            offset = args.offset
            scores = {offset: "manual override"}
        print(f"Gewählter Dokument→PDU-Offset: {offset:+}")

        definitions = list(REGISTERS)
        if args.scan_candidates:
            definitions.extend(candidate_registers())
        results = []
        for reg in definitions:
            try:
                raw = probe.read_one(reg.kind, reg.address + offset)
                # Candidate 0x8000 carries no evidence that an object responds.
                if reg.meaning == "candidate" and raw == UNAVAILABLE:
                    continue
                results.append(make_result(reg, offset, raw))
            except (ModbusException, OSError, TimeoutError) as exc:
                # A failed adjacent probe proves no responding unknown object.
                # Documented failures remain valuable compatibility evidence.
                if reg.meaning != "candidate":
                    results.append(make_result(reg, offset, None, str(exc)))
    finally:
        probe.close()

    metadata = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "host": args.host,
        "port": args.port,
        "unit_id": args.unit,
        "offset": offset,
        "offset_scores": scores,
        "read_only": True,
        "function_codes": [3, 4],
        "candidate_scan": args.scan_candidates,
        "documentation": DOC_URL,
    }
    print_results(results)
    json_path, csv_path = write_outputs(results, metadata, args.output_dir)
    print(f"\nJSON: {json_path}\nCSV:  {csv_path}")
    return 0 if not any(r.availability == "error" for r in results) else 2


if __name__ == "__main__":
    sys.exit(main())
