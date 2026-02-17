from pathlib import Path

from app.dtos.audi_quattro import AUDI_Quattro_CAN_IDs_of_interest, Audi_Quattro_Profile
from app.plots.plot_audi_quattro import (
    append_estimated_signals_for_audi_quattro,
    build_dashboard_for_audi_quattro,
)

from app.utils.load_log_file import build_payload_column, load_log_file_into_dataframe
from app.utils.signal_processor import append_physical_signals_to_dataframe


def parse_audi_quattro_can_recording_and_plot_signal(
    *, log_file_path: Path, usable_battery_capacity: int
) -> None:
    print(f"log chosen={log_file_path}")
    log_name = log_file_path._cparts[-1].split(".")[0]
    print(f"{log_name=}")
    df = load_log_file_into_dataframe(
        log_file_path=log_file_path,
        can_ids_of_interest=AUDI_Quattro_CAN_IDs_of_interest,
    )
    df_with_payload = build_payload_column(df=df, car_model=Audi_Quattro_Profile)
    df_with_physical_signals = append_physical_signals_to_dataframe(
        df=df_with_payload, car_model=Audi_Quattro_Profile
    )
    df_with_estimated_and_physical_signals = append_estimated_signals_for_audi_quattro(
        df_with_physical_signals=df_with_physical_signals
    )
    # build_dashboard_for_audi_quattro(df_with_payload)
    build_dashboard_for_audi_quattro(
        df_with_estimated_and_physical_signals=df_with_estimated_and_physical_signals,
        log_name=log_name,
    )
