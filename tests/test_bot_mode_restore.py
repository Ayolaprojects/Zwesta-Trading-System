import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"c:\backend\multi_broker_backend_updated.py")
SPEC = importlib.util.spec_from_file_location("multi_broker_backend_updated", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BotModeRestoreTests(unittest.TestCase):
    def test_persisted_bot_flag_wins_over_credential_mode(self):
        row = {"bot_is_live": True, "is_live": False}
        credential_row = {"broker_name": "MT5", "is_live": False, "server": None}
        self.assertEqual(
            MODULE._derive_restored_bot_mode_from_row(row, credential_row=credential_row),
            "live",
        )

    def test_credential_mode_is_used_when_no_persisted_flag_exists(self):
        row = {"bot_is_live": None, "is_live": None}
        credential_row = {"broker_name": "MT5", "is_live": True, "server": None}
        self.assertEqual(
            MODULE._derive_restored_bot_mode_from_row(row, credential_row=credential_row),
            "live",
        )


if __name__ == "__main__":
    unittest.main()
