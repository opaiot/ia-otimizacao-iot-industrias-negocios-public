from machine import I2C
import struct

MPU6050_ADDR = 0x68
REG_PWR_MGMT_1 = 0x6B
REG_ACCEL_XOUT_H = 0x3B
REG_ACCEL_CONFIG = 0x1C

ACCEL_SCALE = 16384.0  # ±2g
G = 9.80665


class MPU6050:
    def __init__(self, i2c: I2C, addr: int = MPU6050_ADDR):
        self._i2c = i2c
        self._addr = addr
        # Wake sensor and set ±2g
        self._i2c.writeto_mem(self._addr, REG_PWR_MGMT_1, b'\x00')
        self._i2c.writeto_mem(self._addr, REG_ACCEL_CONFIG, b'\x00')

    def read_accel(self) -> tuple:
        """Return (ax, ay, az) in m/s²."""
        raw = self._i2c.readfrom_mem(self._addr, REG_ACCEL_XOUT_H, 6)
        x, y, z = struct.unpack('>hhh', raw)
        return (x / ACCEL_SCALE) * G, (y / ACCEL_SCALE) * G, (z / ACCEL_SCALE) * G
