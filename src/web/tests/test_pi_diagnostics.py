from web.pi_diagnostics import decode_throttled, parse_usb


def test_throttled_flags_distinguish_current_and_history():
    result = decode_throttled('throttled=0x50001')
    assert result['current'] == ['Undervoltage']
    assert result['history'] == ['Undervoltage', 'Throttling']
    assert decode_throttled('bad') is None


def test_usb_skips_root_hubs():
    devices = parse_usb('Bus 002 Device 002: ID 1a86:7523 QinHeng CH340\nBus 001 Device 001: ID 1d6b:0002 Linux root hub\n')
    assert devices == ['1a86:7523 QinHeng CH340']
