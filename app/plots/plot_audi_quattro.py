import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from app.dtos.models import Audi_Quattro_CAN_Signal, PLOT_SIGNALS
from app.utils.plot_helper import (
    get_layout_y_axis_name,
    set_axes_visibility_for_the_selected_signals,
    set_trace_visibility_mask_based_on_selected_signals,
)
from app.utils.signal_processor import append_physical_signals_to_dataframe
import numpy as np

CAPACITY_AT_BOL_kWh = 86


def _add_estimated_capacity_to_the_dataframe(df) -> None:
    soc_ffill = df["hv_battery_soc_hr"].ffill().astype("Float64").astype("float64")
    energy = df["hv_battery_current_energy"].astype("Float64").astype("float64")
    # soc values are lesser compared to current_energy , therefore there is forward filled data of soc
    soc_arr = soc_ffill.to_numpy()
    energy_arr = energy.to_numpy()

    valid = np.isfinite(energy_arr) & np.isfinite(soc_arr) & (soc_arr > 0)
    df["estimated_capacity_kwh"] = energy_arr / (soc_arr / 100.0)
    df.loc[~valid, "estimated_capacity_kwh"] = np.nan


def _add_energy_from_vi_kwh_to_the_dataframe(df) -> None:
    # Ensure numeric
    t = pd.to_numeric(df["time_offset_s"], errors="coerce")
    v = pd.to_numeric(df["hv_battery_voltage"], errors="coerce")

    i = pd.to_numeric(df["hv_battery_current"], errors="coerce")

    # dt in seconds
    dt = t.diff()
    dt.iloc[0] = 0.0
    dt_s = dt * 60.0

    # Hold last sample (because V/I are sparse vs time base)
    v_ff = v.ffill()
    i_ff = i.ffill()

    # Power (W). If still NaN at the beginning, treat as 0.
    power_w = (v_ff * i_ff).fillna(0.0)

    df["energy_from_vi_kwh"] = (power_w * dt_s).cumsum() / 3_600_000.0


def _estimate_signals_for_audi_quattro(df: pd.DataFrame) -> pd.DataFrame:
    _add_estimated_capacity_to_the_dataframe(df)
    df["soh_percent"] = df["estimated_capacity_kwh"] / CAPACITY_AT_BOL_kWh * 100.0

    _add_energy_from_vi_kwh_to_the_dataframe(df)

    e_vi0 = df["energy_from_vi_kwh"].dropna().iloc[0]
    df["energy_vi_from_t1"] = df["energy_from_vi_kwh"] - e_vi0

    # --- UDS energy: choose whether you want sparse or dense comparison ---
    uds = pd.to_numeric(df["hv_battery_current_energy"], errors="coerce")

    # forward-fill UDS energy to compare at every timestamp
    uds_ff = uds.ffill()
    uds0 = uds_ff.dropna().iloc[0]
    df["hv_battery_current_energy_from_t1"] = uds_ff - uds0

    # --- Delta ---
    df["delta_energy_kwh"] = (
        df["energy_vi_from_t1"] - df["hv_battery_current_energy_from_t1"]
    )

    return df


def create_traces(
    df: pd.DataFrame,
) -> tuple[go.Figure, dict[str, int], dict[str, list[float]]]:

    fig = go.Figure()

    # Track which trace index corresponds to which signal key
    trace_index: dict[str, int] = {}
    y_axis_range: dict[str, list[float]] = {}

    # Create traces from registry
    for plot_signal in PLOT_SIGNALS:
        if plot_signal.column not in df.columns:
            continue

        plot_signal_and_time = df[["time_offset_s", plot_signal.column]].dropna(
            subset=[plot_signal.column]
        )
        if plot_signal_and_time.empty:
            continue

        cleaned_plot_signal = plot_signal_and_time[plot_signal.column].astype("float64")
        y_axis_range[plot_signal.key] = (
            plot_signal.range_fn(cleaned_plot_signal)
            if plot_signal.range_fn
            else [float(cleaned_plot_signal.min()), float(cleaned_plot_signal.max())]
        )

        trace_index[plot_signal.key] = len(fig.data)
        fig.add_trace(
            go.Scatter(
                x=plot_signal_and_time["time_offset_s"],
                y=cleaned_plot_signal,
                mode="lines+markers",
                name=plot_signal.label,
                visible=plot_signal.visible_by_default,
                yaxis=plot_signal.yaxis,  # "y", "y2", ...
                hovertemplate=f"Time: %{{x:.2f}} min<br>{plot_signal.label}: %{{y:{plot_signal.hover_yfmt}}}",
            )
        )
    return fig, trace_index, y_axis_range


