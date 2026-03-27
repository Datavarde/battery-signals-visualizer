import pandas as pd
import plotly.graph_objects as go
from app.dtos.audi_quattro import (
    AUDI_QUATTRO_PLOT_SIGNALS,
    AUDI_E_TRON_QUATTRO_55_CAPACITY_AT_BOL_kWh,
)
from app.utils.plot_helper import (
    create_traces_for_signals,
    get_layout_y_axis_name,
    set_axes_visibility_for_the_selected_signals,
    set_trace_visibility_mask_based_on_selected_signals,
)

import numpy as np


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


SIGNALS_TO_PRINT = [
    "hv_battery_voltage",
    "hv_battery_current",
    "hv_battery_current_energy",
    "hv_battery_soc_hr",
    "soc_disp_percent",
    "min_cell_soc",
    "estimated_capacity_kwh",
    "soh_percent",
]


def add_axes_definition_to_figure(fig: go.Figure, log_name: str) -> dict[str, dict]:
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
        "yaxis4": dict(
            title="Energy Capacity (kWh)",
            side="right",
            position=1.0,
            overlaying="y",
            visible=False,
            showgrid=False,
        ),
        "yaxis5": dict(
            title="SOH (%)",
            side="right",
            position=0.94,
            overlaying="y",
            visible=False,
            showgrid=False,
        ),
    }

    fig.update_layout(
        title=f"HV Battery Signals : <b>{log_name}</b>",
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


def append_estimated_signals_for_audi_quattro(
    *, df_with_physical_signals: pd.DataFrame
) -> pd.DataFrame:
    df_with_estimated_and_physical_signals = df_with_physical_signals.copy()
    soc_ffill = (
        df_with_estimated_and_physical_signals["hv_battery_soc_hr"]
        .ffill()
        .astype("Float64")
        .astype("float64")
    )
    energy = (
        df_with_estimated_and_physical_signals["hv_battery_current_energy"]
        .astype("Float64")
        .astype("float64")
    )
    # soc values are lesser compared to current_energy , therefore there is
    # forward filled data of soc
    soc_arr = soc_ffill.to_numpy()
    energy_arr = energy.to_numpy()

    valid = np.isfinite(energy_arr) & np.isfinite(soc_arr) & (soc_arr > 0)
    df_with_estimated_and_physical_signals["estimated_capacity_kwh"] = energy_arr / (
        soc_arr / 100.0
    )
    df_with_estimated_and_physical_signals.loc[~valid, "estimated_capacity_kwh"] = (
        np.nan
    )
    df_with_estimated_and_physical_signals["soh_percent"] = (
        df_with_estimated_and_physical_signals["estimated_capacity_kwh"]
        / AUDI_E_TRON_QUATTRO_55_CAPACITY_AT_BOL_kWh
        * 100.0
    )

    return df_with_estimated_and_physical_signals


def build_dashboard_for_audi_quattro(
    *, df_with_estimated_and_physical_signals, log_name: str
) -> None:

    did_series = (
        df_with_estimated_and_physical_signals["payload"]
        .apply(
            lambda p: (
                f"{((p[1] << 8) | p[2]):04X}"
                if isinstance(p, list) and len(p) >= 3
                else None
            )
        )
        .dropna()
    )
    print(f"did_series:{did_series.value_counts()}")
    print(f"df_snapshot:{df_with_estimated_and_physical_signals.head(10)}")
    for signal_name in SIGNALS_TO_PRINT:
        print(
            f"Min Limit for {signal_name}: "
            f"{df_with_estimated_and_physical_signals[signal_name].min()}\n"
            f"Max Limits for {signal_name}:"
            f"{df_with_estimated_and_physical_signals[signal_name].max()}"
        )

    cols = [ps.df_column for ps in AUDI_QUATTRO_PLOT_SIGNALS]

    print(
        df_with_estimated_and_physical_signals[cols]
        .notna()
        .sum()
        .sort_values(ascending=False)
    )

    cols = [ps.df_column for ps in AUDI_QUATTRO_PLOT_SIGNALS]
    print(
        df_with_estimated_and_physical_signals[cols]
        .notna()
        .sum()
        .sort_values(ascending=False)
    )

    fig, trace_index, ranges = create_traces_for_signals(
        df_with_physical_and_estimated_signals=df_with_estimated_and_physical_signals,
        signals_to_plot=AUDI_QUATTRO_PLOT_SIGNALS,
    )
    axis_defs = add_axes_definition_to_figure(fig=fig, log_name=log_name)
    buttons = []

    def pad_label(text: str, width: int = 26) -> str:
        # regular spaces can get collapsed visually; NBSP is more reliable in
        # Plotly labels
        return (text + "\u00a0" * width)[:width]

    # Build dropdown buttons (IMPORTANT: add "Combined" only once, after loop)

    for plot_signal in AUDI_QUATTRO_PLOT_SIGNALS:
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
                            plot_signals=AUDI_QUATTRO_PLOT_SIGNALS,
                            axis_defs=axis_defs,
                        ),
                        (
                            f"{get_layout_y_axis_name(plot_signal.yaxis)}"
                            ".title.text"
                        ): plot_signal.ytitle,
                        f"{get_layout_y_axis_name(plot_signal.yaxis)}.range": ranges[
                            plot_signal.key
                        ],
                    },
                ],
            )
        )

    combo_keys = {
        "hv_battery_soc_hr",
        "min_cell_soc",
        "soc_disp_percent",
        "hv_battery_current_energy",
        "estimated_capacity_kwh",
        "soh_percent",
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
                        plot_signals=AUDI_QUATTRO_PLOT_SIGNALS,
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
