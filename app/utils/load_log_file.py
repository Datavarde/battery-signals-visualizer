from pathlib import Path
import pandas as pd
import can

from app.dtos.dtypes import FilterCANIdentifier, FilteredPID


def extract_pid(can_message: can.Message) -> str | None:
    data = can_message.data
    pci = data[0]  # protocol control information

    frame_type = pci & 0xF0
    if frame_type == 0x00:  # single frame (0x0L)
        # 05 62 1E 3B ...
        return f"{data[2]:02X}{data[3]:02X}"
    elif frame_type == 0x10:  # first frame (0x1L)
        # 10 0D 62 49 65 ...

        return f"{data[3]:02X}{data[4]:02X}"
    else:
        # consecutive frames don't carry a new DID
        return None


def _is_preconditions_to_load_data_successful(can_message: can.Message) -> bool:
    if can_message.is_error_frame or can_message.is_remote_frame:
        return False

    if can_message.dlc < 4:
        return False
    if can_message.arbitration_id not in FilterCANIdentifier._value2member_map_:
        return False
    pid = extract_pid(can_message)

    if pid not in FilteredPID._value2member_map_:
        return False

    return True


def load_log_file_into_dataframe(log_file_path: Path) -> pd.DataFrame:
    rows = []

    with can.LogReader(str(log_file_path)) as log_reader:

        for can_message in log_reader:
            pid = extract_pid(can_message)
            if not _is_preconditions_to_load_data_successful(can_message):
                continue

            data = list(can_message.data)
            rows.append(
                {
                    "time_s": can_message.timestamp,
                    "can_id": can_message.arbitration_id,
                    "dlc": can_message.dlc,
                    "d0": data[0],
                    "d1": data[1],
                    "d2": data[2],
                    "d3": data[3],
                    "d4": data[4],
                    "d5": data[5],
                    "d6": data[6],
                    "d7": data[7],
                    "pid": pid,
                }
            )
        if not rows:
            raise RuntimeError(f"No CAN messages found in {log_file_path}")
        df = pd.DataFrame(rows)

        df["time_offset_s"] = (df["time_s"] - df["time_s"].iloc[0]) / 60
        return df
