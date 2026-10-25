import os
import unittest
from unittest.mock import patch

from config.settings import get_settings


class SettingsTests(unittest.TestCase):
    def test_operational_values_are_loaded_from_environment(self) -> None:
        values = {
            "SUPPORT_DB_TIMEOUT_SECONDS": "2.5",
            "SUPPORT_TICKET_LIST_LIMIT": "25",
            "SUPPORT_TICKET_ID_GENERATION_ATTEMPTS": "3",
        }
        with patch.dict(os.environ, values):
            settings = get_settings()

        self.assertEqual(settings.database_timeout_seconds, 2.5)
        self.assertEqual(settings.ticket_list_limit, 25)
        self.assertEqual(settings.ticket_id_generation_attempts, 3)

    def test_nonpositive_integer_setting_is_rejected(self) -> None:
        with patch.dict(os.environ, {"SUPPORT_TICKET_LIST_LIMIT": "0"}):
            with self.assertRaisesRegex(
                ValueError, "SUPPORT_TICKET_LIST_LIMIT must be a positive integer"
            ):
                get_settings()

    def test_invalid_database_timeout_is_rejected(self) -> None:
        with patch.dict(os.environ, {"SUPPORT_DB_TIMEOUT_SECONDS": "inf"}):
            with self.assertRaisesRegex(
                ValueError, "SUPPORT_DB_TIMEOUT_SECONDS must be a positive finite number"
            ):
                get_settings()


if __name__ == "__main__":
    unittest.main()
