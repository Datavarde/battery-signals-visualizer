import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from app.dtos.models import Audi_Q4_40_CANSignal, Audi_Quattro_CAN_Signal, SignalDef
from app.utils.load_log_file import build_payload_column
from app.utils.signal_processor import (
    _compute_raw_from_payload,
    append_physical_signals_to_dataframe,
)


Q4_ETRON_CAPACITY_AT_BOL_kWh = 76

pio.renderers.default = "browser"


def build_dashboard_for_audi_q4(df: pd.DataFrame) -> None:
    print(df["pid"].value_counts())

    # 1) Decode signals (adds hv_battery_soc, hv_battery_current_energy, max_energy_capacity)

    processed_df = append_physical_signals_to_dataframe(df, Audi_Q4_40_CANSignal).copy()

    # ---- sanity check: make sure columns exist ----
    required_cols = [
        "hv_battery_soc",
        "hv_battery_current_energy",
        "max_energy_capacity",
    ]
    missing = [c for c in required_cols if c not in processed_df.columns]
    if missing:
        raise RuntimeError(f"Missing expected columns after decoding: {missing}")

    # raw → kWh
    processed_df["current_capacity_kwh"] = (
        processed_df["hv_battery_current_energy"] / 1000.0
    )
    processed_df["max_capacity_kwh"] = processed_df["max_energy_capacity"] / 1000.0

    # derived quantities
    processed_df["soc_frac"] = processed_df["hv_battery_soc"] / 100.0

    processed_df["estimated_capacity_kwh"] = pd.NA
    mask_cap = (
        processed_df["current_capacity_kwh"].notna()
        & processed_df["soc_frac"].notna()
        & (processed_df["soc_frac"] > 0)
    )
    processed_df.loc[mask_cap, "estimated_capacity_kwh"] = (
        processed_df.loc[mask_cap, "current_capacity_kwh"]
        / processed_df.loc[mask_cap, "soc_frac"]
    )

    processed_df["current_capacity_pct_bol"] = (
        processed_df["current_capacity_kwh"] / Q4_ETRON_CAPACITY_AT_BOL_kWh * 100.0
    )
    processed_df["max_capacity_pct_bol"] = (
        processed_df["max_capacity_kwh"] / Q4_ETRON_CAPACITY_AT_BOL_kWh * 100.0
    )

    processed_df["soh_estimated_pct"] = (
        processed_df["estimated_capacity_kwh"] / Q4_ETRON_CAPACITY_AT_BOL_kWh * 100.0
    )
    processed_df["soh_energy_pct"] = (
        processed_df["max_capacity_kwh"] / Q4_ETRON_CAPACITY_AT_BOL_kWh * 100.0
    )

    # 4) Series with non-NaNs
    soc_series = processed_df.dropna(subset=["hv_battery_soc"])
    curr_cap_series = processed_df.dropna(subset=["current_capacity_pct_bol"])
    max_cap_series = processed_df.dropna(subset=["max_capacity_pct_bol"])
    soh_est_series = processed_df.dropna(subset=["soh_estimated_pct"])
    soh_energy_series = processed_df.dropna(subset=["soh_energy_pct"])

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
    t_mark = float(processed_df["time_offset_s"].median())
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
