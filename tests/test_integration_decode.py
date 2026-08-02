"""Library-level tests that do not require a Home Assistant installation."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / "custom_components" / "stiebel_isg"


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, COMPONENT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


package = types.ModuleType("custom_components.stiebel_isg")
package.__path__ = [str(COMPONENT)]
sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
sys.modules["custom_components.stiebel_isg"] = package
_load_module("custom_components.stiebel_isg.const", "const.py")
_load_module("custom_components.stiebel_isg.registers", "registers.py")
api = _load_module("custom_components.stiebel_isg.api", "api.py")


class IntegrationSourceTests(unittest.TestCase):
    def test_runtime_contains_only_allowlisted_single_register_writes(self):
        source = "\n".join(path.read_text() for path in COMPONENT.glob("*.py"))
        for forbidden in (
            "write_registers",
            "write_coil",
            "write_coils",
        ):
            self.assertNotIn(forbidden, source)
        self.assertEqual(source.count("client.write_register("), 2)

    def test_manifest_is_present(self):
        manifest = COMPONENT / "manifest.json"
        self.assertTrue(manifest.is_file())

    def test_signed_temperature_decode(self):
        self.assertEqual(api.decode(203, 2), 20.3)
        self.assertEqual(api.decode(0xFFCE, 2), -5.0)

    def test_pressure_decode(self):
        self.assertEqual(api.decode(130, 7), 1.3)

    def test_status_decode_is_unsigned(self):
        self.assertEqual(api.decode(0xFFFF, 6), 65535)


class OperatingModeWriteTests(unittest.TestCase):
    def setUp(self):
        self.client = api.StiebelIsgClient("isg.local", 502, 1, 3.0)

    @patch("custom_components.stiebel_isg.api.time.sleep")
    @patch("custom_components.stiebel_isg.api.ModbusTcpClient")
    def test_writes_fc06_to_offset_address_and_verifies(self, client_class, _sleep):
        modbus = client_class.return_value
        modbus.connect.return_value = True
        modbus.write_register.return_value.isError.return_value = False
        read_response = MagicMock()
        read_response.isError.return_value = False
        read_response.registers = [3]
        modbus.read_holding_registers.return_value = read_response

        self.client._set_operating_mode_sync(3, -1)

        modbus.write_register.assert_called_once_with(1500, 3, device_id=1)
        modbus.read_holding_registers.assert_called_once_with(
            1500, count=1, device_id=1
        )
        modbus.close.assert_called_once()

    @patch("custom_components.stiebel_isg.api.ModbusTcpClient")
    def test_rejects_undocumented_mode_before_connecting(self, client_class):
        with self.assertRaises(ValueError):
            self.client._set_operating_mode_sync(6, -1)
        client_class.assert_not_called()

    @patch("custom_components.stiebel_isg.api.ModbusTcpClient")
    def test_rejects_unknown_offset_before_connecting(self, client_class):
        with self.assertRaises(ValueError):
            self.client._set_operating_mode_sync(3, 1)
        client_class.assert_not_called()

    @patch("custom_components.stiebel_isg.api.time.sleep")
    @patch("custom_components.stiebel_isg.api.ModbusTcpClient")
    def test_fails_when_readback_does_not_match(self, client_class, _sleep):
        modbus = client_class.return_value
        modbus.connect.return_value = True
        modbus.write_register.return_value.isError.return_value = False
        read_response = MagicMock()
        read_response.isError.return_value = False
        read_response.registers = [2]
        modbus.read_holding_registers.return_value = read_response

        with self.assertRaisesRegex(api.StiebelIsgError, "verification failed"):
            self.client._set_operating_mode_sync(3, -1)


class WritableNumberTests(unittest.TestCase):
    def setUp(self):
        self.client = api.StiebelIsgClient("isg.local", 502, 1, 3.0)

    @patch("custom_components.stiebel_isg.api.time.sleep")
    @patch("custom_components.stiebel_isg.api.ModbusTcpClient")
    def test_writes_scaled_temperature_and_verifies(self, client_class, _sleep):
        modbus = client_class.return_value
        modbus.connect.return_value = True
        modbus.write_register.return_value.isError.return_value = False
        read_response = MagicMock()
        read_response.isError.return_value = False
        read_response.registers = [200]
        modbus.read_holding_registers.return_value = read_response

        self.client._set_number_parameter_sync("hc1_eco_temperature", 20.0, -1)

        modbus.write_register.assert_called_once_with(1502, 200, device_id=1)
        modbus.read_holding_registers.assert_called_once_with(
            1502, count=1, device_id=1
        )

    @patch("custom_components.stiebel_isg.api.ModbusTcpClient")
    def test_rejects_out_of_range_before_connecting(self, client_class):
        with self.assertRaises(ValueError):
            self.client._set_number_parameter_sync("hc1_eco_temperature", 30.1, -1)
        client_class.assert_not_called()

    @patch("custom_components.stiebel_isg.api.ModbusTcpClient")
    def test_rejects_unsupported_precision_before_connecting(self, client_class):
        with self.assertRaises(ValueError):
            self.client._set_number_parameter_sync("hc1_eco_temperature", 20.05, -1)
        client_class.assert_not_called()

    @patch("custom_components.stiebel_isg.api.ModbusTcpClient")
    def test_rejects_non_allowlisted_register_before_connecting(self, client_class):
        with self.assertRaises(ValueError):
            self.client._set_number_parameter_sync("fixed_temperature", 30.0, -1)
        client_class.assert_not_called()

    @patch("custom_components.stiebel_isg.api.time.sleep")
    @patch("custom_components.stiebel_isg.api.ModbusTcpClient")
    def test_writes_scaled_heating_curve(self, client_class, _sleep):
        modbus = client_class.return_value
        modbus.connect.return_value = True
        modbus.write_register.return_value.isError.return_value = False
        read_response = MagicMock()
        read_response.isError.return_value = False
        read_response.registers = [55]
        modbus.read_holding_registers.return_value = read_response

        self.client._set_number_parameter_sync("hc1_heating_curve", 0.55, 0)

        modbus.write_register.assert_called_once_with(1504, 55, device_id=1)

    @patch("custom_components.stiebel_isg.api.ModbusTcpClient")
    def test_rejects_invalid_dhw_half_degree_step(self, client_class):
        with self.assertRaises(ValueError):
            self.client._set_number_parameter_sync("dhw_comfort_temperature", 50.1, -1)
        client_class.assert_not_called()


if __name__ == "__main__":
    unittest.main()
