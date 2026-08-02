"""Library-level tests that do not require a Home Assistant installation."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest


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
    def test_runtime_contains_no_modbus_write_calls(self):
        source = "\n".join(path.read_text() for path in COMPONENT.glob("*.py"))
        for forbidden in ("write_register", "write_registers", "write_coil", "write_coils"):
            self.assertNotIn(forbidden, source)

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


if __name__ == "__main__":
    unittest.main()
