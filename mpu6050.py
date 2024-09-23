import smbus2
import math
import time


class MPU6050:
    def __init__(self, address=0x68):
        self.address = address
        self.bus = smbus2.SMBus(1)
        self.bus.write_byte_data(self.address, 0x6B, 0)

    def read_raw_data(self, addr):
        high = self.bus.read_byte_data(self.address, addr)
        low = self.bus.read_byte_data(self.address, addr + 1)
        value = ((high << 8) | low)
        if value > 32768:
            value = value - 65536
        return value

    def get_roll(self):
        acc_x = self.read_raw_data(0x3B)
        acc_y = self.read_raw_data(0x3D)
        acc_z = self.read_raw_data(0x3F)

        roll = math.atan2(acc_y, acc_z) * 180 / math.pi
        return int(roll)


if __name__ == "__main__":
    mpu = MPU6050()
    while True:
        roll = mpu.get_roll()
        print(f"Roll: {roll}")
        time.sleep(0.5)
