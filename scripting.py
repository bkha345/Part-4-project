def setVoltage(bus, address, destination, voltageDecimal):
    """
    :param bus: The bus that the sensor is connected to
    :param address: The address of the rail that we want to read
    :param destination: The actual value inside the rail (See datasheet)
    :param voltageDecimal: The voltage to be written to the rail AS A DECIMAL
    :return: None
    """

    # voltageDecimal # This needs to be converted to a value between 0 and 4096 and written into hex
    if voltageDecimal < 0 or voltageDecimal > 1: # out of bounds
        raise Exception(f"Voltage must be between 0 and 1, entered voltage: {voltageDecimal}")

    try:
        bus.write_word_data(address, destination, (int(voltageDecimal*4096)))
        return True
    except OSError as e:
        print(f"Error writing to device at address {hex(address)}: {e}")
        return False


def write_data(bus, device_address, location, voltageDecimal):
    try:
        bus.write_word_data(device_address, location, hex(int(voltageDecimal*4096)))
        return True
    except OSError as e:
        print(f"Error writing to device at address {hex(device_address)}: {e}")
        return False





limit = 4095
b = hex(0)
for i in range(0, limit, 1): # This could be made more fine
    a = setVoltage(1, 1, 1, i/limit)

    print(i/limit, a, int(a, 16) - int(b, 16))

    b = a

    # write_data(smbus2.SMBus(4), 0x13, 0x21, 0x0CCC)