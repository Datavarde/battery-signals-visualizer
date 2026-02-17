from pathlib import Path

from app.dtos.audi_q4_40 import AUDI_Q4_CAN_Signals_of_interest
from app.dtos.audi_quattro import (
    AUDI_E_TRON_QUATTRO_50_CAPACITY_AT_BOL_kWh,
    AUDI_E_TRON_QUATTRO_55_CAPACITY_AT_BOL_kWh,
    Audi_Quattro_Profile,
)
from app.dtos.bmw_i4 import BMW_I4_PROFILE, BMW_I4_CAN_IDs_of_interest
from app.dtos.bmw_ix2 import BMW_IX2_PROFILE, BMW_IX2_CAN_IDs_of_interest
from app.dtos.models import (
    CarModel,
)
from app.plots.plot_bmw_i4 import (
    append_estimated_signals_for_bmw_i4,
    build_dashboard_for_bmw_i4,
)
from app.plots.plot_bmw_ix2 import (
    append_estimated_signals_for_bmw_ix2,
    build_dashboard_for_bmw_ix2,
)
from app.scripts.audi_quattro import parse_audi_quattro_can_recording_and_plot_signal
from app.scripts.bmw_i4 import parse_bmw_i4_can_recording_and_plot_signal
from app.scripts.bmw_ix2 import parse_bmw_ix2_can_recording_and_plot_signal
from app.utils.load_log_file import build_payload_column, load_log_file_into_dataframe

from app.plots.plot_audi_q4 import (
    append_estimated_signals_for_audi_q4,
    build_dashboard_for_audi_q4,
)
from app.plots.plot_audi_quattro import build_dashboard_for_audi_quattro
from app.utils.signal_processor import append_physical_signals_to_dataframe


Audi_Quattro_Log_path = Path("app/logs/audi/Audi_quattro_TNO416_16th_december.trc")
Audi_Q4_Log_Path = Path("app/logs/00000001_audi_q4_5th_dec_2025.asc")
BMW_IX2_log_path = Path("app/logs/bmw/BMW_ix2_Jan_30.trc")
# BMW_I4_log_path = Path("app/logs/bmw/BMW_i4_feb_6_canedge.trc")
BMW_I4_log_path = Path("app/logs/bmw/BMW_i4_feb_6_XTG95U_canedge.trc")


def main() -> None:
    prompt = (
        "Choose Car Models Available Options are\n"
        " [1]: Audi Q4\n"
        " [2]: Audi Quattro 55 (86 kWh) \n"
        " [3]: Audi Quattro 50 (61 kWh) \n"
        " [4]: BMW IX2 \n"
        " [5]: BMW I4 \n"
        "Enter choice: "
    )

    chosen_car_model = CarModel(input(prompt).strip().lower())
    print(f"You chose [{chosen_car_model.value}]: {chosen_car_model.name}")

    match chosen_car_model:
        case CarModel.Audi_Q4_40:
            df = load_log_file_into_dataframe(
                log_file_path=Audi_Q4_Log_Path,
                can_ids_of_interest=AUDI_Q4_CAN_Signals_of_interest,
            )
            df_with_payload = build_payload_column(
                df=df, car_model=Audi_Quattro_Profile
            )
            df_with_physical_signals = append_physical_signals_to_dataframe(
                df=df_with_payload, car_model=Audi_Quattro_Profile
            )
            df_with_estimated_and_physical_signals = (
                append_estimated_signals_for_audi_q4(
                    df_with_physical_signals=df_with_physical_signals
                )
            )
            build_dashboard_for_audi_q4(
                df_with_estimated_and_physical_signals=df_with_estimated_and_physical_signals
            )
        case CarModel.Audi_Quattro_55_86_kWh:
            parse_audi_quattro_can_recording_and_plot_signal(
                log_file_path=Audi_Quattro_Log_path,
                usable_battery_capacity=AUDI_E_TRON_QUATTRO_55_CAPACITY_AT_BOL_kWh,
            )

        case CarModel.Audi_Quattro_50_61_kWh:
            parse_audi_quattro_can_recording_and_plot_signal(
                log_file_path=Audi_Quattro_Log_path,
                usable_battery_capacity=AUDI_E_TRON_QUATTRO_50_CAPACITY_AT_BOL_kWh,
            )

        case CarModel.BMW_IX2:
            parse_bmw_ix2_can_recording_and_plot_signal(log_file_path=BMW_IX2_log_path)
        case CarModel.BMW_I4:
            parse_bmw_i4_can_recording_and_plot_signal(log_file_path=BMW_I4_log_path)
    print("here")


if __name__ == "__main__":
    main()
