from enum import Enum
from typing import Tuple
import pandas as pd
from dataclasses import dataclass
from typing import Callable, Optional
from pydantic import BaseModel
from app.dtos.dtypes import RawType, Unit


class CarModel(str, Enum):
    Audi_Q4_40 = "1"
    Audi_Quattro_55_86_kWh = "2"
    Audi_Quattro_50_61_kWh = "3"
    BMW_IX2 = "4"
    BMW_I4 = "5"


class SignalDef(BaseModel):
    can_id: int
    raw_type: RawType
    uds_skip_bytes: int = 3
    pid: str
    scaling: float
    offset: float
    byte_indices: Tuple[int, ...]
    unit: Unit
    column: str


class CanFrameInfo(BaseModel):
    can_id: int
    is_extended_addressing_used: bool = False
    extended_address: int | None = None
    is_multiframe: bool = False


class CarProfile(BaseModel):
    name: str
    frames: dict[int, CanFrameInfo]  # key = can_id
    signals: tuple[SignalDef, ...]


@dataclass(frozen=True)
class PlotSignal:
    key: str  # unique id used in dropdown
    df_column: str  # df column to plot
    label: str  # legend name
    yaxis: str  # "y", "y2", ...
    ytitle: str  # axis title when selected
    hover_yfmt: str = ".2f"  # formatting
    visible_by_default: bool = False
    range_fn: Optional[Callable[[pd.Series], list[float]]] = (
        None  # custom ranges if needed
    )
