from pathlib import Path

from app.utils.load_log_file import load_log_file_into_dataframe
from app.utils.plot_can_signals import build_dashboard

TRC_PATH = Path(
    "Audi_e-tron_quattro_11-21_11-33-38_423_to_13_58_soc_74_to96_percent.trc"
)


def main() -> None:

    df = load_log_file_into_dataframe(TRC_PATH)
    print(df["can_id"].unique())
    # fig = build_dashboard(df)
    fig = build_dashboard(df)


if __name__ == "__main__":
    main()
