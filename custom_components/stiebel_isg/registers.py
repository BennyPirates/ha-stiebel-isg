"""Officially documented WPMsystem registers used by Home Assistant."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Register:
    key: str
    address: int
    kind: str
    name: str
    data_type: int
    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    cooling: bool = False


# Addresses and data types are from STIEBEL ELTRON DM0000040850.
REGISTERS: tuple[Register, ...] = (
    Register("outside_temperature", 507, "input", "Outside temperature", 2, "°C", "temperature", "measurement", -60, 80),
    Register("hc1_actual_temperature", 508, "input", "HC1 actual temperature", 2, "°C", "temperature", "measurement", 0, 40),
    Register("hc1_set_temperature", 510, "input", "HC1 set temperature", 2, "°C", "temperature", "measurement", 0, 40),
    Register("flow_temperature", 513, "input", "Heat pump flow temperature", 2, "°C", "temperature", "measurement", -20, 120),
    Register("return_temperature", 516, "input", "Return temperature", 2, "°C", "temperature", "measurement", 0, 90),
    Register("buffer_temperature", 518, "input", "Buffer temperature", 2, "°C", "temperature", "measurement", 0, 90),
    Register("heating_pressure", 520, "input", "Heating pressure", 7, "bar", "pressure", "measurement", 0, 10),
    Register("dhw_temperature", 522, "input", "DHW temperature", 2, "°C", "temperature", "measurement", 10, 65),
    Register("dhw_set_temperature", 523, "input", "DHW set temperature", 2, "°C", "temperature", "measurement", 10, 65),
    Register("source_temperature", 536, "input", "Source temperature", 2, "°C", "temperature", "measurement", -50, 80),
    Register("hp1_hot_gas_temperature", 544, "input", "HP1 hot gas temperature", 2, "°C", "temperature", "measurement", -50, 200),
    Register("hp1_water_flow", 548, "input", "HP1 water flow", 2, "L/min", "volume_flow_rate", "measurement", 0, 150),
    Register("hc1_room_temperature", 584, "input", "HC1 room temperature", 2, "°C", "temperature", "measurement", -10, 50),
    Register("hc1_relative_humidity", 586, "input", "HC1 relative humidity", 2, "%", "humidity", "measurement", 0, 100),
    Register("hc1_dew_point", 587, "input", "HC1 dew point", 2, "°C", "temperature", "measurement", -40, 40),
    Register("cooling_room_set_temperature", 604, "input", "Cooling room set temperature", 2, "°C", "temperature", "measurement", 5, 35, True),
    Register("operating_mode", 1501, "holding", "Operating mode", 8, minimum=0, maximum=5),
    Register("hc1_comfort_temperature", 1502, "holding", "HC1 comfort temperature", 2, "°C", "temperature", "measurement", 5, 30),
    Register("hc1_eco_temperature", 1503, "holding", "HC1 eco temperature", 2, "°C", "temperature", "measurement", 5, 30),
    Register("hc1_heating_curve", 1504, "holding", "HC1 heating curve rise", 7, minimum=0, maximum=3),
    Register("dhw_comfort_temperature", 1510, "holding", "DHW comfort temperature", 2, "°C", "temperature", "measurement", 10, 60),
    Register("dhw_eco_temperature", 1511, "holding", "DHW eco temperature", 2, "°C", "temperature", "measurement", 10, 60),
    Register("area_cooling_flow_set", 1514, "holding", "Area cooling flow set temperature", 2, "°C", "temperature", "measurement", 7, 25, True),
    Register("operating_status", 2501, "input", "Operating status", 6),
    Register("fault_status", 2504, "input", "Fault status", 6, minimum=0, maximum=1),
    Register("bus_status", 2505, "input", "Bus status", 6, minimum=-4, maximum=0),
    Register("active_error", 2507, "input", "Active error number", 6, minimum=0, maximum=65535),
    Register("heat_heating_today", 3501, "input", "Heat output heating today", 6, "kWh", "energy", "total", 0, 65535),
    Register("heat_dhw_today", 3504, "input", "Heat output DHW today", 6, "kWh", "energy", "total", 0, 65535),
    Register("electricity_heating_today", 3511, "input", "Electricity heating today", 6, "kWh", "energy", "total", 0, 65535),
    Register("electricity_dhw_today", 3514, "input", "Electricity DHW today", 6, "kWh", "energy", "total", 0, 65535),
    Register("compressor_heating_runtime", 3539, "input", "Compressor heating runtime", 6, "h", "duration", "total_increasing", 0, 65535),
    Register("compressor_dhw_runtime", 3542, "input", "Compressor DHW runtime", 6, "h", "duration", "total_increasing", 0, 65535),
    Register("cooling_runtime", 3545, "input", "Cooling runtime", 6, "h", "duration", "total_increasing", 0, 65535, True),
    Register("sg_ready_state", 5001, "input", "SG Ready state", 6, minimum=0, maximum=4),
    Register("controller_identification", 5002, "input", "Controller identification", 6, minimum=0, maximum=65535),
)

REGISTER_BY_KEY = {register.key: register for register in REGISTERS}
OFFSET_PROBES = ("outside_temperature", "hc1_actual_temperature", "return_temperature", "dhw_temperature", "fault_status")
STATUS_BITS = {
    "hc1_pump": (0, "HC1 pump"), "hc2_pump": (1, "HC2 pump"),
    "backup_heater": (3, "Backup heater"), "heating": (4, "Heating"),
    "dhw": (5, "DHW"), "compressor": (6, "Compressor"),
    "summer_mode": (7, "Summer mode"), "cooling": (8, "Cooling"),
    "defrost": (9, "Defrost"),
}
