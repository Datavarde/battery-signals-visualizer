from app.dtos.dtypes import RawType, Unit
from app.dtos.models import CanFrameInfo, CarProfile, PlotSignal, SignalDef


BMW_IX2_PLOT_SIGNALS = [
    PlotSignal(
        key="soc",
        df_column="soc",
        label="SOC (%)",
        yaxis="y",
        ytitle="SOC (%)",
        visible_by_default=True,
    ),
    PlotSignal(
        key="max_energy_capacity",
        df_column="max_energy_capacity",
        label="Max Energy Capacity (kWh)",
        yaxis="y2",
        ytitle="Max Energy Capacity (kWh)",
    ),
    PlotSignal(
        key="soh_percent",
        df_column="soh",
        label="SOH (%)",
        yaxis="y3",
        ytitle="SOH (%)",
    ),
    PlotSignal(
        key="estimated_soh",
        df_column="estimated_soh",
        label="Estimated SOH (%)",
        yaxis="y4",
        ytitle="Estimated SOH (%)",
    ),
    PlotSignal(
        key="estimated_max_energy_capacity",
        df_column="estimated_max_energy_capacity",
        label="Estimated Max Energy Capacity (kWh)",
        yaxis="y5",
        ytitle="Estimated Max Energy Capacity (kWh)",
    ),
    PlotSignal(
        key="current_energy_capacity",
        df_column="current_energy_capacity",
        label="Current Energy Capacity (kWh)",
        yaxis="y6",
        ytitle="Current Energy Capacity (kWh)",
    ),
]

BMW_IX2_PROFILE: CarProfile = CarProfile(
    name="BMW_IX2",
    frames={
        0x607: CanFrameInfo(
            can_id=0x607,
            is_extended_addressing_used=True,
            extended_address=0xF1,
            is_multiframe=True,
        ),
        # add more CAN IDs if needed
    },
    signals=(
        SignalDef(
            pid="A85F",
            scaling=0.01,
            offset=-50.0,
            unit=Unit.KILOWATT_HOURS,
            raw_type=RawType.U16_BE,
            byte_indices=(2, 3),
            can_id=0x607,
            column="max_energy_capacity",
        ),
        SignalDef(
            pid="A85F",
            scaling=0.01,
            offset=-50.0,
            unit=Unit.KILOWATT_HOURS,
            raw_type=RawType.U16_BE,
            byte_indices=(0, 2),
            can_id=0x607,
            column="current_energy_capacity",
        ),
        SignalDef(
            pid="E545",
            scaling=0.01,
            offset=0,
            unit=Unit.PERCENT,
            raw_type=RawType.U16_BE,
            byte_indices=(4, 5),
            can_id=0x607,
            column="soh",
        ),
        SignalDef(
            pid="E59A",
            scaling=0.01,
            offset=0,
            unit=Unit.PERCENT,
            raw_type=RawType.U16_BE,
            byte_indices=(4, 5),
            can_id=0x607,
            column="soc",
        ),
    ),
)

BMW_IX2_CAN_IDs_of_interest: set[int] = set(BMW_IX2_PROFILE.frames.keys())
