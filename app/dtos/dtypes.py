from enum import Enum


class RawType(str, Enum):
    U8 = "u8"  # one byte
    U16_BE = "u16_be"  # two bytes big endian
    U32_BE = "u32_be"  # four bytes big endian


class Unit(str, Enum):
    PERCENT = "%"
    VOLTS = "V"
    AMPERES = "A"
    CELSIUS = "°C"
    NO_UNIT = "No-Unit"
    KILOWATT_HOURS = "kWh"


class CarModel(Enum):
    Audi_Quattro = "Audi_Quattro"
    Audi_Q4_E_tron = "Audi_Q4_E-tron"


class CANFrameType(Enum):
    SINGLE_FRAME = 0x0
    FIRST_FRAME = 0x1
    CONSECUTIVE_FRAME = 0x2
