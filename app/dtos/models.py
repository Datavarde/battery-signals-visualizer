from enum import Enum
from typing import Tuple
import pandas as pd
from dataclasses import dataclass
from typing import Callable, Optional
from pydantic import BaseModel
from app.dtos.dtypes import RawType, Unit

"""
    MIN_CELL_SOC = SignalDef(
        pid="1E2D",
        scaling=1.0,
        offset=0.0,
        unit=Unit.PERCENT,
        byte_indices=(0,),
        raw_type=RawType.U8,
        can_id=0x7ED,
        column="hv_battery_soc",
    )
        BMS_BATTERY_TEMPERATURE = SignalDef(
        pid="2A0B",
        scaling=1,
        offset=-100.0,
        unit=Unit.CELSIUS,
        byte_indices=(0, 1),
        raw_type=RawType.U16_BE,
        can_id=0x7ED,
        column="hv_battery_temperature",
    )
"""


class CarModel(str, Enum):
    Audi_Q4_40 = "1"
    Audi_Quattro = "2"


class SignalDef(BaseModel):
    pid: str
    scaling: float
    offset: float
    unit: Unit
    raw_type: RawType
    byte_indices: Tuple[int, ...]
    is_multiframe: bool = False
    uds_skip_bytes: int = 3
    can_id: int
    column: str


class SignalEnum(Enum):
    value: SignalDef


class Audi_Quattro_CAN_Signal(SignalEnum):

    HV_BATTERY_VOLTAGE = SignalDef(
        pid="1E3B",
        scaling=0.1,
        offset=0.0,
        unit=Unit.VOLTS,
        byte_indices=(0, 1),
        raw_type=RawType.U16_BE,
        can_id=0x7ED,
        column="hv_battery_voltage",
    )
    HV_BATTERY_CURRENT = SignalDef(
        pid="1E3D",
        scaling=0.0675,
        offset=0.0,
        unit=Unit.AMPERES,
        byte_indices=(2,),
        raw_type=RawType.U8,
        can_id=0x7ED,
        column="hv_battery_current",
    )

    HV_BATTERY_CURRENT_ENERGY_CAPACITY = SignalDef(
        pid="4965",
        scaling=0.05,
        offset=0.0,
        unit=Unit.KILOWATT_HOURS,
        byte_indices=(0, 1),
        raw_type=RawType.U16_BE,
        can_id=0x7AE,
        column="hv_battery_current_energy",
    )
    SOC_HIGH_RESOLUTION = SignalDef(
        pid="4965",
        scaling=0.05,
        offset=4.0,
        unit=Unit.PERCENT,
        byte_indices=(7, 8),
        raw_type=RawType.U16_BE,
        can_id=0x7AE,
        column="hv_battery_soc_hr",
    )
    SOC_DISPLAY = SignalDef(
        pid="1DD0",
        scaling=0.5,
        offset=0.0,
        unit=Unit.PERCENT,
        byte_indices=(0,),
        raw_type=RawType.U8,
        can_id=0x7AE,
        column="hv_battery_soc_disp",
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


class Audi_Q4_40_CANSignal(SignalEnum):
    MIN_CELL_SOC = SignalDef(
        pid="1E2D",
        scaling=0.01,
        offset=0.0,
        unit=Unit.PERCENT,
        raw_type=RawType.U16_BE,
        byte_indices=(0, 1),
        can_id=0x17FE007B,
        column="hv_battery_soc",
    )
    HV_BATTERY_CURRENT_ENERGY_CAPACITY = SignalDef(
        pid="2AB8",
        scaling=25.0,  # use your real scaling here
        offset=0.0,
        unit=Unit.KILOWATT_HOURS,
        raw_type=RawType.U16_BE,  # d5 * 256 + d6 (we’ll use indices (5,6))
        byte_indices=(2, 3),
        can_id=0x77A,
        is_multiframe=True,
        column="hv_battery_current_energy",
    )
    MAX_ENERGY_CAPACITY = SignalDef(
        pid="2AB2",
        scaling=0.000763976958454933,
        offset=0.0,
        unit=Unit.KILOWATT_HOURS,
        raw_type=RawType.U32_BE,
        byte_indices=(0, 1, 2, 3),
        can_id=0x77A,
        column="max_energy_capacity",
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


@dataclass(frozen=True)
class PlotSignal:
    key: str  # unique id used in dropdown
    column: str  # df column to plot
    label: str  # legend name
    yaxis: str  # "y", "y2", ...
    ytitle: str  # axis title when selected
    hover_yfmt: str = ".2f"  # formatting
    visible_by_default: bool = False
    range_fn: Optional[Callable[[pd.Series], list[float]]] = (
        None  # custom ranges if needed
    )


PLOT_SIGNALS = [
    PlotSignal(
        "soc", "hv_battery_soc_hr", "SOC (%)", "y", "SOC (%)", visible_by_default=True
    ),
    PlotSignal("volt", "hv_battery_voltage", "Voltage (V)", "y2", "Voltage (V)"),
    PlotSignal("current", "hv_battery_current", "Current (A)", "y3", "Current (A)"),
    PlotSignal(
        "current_energy",
        "hv_battery_current_energy",
        "UDS Energy (kWh)",
        "y5",
        "Energy (kWh)",
    ),
    PlotSignal(
        "energy_from_vi_kwh",
        "energy_from_vi_kwh",
        "Energy from V·I (kWh)",
        "y5",
        "Energy (kWh)",
    ),
    PlotSignal(
        "estimated_capacity_kwh",
        "estimated_capacity_kwh",
        "Estimated capacity (kWh)",
        "y5",
        "Capacity/Energy (kWh)",
    ),
    PlotSignal(
        "delta_energy_kwh",
        "delta_energy_kwh",
        "delta_energy (kwh)",
        "y5",
        "delta_energy(kWh)",
    ),
    PlotSignal("soh_percent", "soh_percent", "SOH (%)", "y6", "SOH (%)"),
    PlotSignal(
        "soc_disp_percent",
        "hv_battery_soc_disp",
        "soc_disp_percent (%)",
        "y",
        "SOC(%)",
    ),
]
