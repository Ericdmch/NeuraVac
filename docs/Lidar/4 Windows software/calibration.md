# calibration.py

Original file: [calibration.py](../_originals/4%20Windows%20software/calibration.py).

```python
def verify_coin_d6_correct(packet_hex):
    """
    COIN-D6 LiDAR checksum verification (correct version)

    Key finding: the byte combination order of the Si data used in the
    checksum differs from the storage order.
    Storage order:        Si_L, Si_2nd, Si_H
    Checksum combination: D5=(Si_H<<8)|Si_2nd, D6=Si_L
    """
    hex_str = packet_hex.replace(' ', '').replace('\n', '')
    data = bytes.fromhex(hex_str)

    if len(data) < 10 or data[0] != 0xAA or data[1] != 0x55:
        return False

    # Extract fields
    ph = (data[1] << 8) | data[0]
    mt = data[2]
    lsn = data[3]
    fsa = (data[5] << 8) | data[4]
    lsa = (data[7] << 8) | data[6]
    cs_expected = (data[9] << 8) | data[8]

    print("=" * 60)
    print("COIN-D6 LiDAR checksum verification (correct version)")
    print("=" * 60)
    print(f"Header (PH):             0x{ph:04X}")
    print(f"M&T:                     0x{mt:02X}")
    print(f"Sample count (LSN):      {lsn}")
    print(f"Start angle (FSA):       0x{fsa:04X}")
    print(f"End angle (LSA):         0x{lsa:04X}")
    print(f"Expected checksum (CS):  0x{cs_expected:04X}")
    print("-" * 60)

    # Try the new Si byte combination
    checksum = 0x0000

    # D1: PH
    checksum ^= ph
    print(f"D1 - PH:              0x{ph:04X} → CS = 0x{checksum:04X}")

    # D2: (LSN<<8)|M&T
    d2 = (lsn << 8) | mt
    checksum ^= d2
    print(f"D2 - (LSN<<8)|M&T:    0x{d2:04X} → CS = 0x{checksum:04X}")

    # D3: FSA
    checksum ^= fsa
    print(f"D3 - FSA:             0x{fsa:04X} → CS = 0x{checksum:04X}")

    # D4: LSA
    checksum ^= lsa
    print(f"D4 - LSA:             0x{lsa:04X} → CS = 0x{checksum:04X}")

    print("-" * 60)

    # Si data: try the new byte combination
    si_start = 10
    for i in range(lsn):
        si_offset = si_start + i * 3
        if si_offset + 2 >= len(data):
            break

        si_l = data[si_offset]
        si_2nd = data[si_offset + 1]
        si_h = data[si_offset + 2]

        # New understanding: D5=(Si_H<<8)|Si_2nd, D6=Si_L
        d5 = (si_h << 8) | si_2nd
        d6 = si_l

        checksum ^= d5
        checksum ^= d6

        if i < 3 or i >= lsn - 2:  # Show only the first 3 and last 2
            print(f"S{i+1:2d} (0x{si_h:02X}{si_2nd:02X}{si_l:02X}): D5=0x{d5:04X}, D6=0x{d6:04X} → CS = 0x{checksum:04X}")
        elif i == 3:
            print("...")

    print("-" * 60)
    print(f"Final computed checksum:  0x{checksum:04X}")
    print(f"Expected checksum:        0x{cs_expected:04X}")
    print("-" * 60)

    if checksum == cs_expected:
        print("Checksum OK!")
        return True
    else:
        print("Checksum FAILED")
        return False

if __name__ == "__main__":
    packet1 = """aa 55 00 19 7d 00 3b 0b 1f 45 88 87 02 7c 8b 02 84 93 02 84 97 02
    80 97 02 74 97 02 70 9f 02 6c 9f 02 68 a3 02 6c b3 02 6c bb 02 64 bf 02
    64 cb 02 6c d3 02 58 d7 02 4c df 02 4c e7 02 40 f3 02 3c ff 02 48 0f 03
    34 13 03 30 23 03 2c 2f 03 24 3b 03 00 47 03"""

    packet2 = """aa 55 00 19 ad 0b 87 16 f1 78 e8 52 03 e4 6a 03 c4 7a 03 a4 8e 03
    74 b2 03 8c ad 03 b8 00 00 ec 00 00 a0 9c 1c 5c f4 1f 94 14 20 44 65 1c
    58 e2 1d 18 ef 1d 38 1b 1e 74 e6 1c 14 6a 17 94 82 16 a8 8a 15 b0 86 14
    90 66 13 6c 76 12 d0 0e 14 14 b7 13 d8 9e 12"""

    print("Verify packet 1:")
    result1 = verify_coin_d6_correct(packet1)

    print("\n" + "=" * 60 + "\n")

    print("Verify packet 2:")
    result2 = verify_coin_d6_correct(packet2)

    if result1 and result2:
        print("\nBoth packets verified! Correct algorithm found!")
```
