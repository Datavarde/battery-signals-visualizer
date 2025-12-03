import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from app.dtos.models import Audi_Quattro_CAN_Signal
from app.utils.signal_processor import append_physical_signals_to_dataframe_for_q4_etron

CAPACITY_AT_BOL_kWh = 86
Q4_ETRON_CAPACITY_AT_BOL_kWh = 76

pio.renderers.default = "browser"


def append_physical_signals_to_dataframe_for_quattro(df: pd.DataFrame) -> pd.DataFrame:
    hv_battery_soc_mask = df["pid"] == Audi_Quattro_CAN_Signal.MIN_CELL_SOC.pid
    hv_battery_soc_raw = df.loc[hv_battery_soc_mask, "d4"]
    df.loc[hv_battery_soc_mask, "hv_battery_soc"] = (
        hv_battery_soc_raw * Audi_Quattro_CAN_Signal.MIN_CELL_SOC.scaling
    )

    hv_battery_voltage_mask = (
        df["pid"] == Audi_Quattro_CAN_Signal.HV_BATTERY_VOLTAGE.pid
    )
    hv_battery_voltage_raw = df["d4"] * 256 + df["d5"]
    df.loc[hv_battery_voltage_mask, "hv_battery_voltage"] = (
        hv_battery_voltage_raw * Audi_Quattro_CAN_Signal.HV_BATTERY_VOLTAGE.scaling
    )

    hv_battery_current_mask = (
        df["pid"] == Audi_Quattro_CAN_Signal.HV_BATTERY_CURRENT.pid
    )
    hv_battery_current_raw = df["d6"]
    df.loc[hv_battery_current_mask, "hv_battery_current"] = (
        hv_battery_current_raw * Audi_Quattro_CAN_Signal.HV_BATTERY_CURRENT.scaling
    )

    hv_battery_temperature_mask = (
        df["pid"] == Audi_Quattro_CAN_Signal.BMS_BATTERY_TEMPERATURE.pid
    )
    hv_battery_temperature_raw = df["d4"]
    df.loc[hv_battery_temperature_mask, "hv_battery_temperature"] = (
        hv_battery_temperature_raw
        * Audi_Quattro_CAN_Signal.BMS_BATTERY_TEMPERATURE.scaling
        + Audi_Quattro_CAN_Signal.BMS_BATTERY_TEMPERATURE.offset
    )

    hv_battery_current_energy_capacity_mask = (
        df["pid"] == Audi_Quattro_CAN_Signal.HV_BATTERY_CURRENT_ENERGY_CAPACITY.pid
    )
    hv_battery_current_energy_raw = df["d5"] * 256 + df["d6"]
    df.loc[hv_battery_current_energy_capacity_mask, "hv_battery_current_energy"] = (
        hv_battery_current_energy_raw
        * Audi_Quattro_CAN_Signal.HV_BATTERY_CURRENT_ENERGY_CAPACITY.scaling
        + Audi_Quattro_CAN_Signal.HV_BATTERY_CURRENT_ENERGY_CAPACITY.offset
    )

    soc_ffill = df["hv_battery_soc"].ffill()  # still in %
    energy = df["hv_battery_current_energy"]  # kWh

    valid_mask = energy.notna() & soc_ffill.notna() & (soc_ffill > 0)

    df["estimated_capacity_kwh"] = pd.NA
    df.loc[valid_mask, "estimated_capacity_kwh"] = energy.loc[valid_mask] / (
        soc_ffill.loc[valid_mask] / 100.0
    )
    df["soh_percent"] = pd.NA
    soh_mask = df["estimated_capacity_kwh"].notna()
    df.loc[soh_mask, "soh_percent"] = (
        df.loc[soh_mask, "estimated_capacity_kwh"] / CAPACITY_AT_BOL_kWh * 100.0
    )
    return df


"""


def build_dashboard_for_audi_q4(df: pd.DataFrame) -> go.Figure:
    print(df["pid"].value_counts())

    # 1) Decode signals (adds hv_battery_soc, hv_battery_current_energy, max_energy_capacity)
    processed_df = append_physical_signals_to_dataframe_for_q4_etron(df).copy()

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

"""


