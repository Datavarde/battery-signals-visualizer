import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from app.dtos.models import Audi_Q4_40_CANSignal, CANSignal

CAPACITY_AT_BOL_kWh = 86

pio.renderers.default = "browser"


def append_physical_signals_to_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    hv_battery_soc_mask = df["pid"] == CANSignal.MIN_CELL_SOC.pid
    hv_battery_soc_raw = df.loc[hv_battery_soc_mask, "d4"]
    df.loc[hv_battery_soc_mask, "hv_battery_soc"] = (
        hv_battery_soc_raw * CANSignal.MIN_CELL_SOC.scaling
    )

    hv_battery_voltage_mask = df["pid"] == CANSignal.HV_BATTERY_VOLTAGE.pid
    hv_battery_voltage_raw = df["d4"] * 256 + df["d5"]
    df.loc[hv_battery_voltage_mask, "hv_battery_voltage"] = (
        hv_battery_voltage_raw * CANSignal.HV_BATTERY_VOLTAGE.scaling
    )

    hv_battery_current_mask = df["pid"] == CANSignal.HV_BATTERY_CURRENT.pid
    hv_battery_current_raw = df["d6"]
    df.loc[hv_battery_current_mask, "hv_battery_current"] = (
        hv_battery_current_raw * CANSignal.HV_BATTERY_CURRENT.scaling
    )

    hv_battery_temperature_mask = df["pid"] == CANSignal.BMS_BATTERY_TEMPERATURE.pid
    hv_battery_temperature_raw = df["d4"]
    df.loc[hv_battery_temperature_mask, "hv_battery_temperature"] = (
        hv_battery_temperature_raw * CANSignal.BMS_BATTERY_TEMPERATURE.scaling
        + CANSignal.BMS_BATTERY_TEMPERATURE.offset
    )

    hv_battery_current_energy_capacity_mask = (
        df["pid"] == CANSignal.HV_BATTERY_CURRENT_ENERGY_CAPACITY.pid
    )
    hv_battery_current_energy_raw = df["d5"] * 256 + df["d6"]
    df.loc[hv_battery_current_energy_capacity_mask, "hv_battery_current_energy"] = (
        hv_battery_current_energy_raw
        * CANSignal.HV_BATTERY_CURRENT_ENERGY_CAPACITY.scaling
        + CANSignal.HV_BATTERY_CURRENT_ENERGY_CAPACITY.offset
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


def append_physical_signals_to_dataframe_for_q4_etron(df: pd.DataFrame) -> pd.DataFrame:
    hv_battery_soc_mask = df["pid"] == Audi_Q4_40_CANSignal.MIN_CELL_SOC.pid
    hv_battery_soc_raw = df["d4"] * 256 + df["d5"]

    df.loc[hv_battery_soc_mask, "hv_battery_soc"] = (
        hv_battery_soc_raw * Audi_Q4_40_CANSignal.MIN_CELL_SOC.scaling
    )

    hv_battery_current_energy_capacity_mask = (
        df["pid"] == Audi_Q4_40_CANSignal.HV_BATTERY_CURRENT_ENERGY_CAPACITY.pid
    )
    hv_battery_current_energy_raw = df["d5"] * 256 + df["d6"]
    df.loc[hv_battery_current_energy_capacity_mask, "hv_battery_current_energy"] = (
        hv_battery_current_energy_raw
        * Audi_Q4_40_CANSignal.HV_BATTERY_CURRENT_ENERGY_CAPACITY.scaling
        + Audi_Q4_40_CANSignal.HV_BATTERY_CURRENT_ENERGY_CAPACITY.offset
    )

    max_energy_capacity_mask = df["pid"] == Audi_Q4_40_CANSignal.MAX_ENERGY_CAPACITY.pid
    max_energy_capacity_raw = (
        df["d4"] * 16777216 + df["d5"] * 65536 + df["d6"] * 256 + df["d7"]
    )
    df.loc[max_energy_capacity_mask, "max_energy_capacity"] = (
        max_energy_capacity_raw * Audi_Q4_40_CANSignal.MAX_ENERGY_CAPACITY.scaling
        + Audi_Q4_40_CANSignal.MAX_ENERGY_CAPACITY.offset
    )
    return df
    # ---------- NEW: estimated total capacity (kWh) ----------
    # SOC is in %, convert to fraction, avoid div-by-zero


def plot_signals_for_q4_etron(processed_df: pd.DataFrame) -> go.Figure:
    soc_series = processed_df.dropna(subset=["hv_battery_soc"])
    curr_cap_series = processed_df.dropna(subset=["hv_battery_current_energy"])
    max_cap_series = processed_df.dropna(subset=["max_energy_capacity"])

    fig = go.Figure()

    # ---- 1. SOC on left axis ----
    fig.add_trace(
        go.Scatter(
            x=soc_series["time_offset_s"],
            y=soc_series["hv_battery_soc"],
            mode="lines+markers",
            name="SOC (%)",
            yaxis="y",
            hovertemplate="Time: %{x:.2f} min<br>SOC: %{y:.2f} %",
        )
    )

    # ---- 2. Current capacity ----
    fig.add_trace(
        go.Scatter(
            x=curr_cap_series["time_offset_s"],
            y=curr_cap_series["hv_battery_current_energy"],
            mode="lines+markers",
            name="Current capacity (kWh)",
            yaxis="y2",
            visible=False,
            hovertemplate="Time: %{x:.2f} min<br>Current cap: %{y:.2f} kWh",
        )
    )

    # ---- 3. Max capacity ----
    fig.add_trace(
        go.Scatter(
            x=max_cap_series["time_offset_s"],
            y=max_cap_series["max_energy_capacity"],
            mode="lines+markers",
            name="Max capacity (kWh)",
            yaxis="y2",
            visible=True,
            hovertemplate="Time: %{x:.2f} min<br>Max cap: %{y:.2f} kWh",
        )
    )

    # ---- Axes ----
    fig.update_layout(
        xaxis=dict(
            title="Time (minutes)",
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
        ),
        yaxis=dict(
            title="SOC (%)",
            side="left",
            rangemode="tozero",
        ),
        yaxis2=dict(
            title="Capacity (kWh)",
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
        title="Audi Q4 40 – SOC vs Current & Max Capacity",
    )

    fig.show()
    return fig


def build_dashboard(df: pd.DataFrame) -> go.Figure:
    print(df["pid"].value_counts())
    processed_dataframe = append_physical_signals_to_dataframe(df).copy()

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
