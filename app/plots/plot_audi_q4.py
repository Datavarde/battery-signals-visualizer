import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from app.dtos.audi_q4_40 import AUDI_Q4_40_Profile
from app.dtos.audi_quattro import Audi_Quattro_Profile
from app.utils.load_log_file import build_payload_column
from app.utils.signal_processor import (
    _compute_raw_from_payload,
    append_physical_signals_to_dataframe,
)


Q4_ETRON_CAPACITY_AT_BOL_kWh = 76

pio.renderers.default = "browser"


def append_estimated_signals_for_audi_q4(
    *, df_with_physical_signals: pd.DataFrame
) -> pd.DataFrame:

    df_with_estimated_signals_and_physical_signals = df_with_physical_signals.copy()
    # ---- sanity check: make sure columns exist ----
    required_cols = [
        "hv_battery_soc",
        "hv_battery_current_energy",
        "max_energy_capacity",
    ]
    missing = [
        c
        for c in required_cols
        if c not in df_with_estimated_signals_and_physical_signals.columns
    ]
    if missing:
        raise RuntimeError(f"Missing expected columns after decoding: {missing}")

    # raw → kWh
    df_with_estimated_signals_and_physical_signals["current_capacity_kwh"] = (
        df_with_estimated_signals_and_physical_signals["hv_battery_current_energy"]
        / 1000.0
    )
    df_with_estimated_signals_and_physical_signals["max_capacity_kwh"] = (
        df_with_estimated_signals_and_physical_signals["max_energy_capacity"] / 1000.0
    )

    # derived quantities
    df_with_estimated_signals_and_physical_signals["soc_frac"] = (
        df_with_estimated_signals_and_physical_signals["hv_battery_soc"] / 100.0
    )

    df_with_estimated_signals_and_physical_signals["estimated_capacity_kwh"] = pd.NA
    mask_cap = (
        df_with_estimated_signals_and_physical_signals["current_capacity_kwh"].notna()
        & df_with_estimated_signals_and_physical_signals["soc_frac"].notna()
        & (df_with_estimated_signals_and_physical_signals["soc_frac"] > 0)
    )
    df_with_estimated_signals_and_physical_signals.loc[
        mask_cap, "estimated_capacity_kwh"
    ] = (
        df_with_estimated_signals_and_physical_signals.loc[
            mask_cap, "current_capacity_kwh"
        ]
        / df_with_estimated_signals_and_physical_signals.loc[mask_cap, "soc_frac"]
    )

    df_with_estimated_signals_and_physical_signals["current_capacity_pct_bol"] = (
        df_with_estimated_signals_and_physical_signals["current_capacity_kwh"]
        / Q4_ETRON_CAPACITY_AT_BOL_kWh
        * 100.0
    )
    df_with_estimated_signals_and_physical_signals["max_capacity_pct_bol"] = (
        df_with_estimated_signals_and_physical_signals["max_capacity_kwh"]
        / Q4_ETRON_CAPACITY_AT_BOL_kWh
        * 100.0
    )

    df_with_estimated_signals_and_physical_signals["soh_estimated_pct"] = (
        df_with_estimated_signals_and_physical_signals["estimated_capacity_kwh"]
        / Q4_ETRON_CAPACITY_AT_BOL_kWh
        * 100.0
    )
    df_with_estimated_signals_and_physical_signals["soh_energy_pct"] = (
        df_with_estimated_signals_and_physical_signals["max_capacity_kwh"]
        / Q4_ETRON_CAPACITY_AT_BOL_kWh
        * 100.0
    )
    return df_with_estimated_signals_and_physical_signals


