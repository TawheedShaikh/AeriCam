import smbus
import time
from math import atan2, sqrt, pi

# MPU6050 Registers and their Address
MPU_ADDR = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B

bus = smbus.SMBus(1)  # For Raspberry Pi revision 2 or 3, use bus number 1
bus.write_byte_data(MPU_ADDR, PWR_MGMT_1, 0)  # Wake up the MPU6050

def read_raw_data(addr):
    # Read two bytes of data from a specific address
    high = bus.read_byte_data(MPU_ADDR, addr)
    low = bus.read_byte_data(MPU_ADDR, addr+1)
    value = (high << 8) | low
    if value > 32768:
        value -= 65536
    return value

def calculate_pitch_roll():
    # Read accelerometer data
    acc_x = read_raw_data(ACCEL_XOUT_H)
    acc_y = read_raw_data(ACCEL_XOUT_H + 2)
    acc_z = read_raw_data(ACCEL_XOUT_H + 4)

    # Calculate pitch and roll
    roll = atan2(acc_y, acc_z) * 180.0 / pi
    pitch = atan2(-acc_x, sqrt(acc_y**2 + acc_z**2)) * 180.0 / pi

    return roll, pitch

while True:
    roll, pitch = calculate_pitch_roll()
    print(f"Roll = {roll:.1f}, Pitch = {pitch:.1f}")
    time.sleep(0.4)
