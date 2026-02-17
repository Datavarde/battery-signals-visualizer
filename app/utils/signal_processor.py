import pandas as pd

from app.dtos.dtypes import RawType
from app.dtos.models import (
    CarProfile,
    SignalDef,
)
from app.utils.load_log_file import build_payload_column


def _compute_raw_from_payload(payload: list[int], sig: SignalDef) -> int:
    """
    Compute raw integer from a UDS payload based on SignalDef.

    payload example (for UDS ReadDataByIdentifier):
        [0x62, DID_HI, DID_LO, data0, data1, data2, ...]
    We first drop the UDS header (62 + DID) using uds_skip_bytes,
    then index into data bytes using sig.byte_indices.
    """
    # Drop UDS header if configured
    data = payload[sig.uds_skip_bytes :] if sig.uds_skip_bytes else payload

    # Pick the bytes according to byte_indices (0-based in 'data')
    bytes_used = [data[i] for i in sig.byte_indices]

    match sig.raw_type:
        case RawType.U8:
            return bytes_used[0]

        case RawType.U16_BE:
            hi, lo = bytes_used
            return (hi << 8) | lo

        case RawType.U32_BE:
            b0, b1, b2, b3 = bytes_used
            return (b0 << 24) | (b1 << 16) | (b2 << 8) | b3

        case _:
            raise ValueError(f"Unsupported RawType: {sig.raw_type}")


def append_physical_signals_to_dataframe(
    *, df: pd.DataFrame, car_model: CarProfile
) -> pd.DataFrame:
    df = df.copy()

    signals: tuple[SignalDef, ...] = car_model.signals
    # 1) Ensure output columns exist
    for signal in signals:
        column_name = signal.column
        # create empty column if missing
        if column_name not in df.columns:
            df[column_name] = pd.NA

    # walk each row that might have a completed UDS payload
    for idx, row in df.iterrows():
        payload = row["payload"]
        if not isinstance(payload, list) or len(payload) < 3:
            continue

        # DID from payload bytes 1 and 2
        did = (payload[1] << 8) | payload[2]
        did_hex = f"{did:04X}"

        for signal in signals:
            if signal.pid != did_hex:
                continue

            # optional CAN-ID filter
            if signal.can_id != int(row["can_id"]):
                continue

            raw = _compute_raw_from_payload(payload, signal)
            phys = raw * signal.scaling + signal.offset

            column: str = signal.column
            df.at[idx, column] = phys

    return df
