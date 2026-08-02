"""Constants for the STIEBEL ISG integration."""

DOMAIN = "stiebel_isg"
DEFAULT_NAME = "STIEBEL ISG"
DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 1
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_TIMEOUT = 3.0
CONF_UNIT_ID = "unit_id"
CONF_OFFSET = "address_offset"
UNAVAILABLE_RAW = 0x8000
PLATFORMS = ["sensor", "binary_sensor", "select", "number"]

OPERATING_MODE_TO_VALUE = {
    "emergency": 0,
    "standby": 1,
    "program": 2,
    "comfort": 3,
    "eco": 4,
    "dhw": 5,
}
OPERATING_MODE_FROM_VALUE = {
    value: option for option, value in OPERATING_MODE_TO_VALUE.items()
}