def build_dashboard_for_audi_q4(
    *, df_with_estimated_and_physical_signals: pd.DataFrame
) -> None:
    print(df_with_estimated_and_physical_signals["pid"].value_counts())

    # 4) Series with non-NaNs
    soc_series = df_with_estimated_and_physical_signals.dropna(
        subset=["hv_battery_soc"]
    )
    curr_cap_series = df_with_estimated_and_physical_signals.dropna(
        subset=["current_capacity_pct_bol"]
    )
    max_cap_series = df_with_estimated_and_physical_signals.dropna(
        subset=["max_capacity_pct_bol"]
    )
    soh_est_series = df_with_estimated_and_physical_signals.dropna(
        subset=["soh_estimated_pct"]
    )
    soh_energy_series = df_with_estimated_and_physical_signals.dropna(
        subset=["soh_energy_pct"]
    )

    # 5) Plot
    fig = go.Figure()

    # SOC (left axis)
    fig.add_trace(
        go.Scatter(
            x=soc_series["time_offset_s"],
            y=soc_series["hv_battery_soc"],
            mode="lines+markers",
            name="SOC (%)",
            yaxis="y",
            hovertemplate="SOC: %{y:.2f} %<br>Time: %{x:.2f} min<extra></extra>",
        )
    )

    # Current capacity % of BOL (+ kWh)
    fig.add_trace(
        go.Scatter(
            x=curr_cap_series["time_offset_s"],
            y=curr_cap_series["current_capacity_pct_bol"],
            mode="lines+markers",
            name="Current capacity (% of BOL)",
            yaxis="y2",
            customdata=curr_cap_series[["current_capacity_kwh"]].to_numpy(),
            hovertemplate=(
                "Current capacity: %{customdata[0]:.2f} kWh<br>"
                "% of BOL: %{y:.2f} %<br>"
                "Time: %{x:.2f} min"
                "<extra></extra>"
            ),
        )
    )

    # Max capacity % of BOL (+ kWh)
    fig.add_trace(
        go.Scatter(
            x=max_cap_series["time_offset_s"],
            y=max_cap_series["max_capacity_pct_bol"],
            mode="lines+markers",
            name="Max capacity (% of BOL)",
            yaxis="y2",
            customdata=max_cap_series[["max_capacity_kwh"]].to_numpy(),
            hovertemplate=(
                "Max capacity: %{customdata[0]:.2f} kWh<br>"
                "% of BOL: %{y:.2f} %<br>"
                "Time: %{x:.2f} min"
                "<extra></extra>"
            ),
        )
    )

    # SOH from max energy (derived from max_capacity_kwh)
    fig.add_trace(
        go.Scatter(
            x=soh_energy_series["time_offset_s"],
            y=soh_energy_series["soh_energy_pct"],
            mode="lines+markers",
            name="SOH based on max energy (% of BOL)",
            yaxis="y2",
            line=dict(dash="dash"),
            customdata=soh_energy_series[["max_capacity_kwh"]].to_numpy(),
            hovertemplate=(
                "SOH (max energy): %{y:.2f} % of BOL<br>"
                "Max capacity: %{customdata[0]:.2f} kWh<br>"
                "Time: %{x:.2f} min"
                "<extra></extra>"
            ),
        )
    )

    # SOH from estimated_capacity_kwh
    fig.add_trace(
        go.Scatter(
            x=soh_est_series["time_offset_s"],
            y=soh_est_series["soh_estimated_pct"],
            mode="lines+markers",
            name="SOH estimated (% of BOL)",
            yaxis="y2",
            line=dict(dash="dot"),
            customdata=soh_est_series[["estimated_capacity_kwh"]].to_numpy(),
            hovertemplate=(
                "SOH (estimated): %{y:.2f} % of BOL<br>"
                "Est. capacity: %{customdata[0]:.2f} kWh<br>"
                "Time: %{x:.2f} min"
                "<extra></extra>"
            ),
        )
    )

    # Optional vertical marker
    t_mark = float(df_with_estimated_and_physical_signals["time_offset_s"].median())
    fig.add_vline(x=t_mark, line_dash="dot", line_color="gray")

    fig.update_layout(
        title="Audi Q4 40 – SOC, Capacity & SOH (all in % of BOL)",
        xaxis=dict(
            title="Time (minutes)",
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
        ),
        yaxis=dict(title="SOC (%)", side="left"),
        yaxis2=dict(
            title="Capacity / SOH (% of BOL)",
            overlaying="y",
            side="right",
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="left",
            x=0,
        ),
    )

    fig.show()
    return fig
