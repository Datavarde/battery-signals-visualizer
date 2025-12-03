from dataclasses import dataclass
from enum import Enum
from app.dtos.dtypes import Unit


@dataclass(frozen=True)
class SignalDef:
    pid: str
    scaling: float = 1.0
    offset: float = 0.0
    unit: Unit = Unit.NO_UNIT


class CANSignal(Enum):
    HV_BATTERY_SOC = SignalDef(pid="028C", scaling=1.0, offset=0.0, unit=Unit.PERCENT)
    MIN_CELL_SOC = SignalDef(pid="1E2D", scaling=1.0, offset=0.0, unit=Unit.PERCENT)
    HV_BATTERY_VOLTAGE = SignalDef(pid="1E3B", scaling=0.1, offset=0.0, unit=Unit.VOLTS)
    HV_BATTERY_CURRENT = SignalDef(
        pid="1E3D", scaling=0.0675, offset=0.0, unit=Unit.AMPERES
    )
    BMS_BATTERY_TEMPERATURE = SignalDef(
        pid="2A0B", scaling=1, offset=-100.0, unit=Unit.AMPERES
    )
    HV_BATTERY_CURRENT_ENERGY_CAPACITY = SignalDef(
        pid="4965", scaling=0.05, offset=0.0, unit=Unit.KILOWATT_HOURS
    )

    @property
    def pid(self):
        return self.value.pid

    @property
    def scaling(self):
        return self.value.scaling

    @property
    def offset(self):
        return self.value.offset

    @property
    def unit(self):
        return self.value.unit


class Audi_Q4_40_CANSignal(Enum):
    MIN_CELL_SOC = SignalDef(pid="1E2D", scaling=0.01, offset=0.0, unit=Unit.PERCENT)
    BMS_BATTERY_TEMPERATURE = SignalDef(
        pid="2A0B", scaling=1, offset=-100.0, unit=Unit.AMPERES
    )
    HV_BATTERY_CURRENT_ENERGY_CAPACITY = SignalDef(
        pid="2AB8", scaling=25, offset=0.0, unit=Unit.KILOWATT_HOURS
    )
    MAX_ENERGY_CAPACITY = SignalDef(
        pid="2AB2", scaling=0.000763976958454933, offset=0.0, unit=Unit.KILOWATT_HOURS
    )
    HV_BATTERY_VOLTAGE = SignalDef(pid="1E3B", scaling=0.1, offset=0.0, unit=Unit.VOLTS)

    @property
    def pid(self):
        return self.value.pid

    @property
    def scaling(self):
        return self.value.scaling

    @property
    def offset(self):
        return self.value.offset

    @property
    def unit(self):
        return self.value.unit
