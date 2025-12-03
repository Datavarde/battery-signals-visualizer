from enum import Enum


class FilteredPID(str, Enum):
    HV_BATTERY_SOC = "028C"
    HV_BATTERY_SOC_DISPLAY = "1DD0"
    MIN_CELL_SOC = "1E2D"
    MAX_CELL_SOC = "1E2C"
    HV_BATTERY_SOC_HIGH_RES = "F45B"
    BMS_BATTERY_TEMPERATURE = "2A0B"
    CURRENT_ENERGY_CONTENT_AND_SOC_TRUE = "4965"
    MAX_ENERGY_CONTENT_OF_TRACTION_BATTERY = "2AB2"
    HV_BATTERY_VOLTAGE = "1E3B"
    HV_BATTERY_CURRENT = "1E3D"


class Unit(str, Enum):
    PERCENT = "%"
    VOLTS = "V"
    AMPERES = "A"
    CELSIUS = "°C"
    NO_UNIT = "No-Unit"
    KILOWATT_HOURS = "kWh"


class FilterCANIdentifier(int, Enum):

    RECEIVER_NODE_1 = 0x77A  # 1914 Max Energy Content of traction battery
    RECEIVER_NODE_2 = 0x7AE  # HV Battery SOC
    RECEIVER_NODE_3 = 0x17FE007B
    RECEIVER_NODE_4 = 0x7ED
    RECEIVER_NODE_5 = 0x17FC0076  # HV Battery SOC
    RECEIVER_NODE_6 = 0x17FE0076
