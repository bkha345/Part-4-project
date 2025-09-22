import os
import glob
import smbus2
import time
import threading
import subprocess
import argparse


# This is to pass the argument to switch between power advantage and UART
parser = argparse.ArgumentParser(description='PA or UART')
parser.add_argument('--threaded', type=str, required=False, help='see source for details')
# parser.add_argument('--threaded', type=str, required=True, help='see source for details')
# if true, this --threaded argument will run in a way to allow UART to capture the output
# if false, this --threaded argument will run without being threaded to allow power advantage to capture the output

args = parser.parse_args()
print(f"Option: {args.threaded}")
if args.threaded:
    isThreaded = args.threaded.lower() == 'true'
    print(f"isThreaded: {isThreaded} {type(isThreaded)}")
else:
    isThreaded = False # default
# define out here
stop_event = threading.Event()

lookup = {
        "ina226_u16" : "VCC3V3",
        "ina226_u80" : "VCCAUX",
        "ina226_u93" : "VCCO_PSDDR_504",
        "ina226_u79" : "VCCINT",
        "ina226_u85" : "MGTRAVCC",
        "ina226_u15" : "VCCOPS3",
        "ina226_u78" : "VCCPSAUX",
        "ina226_u75" : "MGTAVTT",
        "ina226_u76" : "VCCPSINTFP",
        "ina226_u65" : "CADJ_FMC",
        "ina226_u84" : "VCC1V2",
        "ina226_u88" : "VCCOPS",
        "ina226_u81" : "VCCBRAM",
        "ina226_u86" : "MGTRAVTT",
        "ina226_u92" : "VCCPSDDRPLL",
        "ina226_u77" : "VCCPSINTLP",
        "ina226_u87" : "VCCPSPLL",
        "ina226_u74" : "MGTAVCC"
    }

def read_file(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except:
        return None

def print_sensor_values(hwmon):
    name = read_file(os.path.join(hwmon, "name"))
    if not name or not name.startswith("ina226"):
        return  # Only INA226 devices

    print(f"\n=== {hwmon} ({name} : {lookup[name]}) ===")

    # Possible sensor types to read
    sensor_types = ["in", "curr", "power"]

    for sensor_type in sensor_types:
        files = glob.glob(os.path.join(hwmon, f"{sensor_type}*_input"))
        for file_path in files:
            base = os.path.basename(file_path).replace("_input", "")
            label_path = os.path.join(hwmon, f"{base}_label")
            label = read_file(label_path) or base
            value = read_file(file_path)
            if value:
                unit = {
                    "in": "mV",
                    "curr": "mA",
                    "power": "uW" # I think this is the more appropriate unit
                }.get(sensor_type, "")
                print(f"{label}: {int(value)} {unit}")

def getReadings(filePath, vccint, safe = True):
    # safe = True means that we are threading and salfe = False means we are not
    if not safe:
        print_sensor_values(f"{filePath}{vccint}") # run until the stop event is set
        return
    while not stop_event.is_set() and safe:
        print_sensor_values(f"{filePath}{vccint}") # run until the stop event is set
        time.sleep(0.25) # short break

def read_data(bus, device_address, location):
    try:
        # Read the data from the device
        data = bus.read_word_data(device_address, location)
        return data
    except OSError as e:
        print(f"Error reading from device at address {hex(device_address)}: {e}")
        return None

def readLoop(bus, rail, location):
        alt = read_data(bus, 0x13, location)
        if alt is not None:
            print(f"{location}: {hex(alt)} || {alt} Value: {alt/4096}V")

def getReadingsBus(busNumber, safe = True):
    # safe = True means that we are threading and safe = False means we are not
    bus = smbus2.SMBus(busNumber)
    if not safe:
        readLoop(bus, 0x13, 0x8B)
        return # we want to get out of here
    while not stop_event.is_set() and safe:
        readLoop(bus, 0x13, 0x8B)
        time.sleep(0.25)

def runCommand(cmd, cwd):
    subprocess.run(cmd, shell=True, cwd=cwd)
    stop_event.set()

def findDevices(busno = 4):
    bus = smbus2.SMBus(busno) # Not sure if we will change 1
    print("Scanning for devices")
    devices = []
    for address in range(0x03, 0x20):
        try:
            bus.write_quick(address) # Check if the device is present
            devices.append(address)
            print(f"Device found at address: {hex(address)}")
        except (OSError, IOError):
            # Device not found, continue scanning
            continue
    bus.close()
    print("Try again")
    for bus_num in range(0, 23):
        try:
            bus = smbus2.SMBus(bus_num)
            bus.write_quick(0x1A)
            print(f"Found device at 0x1A on bus {bus_num}")
        except:
            continue

    return devices

def test():
    # find the buses that are available
    for i in range(10):
        print(f" ================= Bus {i} ================ ")
        device_list = findDevices(i)

        if not device_list:
            print("No devices found.")
            exit(1)


        # working buses? a, b. 10, 11, 13, 14, 15, 16, 17, 18, 1a, 1b, 1d

        # we have at least one device
        print(f"Found {len(device_list)} devices.")
        for device in device_list:
            print(f"Device address: {hex(device)}")
    exit()

def main():
    test()

if __name__ == "__main__":
    main()
