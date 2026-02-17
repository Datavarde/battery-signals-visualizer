from pathlib import Path
import pandas as pd
import can

from app.dtos.dtypes import CANFrameType
from app.dtos.models import CarProfile


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


def valid_can_data(can_message: can.Message) -> bool:
    if can_message.is_error_frame or can_message.is_remote_frame:
        return False

    return True


def load_log_file_into_dataframe(
    *, log_file_path: Path, can_ids_of_interest: set[int]
) -> pd.DataFrame:
    rows = []

    with can.TRCReader(str(log_file_path)) as log_reader:

        for can_message in log_reader:
            if not valid_can_data(can_message):
                continue

            if can_message.arbitration_id not in can_ids_of_interest:
                continue

            rows.append(
                {
                    "time_s": can_message.timestamp,
                    "can_id": can_message.arbitration_id,
                    "dlc": can_message.dlc,
                    "data": list(can_message.data),
                }
            )
        if not rows:
            raise RuntimeError(f"No CAN messages found in {log_file_path}")
        df = pd.DataFrame(rows)

        df["time_offset_s"] = (df["time_s"] - df["time_s"].iloc[0]) / 60
        return df


def build_payload_column(*, df: pd.DataFrame, car_model: CarProfile) -> pd.DataFrame:
    """
    Reassemble ISO-TP (SF/FF/CF) into canonical UDS payload.

    Result:
        df["payload"] is either:
        - list[int] = [SID, DID_HI, DID_LO, data0, data1, ...]
        - None      = frame is not the final frame in a UDS message
    """
    df = df.copy()

    can_payload_without_iso_tp_and_extended_address: list[list[int] | None] = []
    temp_buffer_to_append_raw_payload_bytes: dict[str, list[int]] = {}
    expected_length_from_can_response: dict[str, int] = {}
    unique_iso_tp_identifier: set[str] = set()
    for _, row in df.iterrows():
        can_id = int(row["can_id"])
        data = [int(x) for x in row["data"]]

        can_frame_info = car_model.frames.get(can_id)
        if can_frame_info is None:
            can_payload_without_iso_tp_and_extended_address.append(None)
            continue

        if can_frame_info.is_extended_addressing_used:
            if len(data) < 2:
                can_payload_without_iso_tp_and_extended_address.append(None)
                continue

            extended_addressing_byte = data[0]

            if (
                can_frame_info.extended_address is not None
                and extended_addressing_byte != can_frame_info.extended_address
            ):
                can_payload_without_iso_tp_and_extended_address.append(None)
                continue
            pci_idx = 1
            iso_tp_identifier = f"{can_id:X}{extended_addressing_byte:X}"
        else:
            extended_addressing_byte = None
            pci_idx = 0
            iso_tp_identifier = f"{can_id:X}"
        unique_iso_tp_identifier.add(iso_tp_identifier)
        pci = data[pci_idx]
        can_frame_type = (pci >> 4) & 0xF

        match CANFrameType(can_frame_type):
            case CANFrameType.SINGLE_FRAME:
                length = pci & 0x0F  # lower nibble for instance 0x07 -> 7 is the length
                payload_start_idx = pci_idx + 1
                payload = data[payload_start_idx : payload_start_idx + length]
                can_payload_without_iso_tp_and_extended_address.append(payload)

                temp_buffer_to_append_raw_payload_bytes.pop(iso_tp_identifier, None)
                expected_length_from_can_response.pop(iso_tp_identifier, None)

            case CANFrameType.FIRST_FRAME:
                length = ((pci & 0x0F) << 8) | data[
                    pci_idx + 1
                ]  # lower nibble in the pci and then the length follows
                temp_buffer_to_append_raw_payload_bytes[iso_tp_identifier] = data[
                    pci_idx + 2 :
                ]  # first chunk of data
                expected_length_from_can_response[iso_tp_identifier] = length
                can_payload_without_iso_tp_and_extended_address.append(
                    None
                )  # not complete yet

            case CANFrameType.CONSECUTIVE_FRAME:
                temp_buffer_to_append_raw_payload_bytes[iso_tp_identifier].extend(
                    data[pci_idx + 1 :]
                )
                if (
                    len(temp_buffer_to_append_raw_payload_bytes[iso_tp_identifier])
                    >= expected_length_from_can_response[iso_tp_identifier]
                ):
                    payload = temp_buffer_to_append_raw_payload_bytes[
                        iso_tp_identifier
                    ][: expected_length_from_can_response[iso_tp_identifier]]
                    can_payload_without_iso_tp_and_extended_address.append(
                        payload
                    )  # final complete payload

                    temp_buffer_to_append_raw_payload_bytes.pop(iso_tp_identifier, None)
                    expected_length_from_can_response.pop(iso_tp_identifier, None)
                else:
                    can_payload_without_iso_tp_and_extended_address.append(
                        None
                    )  # still waiting for more

            case _:
                can_payload_without_iso_tp_and_extended_address.append(None)

    df["payload"] = can_payload_without_iso_tp_and_extended_address
    df["payload"].dropna()
    return df
