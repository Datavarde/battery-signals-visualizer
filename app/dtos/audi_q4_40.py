from app.dtos.dtypes import RawType, Unit
from app.dtos.models import CanFrameInfo, CarProfile, SignalDef


AUDI_Q4_40_Profile: CarProfile = CarProfile(
    name="Audi_Q4_40",
    frames={
        0x77A: CanFrameInfo(
            can_id=0x77A,
            is_extended_addressing_used=False,
            is_multiframe=True,
        ),
        0x17FE007B: CanFrameInfo(
            can_id=0x17FE007B, is_extended_addressing_used=False, is_multiframe=True
        ),
    },
    signals=(
        SignalDef(
            pid="1E2D",
            scaling=0.01,
            offset=0.0,
            unit=Unit.PERCENT,
            raw_type=RawType.U16_BE,
            byte_indices=(0, 1),
            can_id=0x17FE007B,
            column="hv_battery_soc",
        ),
        SignalDef(
            pid="2AB8",
            scaling=25.0,
            offset=0.0,
            unit=Unit.KILOWATT_HOURS,
            raw_type=RawType.U16_BE,
            byte_indices=(0, 1),
            can_id=0x77A,
            column="hv_battery_current_energy",
        ),
        SignalDef(
            pid="2AB2",
            scaling=0.000763976958454933,
            offset=0.0,
            unit=Unit.KILOWATT_HOURS,
            raw_type=RawType.U32_BE,
            byte_indices=(0, 1, 2, 3),
            can_id=0x77A,
            column="max_energy_capacity",
        ),
    ),
)

AUDI_Q4_CAN_Signals_of_interest = set(AUDI_Q4_40_Profile.frames.keys())
