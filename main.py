from pathlib import Path

from app.dtos.models import CarModel
from app.utils.load_log_file import build_payload_column, load_log_file_into_dataframe

from app.plots.plot_audi_q4 import build_dashboard_for_audi_q4
from app.plots.plot_audi_quattro import build_dashboard_for_audi_quattro

Audi_Quattro_Log_path = Path("app/logs/Audi_quattro_canedge.asc")


Audi_Q4_Log_Path = Path("app/logs/00000001_audi_q4_5th_dec_2025.asc")


def main() -> None:
    prompt = (
        "Choose Car Models Available Options are\n"
        " [1]: Audi Q4\n"
        " [2]: Audi Quattro\n"
        "Enter choice: "
    )

    chosen_car_model = CarModel(input(prompt).strip().lower())
    print(f"you chose={chosen_car_model}")
    match chosen_car_model:
        case CarModel.Audi_Q4_40:
            df = load_log_file_into_dataframe(Audi_Q4_Log_Path)
            df_with_payload = build_payload_column(df)
            build_dashboard_for_audi_q4(df_with_payload)
        case CarModel.Audi_Quattro:
            df = load_log_file_into_dataframe(Audi_Quattro_Log_path)
            df_with_payload = build_payload_column(df)
            # build_dashboard_for_audi_quattro(df_with_payload)
            build_dashboard_for_audi_quattro(df_with_payload)


if __name__ == "__main__":
    main()
