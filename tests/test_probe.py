import unittest

from src.stiebel_isg_probe import Register, decode, make_result, signed16


class DecodeTests(unittest.TestCase):
    def test_signed16(self):
        self.assertEqual(signed16(0xFFFF), -1)
        self.assertEqual(signed16(0x7FFF), 32767)

    def test_type_2_temperature(self):
        self.assertEqual(decode(203, 2), 20.3)
        self.assertEqual(decode(0xFFCE, 2), -5.0)

    def test_type_7_pressure(self):
        self.assertEqual(decode(123, 7), 1.23)

    def test_unavailable_precedes_signed_decode(self):
        result = make_result(Register(507, "input", "Outside", 2, "°C", -60, 80), -1, 0x8000)
        self.assertEqual(result.availability, "unavailable")
        self.assertIsNone(result.decoded_value)

    def test_implausible(self):
        result = make_result(Register(507, "input", "Outside", 2, "°C", -60, 80), -1, 1000)
        self.assertEqual(result.plausibility, "implausible")

    def test_fixed_temperature_off_encoding(self):
        result = make_result(Register(1508, "holding", "Fixed", 2, "°C", 20, 70), -1, 0x9000)
        self.assertEqual(result.decoded_value, "off")
        self.assertEqual(result.plausibility, "plausible")


if __name__ == "__main__":
    unittest.main()