def add_axes_definition_to_figure(fig: go.Figure) -> dict[str, dict]:
    # Build a stable axis layout (define all axes you might use)
    axis_defs = {
        "yaxis": dict(title="SOC (%)", side="left", position=0.20, visible=True),
        "yaxis2": dict(
            title="Voltage (V)",
            side="left",
            position=0.26,
            overlaying="y",
            visible=False,
            showgrid=False,
        ),
        "yaxis3": dict(
            title="Current (A)",
            side="left",
            position=0.32,
            overlaying="y",
            visible=False,
            showgrid=False,
        ),
        "yaxis5": dict(
            title="Energy / Capacity (kWh)",
            side="right",
            position=1.0,
            overlaying="y",
            visible=False,
            showgrid=False,
        ),
        "yaxis6": dict(
            title="SOH (%)",
            side="right",
            position=0.94,
            overlaying="y",
            visible=False,
            showgrid=False,
        ),
    }

    fig.update_layout(
        title="HV Battery Signals",
        hovermode="x unified",
        xaxis=dict(
            title="Time (minutes)",
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0),
        **axis_defs,
    )
    return axis_defs


def build_dashboard_for_audi_quattro(df):
    df = append_physical_signals_to_dataframe(
        df, car_model=Audi_Quattro_CAN_Signal
    ).copy()
    df = _estimate_signals_for_audi_quattro(df)

    cols = [ps.column for ps in PLOT_SIGNALS]
    print(df[cols].notna().sum().sort_values(ascending=False))

    fig, trace_index, ranges = create_traces(df)
    axis_defs = add_axes_definition_to_figure(fig=fig)

    def pad_label(text: str, width: int = 26) -> str:
        # regular spaces can get collapsed visually; NBSP is more reliable in Plotly labels
        return (text + "\u00a0" * width)[:width]

    # Build dropdown buttons (IMPORTANT: add "Combined" only once, after loop)
    buttons = []

    for plot_signal in PLOT_SIGNALS:
        if plot_signal.key not in trace_index:
            continue

        buttons.append(
            dict(
                label=pad_label(plot_signal.label, 28),
                method="update",
                args=[
                    {
                        "visible": set_trace_visibility_mask_based_on_selected_signals(
                            plot_signal_keys={plot_signal.key},
                            number_of_traces=len(fig.data),
                            trace_index=trace_index,
                        )
                    },
                    {
                        **set_axes_visibility_for_the_selected_signals(
                            plot_signal_keys={plot_signal.key},
                            trace_index=trace_index,
                            plot_signals=PLOT_SIGNALS,
                            axis_defs=axis_defs,
                        ),
                        f"{get_layout_y_axis_name(plot_signal.yaxis)}.title.text": plot_signal.ytitle,
                        f"{get_layout_y_axis_name(plot_signal.yaxis)}.range": ranges[
                            plot_signal.key
                        ],
                    },
                ],
            )
        )

    combo_keys = {
        "soc",
        "volt",
        "current",
        "current_energy",
        "estimated_capacity_kwh",
        "soh_percent",
        "energy_from_vi_kwh",
        "delta_energy_kwh",
    }

    buttons.append(
        dict(
            label=pad_label("Combined", 28),  # ✅ padded width
            method="update",
            args=[
                {
                    "visible": set_trace_visibility_mask_based_on_selected_signals(
                        plot_signal_keys=combo_keys,
                        number_of_traces=len(fig.data),
                        trace_index=trace_index,
                    )
                },
                {
                    **set_axes_visibility_for_the_selected_signals(
                        plot_signal_keys=combo_keys,
                        trace_index=trace_index,
                        plot_signals=PLOT_SIGNALS,
                        axis_defs=axis_defs,
                    ),
                    # optionally set ranges for combined views if you want:
                    # "yaxis.range": ranges.get("soc", None),
                },
            ],
        )
    )

    # Reserve space on the left for the button column
    fig.update_layout(
        margin=dict(l=320, r=140, t=90, b=60),
    )

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="down",
                x=-0.22,
                y=1.0,
                xanchor="left",
                yanchor="top",
                buttons=buttons,
                showactive=True,
                font=dict(size=14),  # height (bigger font = taller buttons)
                bgcolor="white",
                borderwidth=1,
                pad=dict(t=2, b=2, l=2, r=2),
            )
        ]
    )

    fig.show()
