from pathlib import Path

from app.utils.load_log_file import build_payload_column, load_log_file_into_dataframe
from app.utils.plot_can_signals import (
    build_dashboard_for_audi_quattro,
)

TRC_PATH = Path(
    "Audi_e-tron_quattro_11-21_11-33-38_423_to_13_58_soc_74_to96_percent.trc"
)


AUDI_q4_LOG_PATH = Path("2025-12-02_11-50-39_847.trc")


def main() -> None:

    df = load_log_file_into_dataframe(TRC_PATH)
    # df = load_log_file_into_dataframe(AUDI_q4_LOG_PATH)
    print(df["can_id"].unique())
    # df_with_payload = build_payload_column(df)

    # fig = build_dashboard(df)
    fig = build_dashboard_for_audi_quattro(df)


#  fig = build_dashboard_for_audi_q4(df)


if __name__ == "__main__":
    main()
