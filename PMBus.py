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

def runResnet18():
    volt = 0.85
    for _ in range(28): # step down 5 times
        print("==============================")
        print(f"Voltage: {volt:.2f}")
        print("==============================")
        setVoltage(smbus2.SMBus(4), 0x13, 0x21, volt)
        cwd = "./Vitis-AI/examples/vai_library/samples/classification"
        buildsh = "./build.sh"
        resnet18cmd = "./test_jpeg_classification resnet18_pt ~/Vitis-AI/examples/vai_library/samples/classification/images/002.JPEG"
        # runCommand(buildsh, cwd)
        runCommand(resnet18cmd, cwd)
        volt -= 0.01
    setVoltage(smbus2.SMBus(4), 0x13, 0x21, 0.85) # reset back to normal

def runResnet50():
    volt = 0.85
    for _ in range(28): # step down 5 times
        print("==============================")
        print(f"Voltage: {volt:.2f}")
        print("==============================")
        setVoltage(smbus2.SMBus(4), 0x13, 0x21, volt)
        cwd = "./Vitis-AI/examples/vai_runtime/resnet50"
        resnet50cmd = "./resnet50 /usr/share/vitis_ai_library/models/resnet50/resnet50.xmodel"
        # runCommand(buildsh, cwd)
        runCommand(resnet50cmd, cwd)
        volt -= 0.01
    setVoltage(smbus2.SMBus(4), 0x13, 0x21, 0.85) # reset back to normal


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

def main():
    filePath = "/sys/class/hwmon/hwmon"
    vccint = 12
    # vccbram = 13
    shellCommand = "./test_performance_facedetect densebox_320_320 test_performance_facedetect.list -t 3 -s 60" # run with 3 threads for 60 seconds
    shellCommand = "./test_performance_facedetect densebox_320_320 test_performance_facedetect.list -t 3 -s 20" # run with 3 threads for 60 seconds

    setVoltage(smbus2.SMBus(4), 0x13, 0x21, 0.85)

    directory = "./Vitis-AI/examples/vai_library/samples/facedetect"
    getReadings(filePath, vccint, False)
    getReadingsBus(4, False)

    if isThreaded:
        # shellThread = threading.Thread(target=runCommand, args=(shellCommand,directory,))
        shellThread = threading.Thread(target=runResnet18)
        # monitorThread = threading.Thread(target=getReadings, args=(filePath, vccint, True,))
        monitorThread = threading.Thread(target=getReadingsBus, args=(4, True,))
        shellThread.start()
        monitorThread.start()
        print("Threads started")
        monitorThread.join()
        shellThread.join()

        print("==============================")
        print("==========Finished============")
        print("==============================")

    else: # not threaded

        # runCommand(shellCommand,directory) # don't start the other thread
        # shellThread = threading.Thread(target=runResnet18)
        runResnet50()
        print("==============================")
        print("==========Finished============")
        print("==============================")

if __name__ == "__main__":
    main()
