from app.dtos.dtypes import RawType, Unit
from app.dtos.models import CanFrameInfo, CarProfile, PlotSignal, SignalDef

AUDI_E_TRON_QUATTRO_55_CAPACITY_AT_BOL_kWh = 86
AUDI_E_TRON_QUATTRO_50_CAPACITY_AT_BOL_kWh = 61


Audi_Quattro_Profile: CarProfile = CarProfile(
    name="Audi_Quattro",
    frames={
        0x7ED: CanFrameInfo(
            can_id=0x7ED,
            is_extended_addressing_used=False,
            is_multiframe=True,
        ),
        0x7AE: CanFrameInfo(
            can_id=0x7AE, is_extended_addressing_used=False, is_multiframe=True
        ),
    },
    signals=(
        SignalDef(
            pid="1E3B",
            scaling=0.1,
            offset=0.0,
            unit=Unit.VOLTS,
            byte_indices=(0, 1),
            raw_type=RawType.U16_BE,
            can_id=0x7ED,
            column="hv_battery_voltage",
        ),
        SignalDef(
            pid="1E3D",
            scaling=0.0675,
            offset=0.0,
            unit=Unit.AMPERES,
            byte_indices=(2,),
            raw_type=RawType.U8,
            can_id=0x7ED,
            column="hv_battery_current",
        ),
        SignalDef(
            pid="4965",
            scaling=0.05,
            offset=0.0,
            unit=Unit.KILOWATT_HOURS,
            byte_indices=(0, 1),
            raw_type=RawType.U16_BE,
            can_id=0x7AE,
            column="hv_battery_current_energy",
        ),
        SignalDef(
            pid="4965",
            scaling=0.05,
            offset=0.0,
            unit=Unit.PERCENT,
            byte_indices=(7, 8),
            raw_type=RawType.U16_BE,
            can_id=0x7AE,
            column="hv_battery_soc_hr",
        ),
        SignalDef(
            pid="1DD0",
            scaling=0.5,
            offset=0.0,
            unit=Unit.PERCENT,
            byte_indices=(0,),
            raw_type=RawType.U8,
            can_id=0x7AE,
            column="soc_disp_percent",
        ),
        SignalDef(
            pid="1E2D",
            scaling=1.0,
            offset=0.0,
            unit=Unit.PERCENT,
            byte_indices=(0,),
            raw_type=RawType.U8,
            can_id=0x7ED,
            column="min_cell_soc",
        ),
    ),
)

AUDI_QUATTRO_PLOT_SIGNALS = [
    PlotSignal(
        key="hv_battery_soc_hr",
        df_column="hv_battery_soc_hr",
        label="SOC High Resolution(%)",
        yaxis="y",
        ytitle="SOC (%)",
        visible_by_default=True,
    ),
    PlotSignal(
        key="min_cell_soc",
        df_column="min_cell_soc",
        label="Min Cell SOC(%)",
        yaxis="y",
        ytitle="SOC (%)",
        visible_by_default=False,
    ),
    PlotSignal(
        key="soc_disp_percent",
        df_column="soc_disp_percent",
        label="Display SOC (%)",
        yaxis="y",
        ytitle="SOC (%)",
    ),
    PlotSignal(
        key="hv_battery_voltage",
        df_column="hv_battery_voltage",
        label="Voltage (V)",
        yaxis="y2",
        ytitle="Voltage (V)",
    ),
    PlotSignal(
        key="hv_battery_current",
        df_column="hv_battery_current",
        label="Current (A)",
        yaxis="y3",
        ytitle="Current (A)",
    ),
    PlotSignal(
        key="hv_battery_current_energy",
        df_column="hv_battery_current_energy",
        label="Current Energy (kWh)",
        yaxis="y4",
        ytitle="Current Energy (kWh)",
    ),
    PlotSignal(
        key="estimated_capacity_kwh",
        df_column="estimated_capacity_kwh",
        label="Estimated capacity (kWh)",
        yaxis="y4",
        ytitle="Estimated Capacity (kWh)",
    ),
    PlotSignal(
        key="soh_percent",
        df_column="soh_percent",
        label="SOH (%)",
        yaxis="y5",
        ytitle="SOH (%)",
    ),
]

AUDI_Quattro_CAN_IDs_of_interest: set[int] = set(Audi_Quattro_Profile.frames.keys())