def build_dashboard_for_audi_quattro(df: pd.DataFrame) -> go.Figure:
    print(df["pid"].value_counts())
    processed_dataframe = append_physical_signals_to_dataframe_for_quattro(df).copy()

    soc_series = processed_dataframe.dropna(subset=["hv_battery_soc"])
    hv_battery_voltage_series = processed_dataframe.dropna(
        subset=["hv_battery_voltage"]
    )
    hv_battery_current_series = processed_dataframe.dropna(
        subset=["hv_battery_current"]
    )
    hv_battery_temperature_series = processed_dataframe.dropna(
        subset=["hv_battery_temperature"]
    )
    hv_battery_current_energy_series = processed_dataframe.dropna(
        subset=["hv_battery_current_energy"]
    )
    est_series = processed_dataframe.dropna(subset=["estimated_capacity_kwh"])
    soh_series = processed_dataframe.dropna(subset=["soh_percent"])

    # ranges
    soc_range = [
        soc_series["hv_battery_soc"].min(),
        soc_series["hv_battery_soc"].max(),
    ]
    volt_range = [
        hv_battery_voltage_series["hv_battery_voltage"].min(),
        hv_battery_voltage_series["hv_battery_voltage"].max(),
    ]
    hv_battery_current_range = [
        hv_battery_current_series["hv_battery_current"].min(),
        hv_battery_current_series["hv_battery_current"].max(),
    ]
    temperature_range = [
        hv_battery_temperature_series["hv_battery_temperature"].min(),
        hv_battery_temperature_series["hv_battery_temperature"].max(),
    ]
    hv_energy_capacity_range = [
        hv_battery_current_energy_series["hv_battery_current_energy"].min(),
        hv_battery_current_energy_series["hv_battery_current_energy"].max(),
    ]
    est_range = [
        est_series["estimated_capacity_kwh"].min(),
        est_series["estimated_capacity_kwh"].max(),
    ]
    soh_range = [
        soh_series["soh_percent"].min(),
        soh_series["soh_percent"].max(),
    ]

    # combined range for energy + estimated capacity
    energy_est_y_min = min(hv_energy_capacity_range[0], est_range[0])
    energy_est_y_max = max(hv_energy_capacity_range[1], est_range[1])

    fig = go.Figure()

    # Trace indices:
    # 0 SOC, 1 Volt, 2 Current, 3 Temp, 4 Energy, 5 EstCap, 6 SOH

    fig.add_trace(
        go.Scatter(
            x=soc_series["time_offset_s"],
            y=soc_series["hv_battery_soc"],
            mode="lines+markers",
            name="SOC (%)",
            visible=True,
            yaxis="y",
            hovertemplate="Time: %{x:.2f} min<br>SOC: %{y:.2f} %",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=hv_battery_voltage_series["time_offset_s"],
            y=hv_battery_voltage_series["hv_battery_voltage"],
            mode="lines+markers",
            name="Voltage (V)",
            visible=False,
            yaxis="y2",
            hovertemplate="Time: %{x:.2f} min<br>Voltage: %{y:.2f} V",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=hv_battery_current_series["time_offset_s"],
            y=hv_battery_current_series["hv_battery_current"],
            mode="lines+markers",
            name="Current (A)",
            visible=False,
            yaxis="y3",
            hovertemplate="Time: %{x:.2f} min<br>Current: %{y:.2f} A",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=hv_battery_temperature_series["time_offset_s"],
            y=hv_battery_temperature_series["hv_battery_temperature"],
            mode="lines+markers",
            name="Temperature (°C)",
            visible=False,
            yaxis="y4",
            hovertemplate="Time: %{x:.2f} min<br>Temp: %{y:.2f} °C",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=hv_battery_current_energy_series["time_offset_s"],
            y=hv_battery_current_energy_series["hv_battery_current_energy"],
            mode="lines+markers",
            name="Current energy (kWh)",
            visible=False,
            yaxis="y5",
            hovertemplate="Time: %{x:.2f} min<br>Energy: %{y:.2f} kWh",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=est_series["time_offset_s"],
            y=est_series["estimated_capacity_kwh"],
            mode="lines+markers",
            name="Estimated capacity (kWh)",
            visible=False,
            yaxis="y5",
            hovertemplate="Time: %{x:.2f} min<br>Est. cap: %{y:.2f} kWh",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=soh_series["time_offset_s"],
            y=soh_series["soh_percent"],
            mode="lines+markers",
            name="SOH (%)",
            visible=False,
            yaxis="y6",
            hovertemplate="Time: %{x:.2f} min<br>SOH: %{y:.2f} %",
        )
    )

    # Layout & axes
    fig.update_layout(
        xaxis=dict(
            title="Time (minutes)",
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
        ),
        yaxis=dict(  # SOC
            title="SOC (%)",
            rangemode="tozero",
            side="left",
            position=0.0,
        ),
        yaxis2=dict(  # Voltage
            title="Voltage (V)",
            overlaying="y",
            side="left",
            visible=False,
            position=0.04,
            showgrid=False,
        ),
        yaxis3=dict(  # Current
            title="Current (A)",
            overlaying="y",
            side="left",
            visible=False,
            position=0.08,
            showgrid=False,
        ),
        yaxis4=dict(  # Temperature
            title="Temperature (°C)",
            overlaying="y",
            side="left",
            visible=False,
            position=0.12,
            showgrid=False,
        ),
        yaxis5=dict(  # Energy / capacity
            title="Capacity / Energy (kWh)",
            overlaying="y",
            side="right",
            position=1.0,
            showgrid=False,
        ),
        yaxis6=dict(  # SOH
            title="SOH (%)",
            overlaying="y",
            side="right",
            position=0.96,
            showgrid=False,
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="left",
            x=0,
        ),
        title="HV Battery Signals – SOC, Energy, Estimated Capacity & SOH",
    )

    # Dropdown (7 traces now)
    fig.update_layout(
        updatemenus=[
            dict(
                type="dropdown",
                x=0,
                y=1.15,
                xanchor="left",
                buttons=[
                    dict(
                        label="SOC (%)",
                        method="update",
                        args=[
                            {
                                "visible": [
                                    True,
                                    False,
                                    False,
                                    False,
                                    False,
                                    False,
                                    False,
                                ]
                            },
                            {"yaxis.title.text": "SOC (%)", "yaxis.range": soc_range},
                        ],
                    ),
                    dict(
                        label="Voltage (V)",
                        method="update",
                        args=[
                            {
                                "visible": [
                                    False,
                                    True,
                                    False,
                                    False,
                                    False,
                                    False,
                                    False,
                                ]
                            },
                            {
                                "yaxis.title.text": "Voltage (V)",
                                "yaxis.range": volt_range,
                            },
                        ],
                    ),
                    dict(
                        label="Battery Current (A)",
                        method="update",
                        args=[
                            {
                                "visible": [
                                    False,
                                    False,
                                    True,
                                    False,
                                    False,
                                    False,
                                    False,
                                ]
                            },
                            {
                                "yaxis.title.text": "Current (A)",
                                "yaxis.range": hv_battery_current_range,
                            },
                        ],
                    ),
                    dict(
                        label="Battery Temperature (°C)",
                        method="update",
                        args=[
                            {
                                "visible": [
                                    False,
                                    False,
                                    False,
                                    True,
                                    False,
                                    False,
                                    False,
                                ]
                            },
                            {
                                "yaxis.title.text": "Battery Temperature (°C)",
                                "yaxis.range": temperature_range,
                            },
                        ],
                    ),
                    dict(
                        label="SOH (%)",
                        method="update",
                        args=[
                            {
                                "visible": [
                                    False,
                                    False,
                                    False,
                                    False,
                                    False,
                                    False,
                                    True,
                                ]
                            },
                            {"yaxis.title.text": "SOH (%)", "yaxis.range": soh_range},
                        ],
                    ),
                    dict(
                        label="SOC + Energy + Est. Capacity + SOH",
                        method="update",
                        args=[
                            # [SOC, Volt, Curr, Temp, Energy, EstCap, SOH]
                            {"visible": [True, False, False, False, True, True, True]},
                            {
                                "yaxis.title.text": "SOC (%)",
                                "yaxis.range": soc_range,
                                "yaxis5.range": [energy_est_y_min, energy_est_y_max],
                                "yaxis6.range": soh_range,
                            },
                        ],
                    ),
                ],
            )
        ]
    )

    fig.show()
    return fig
