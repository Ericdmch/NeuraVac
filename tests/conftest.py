import os

import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        if "hardware" in item.keywords and os.getenv("NEURAVAC_ALLOW_HARDWARE_TESTS") != "1":
            item.add_marker(
                pytest.mark.skip(reason="Set NEURAVAC_ALLOW_HARDWARE_TESTS=1 for physical devices")
            )
        if "cloud" in item.keywords and os.getenv("NEURAVAC_ALLOW_CLOUD_TESTS") != "1":
            item.add_marker(
                pytest.mark.skip(reason="Set NEURAVAC_ALLOW_CLOUD_TESTS=1 for billed API calls")
            )
