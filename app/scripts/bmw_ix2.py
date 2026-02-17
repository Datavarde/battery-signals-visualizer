from pathlib import Path
from app.dtos.bmw_ix2 import BMW_IX2_PROFILE, BMW_IX2_CAN_IDs_of_interest
from app.plots.plot_bmw_ix2 import (
    append_estimated_signals_for_bmw_ix2,
    build_dashboard_for_bmw_ix2,
)
from app.utils.load_log_file import build_payload_column, load_log_file_into_dataframe
from app.utils.signal_processor import append_physical_signals_to_dataframe


def parse_bmw_ix2_can_recording_and_plot_signal(*, log_file_path: Path) -> None:
    print(f"log chosen={log_file_path}")
    log_name = log_file_path._cparts[-1].split(".")[0]
    df = load_log_file_into_dataframe(
        log_file_path=log_file_path,
        can_ids_of_interest=BMW_IX2_CAN_IDs_of_interest,
    )
    df_with_payload = build_payload_column(df=df, car_model=BMW_IX2_PROFILE)
    df_with_physical_signals = append_physical_signals_to_dataframe(
        df=df_with_payload, car_model=BMW_IX2_PROFILE
    )
    df_with_estimated_and_physical_signals = append_estimated_signals_for_bmw_ix2(
        df_with_physical_signals=df_with_physical_signals, log_name=log_name
    )
    build_dashboard_for_bmw_ix2(
        df_with_estimated_and_physical_signals=df_with_estimated_and_physical_signals,
        log_name=log_name,
    )
