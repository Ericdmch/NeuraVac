from roomba_interfaces.msg import SerialData

def roomba_drive(velocity, radius) -> SerialData:
    # & 0xFFFF gives the 16-bit two's-complement value the Roomba expects,
    # and lets 32768 (straight) fit
    velocity_bytes = (int(velocity) & 0xFFFF).to_bytes(2, byteorder='big')
    radius_bytes = (int(radius) & 0xFFFF).to_bytes(2, byteorder='big')

    command = [137] + list(velocity_bytes) + list(radius_bytes)
    return SerialData(data=command)