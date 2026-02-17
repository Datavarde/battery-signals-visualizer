import pandas as pd
from app.dtos.bmw_ix2 import BMW_IX2_PLOT_SIGNALS
from app.utils.plot_helper import (
    create_traces_for_signals,
    get_layout_y_axis_name,
    set_axes_visibility_for_the_selected_signals,
    set_trace_visibility_mask_based_on_selected_signals,
)

import plotly.graph_objects as go

BMW_IX2_Battery_Capacity_BOL = 64  # kWh
SIGNALS_TO_PRINT = [
    "soc",
    "estimated_soh",
]


def add_axes_definition_to_figure(fig: go.Figure, log_name: str) -> dict[str, dict]:
    # Build a stable axis layout (define all axes you might use)
    axis_defs = {
        "yaxis": dict(
            title="SOC (%)", side="left", position=0.06, visible=True, automargin=True
        ),
        "yaxis2": dict(
            title="max_energy_capacity (kWh)",
            side="right",
            position=1.0,
            overlaying="y",
            visible=False,
            showgrid=False,
            automargin=True,
        ),
        "yaxis3": dict(
            title="SOH (%)",
            side="left",
            position=0.11,
            overlaying="y",
            visible=False,
            showgrid=False,
            automargin=True,
        ),
        "yaxis4": dict(
            title="Estimated SOH [Max_Cap/Cap_BoL] (%)",
            side="left",
            position=0.16,
            overlaying="y",
            visible=False,
            showgrid=False,
            automargin=True,
        ),
        "yaxis5": dict(
            title="Estimated Max Energy Capacity (kWh)",
            side="left",
            position=0.19,
            overlaying="y",
            visible=False,
            showgrid=False,
            automargin=True,
        ),
        "yaxis6": dict(
            title="Current Energy Capacity (kWh)",
            side="left",
            position=0.21,
            overlaying="y",
            visible=False,
            showgrid=False,
            automargin=True,
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


def append_estimated_signals_for_bmw_ix2(
    *, df_with_physical_signals: pd.DataFrame, log_name: str
) -> pd.DataFrame:
    df_with_estimated_and_physical_signals = df_with_physical_signals.copy()
    df_with_estimated_and_physical_signals["estimated_soh"] = (
        df_with_physical_signals["max_energy_capacity"] / BMW_IX2_Battery_Capacity_BOL
    ) * 100

    df_with_estimated_and_physical_signals["soc"] = pd.to_numeric(
        df_with_estimated_and_physical_signals["soc"], errors="coerce"
    )
    soc = (
        df_with_estimated_and_physical_signals["soc"]
        .div(100)
        .clip(lower=0, upper=1)
        .ffill()
    )
    # percent -> fraction..where(lambda s: s > 0)
    df_with_estimated_and_physical_signals["estimated_max_energy_capacity"] = (
        df_with_estimated_and_physical_signals["current_energy_capacity"].div(soc)
    )

    return df_with_estimated_and_physical_signals


def build_dashboard_for_bmw_ix2(
    *, df_with_estimated_and_physical_signals: pd.DataFrame, log_name: str
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
            f"Min Limit for {signal_name}: {df_with_estimated_and_physical_signals[signal_name].min()}\n"
            f"Max Limits for {signal_name}:{df_with_estimated_and_physical_signals[signal_name].max()}"
        )

    cols = [ps.df_column for ps in BMW_IX2_PLOT_SIGNALS]

    print(
        df_with_estimated_and_physical_signals[cols]
        .notna()
        .sum()
        .sort_values(ascending=False)
    )

    fig, trace_index, ranges = create_traces_for_signals(
        df_with_physical_and_estimated_signals=df_with_estimated_and_physical_signals,
        signals_to_plot=BMW_IX2_PLOT_SIGNALS,
    )
    axis_defs = add_axes_definition_to_figure(fig=fig, log_name=log_name)
    buttons = []

    def pad_label(text: str, width: int = 26) -> str:
        # regular spaces can get collapsed visually; NBSP is more reliable in Plotly labels
        return (text + "\u00a0" * width)[:width]

    for plot_signal in BMW_IX2_PLOT_SIGNALS:
        if plot_signal.key not in trace_index:
            continue

        buttons.append(
            dict(
                label=pad_label(plot_signal.label, 20),
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
                            plot_signals=BMW_IX2_PLOT_SIGNALS,
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
    # Add the key names mentioned in the PlotSignal
    combo_keys = {
        "soc",
        "estimated_soh",
        "max_energy_capacity",
        "current_energy_capacity",
        "estimated_max_energy_capacity",
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
                        plot_signals=BMW_IX2_PLOT_SIGNALS,
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
        margin=dict(l=300, r=150, t=90, b=60),
    )
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="down",
                x=-0.42,
                y=0.98,
                xanchor="left",
                yanchor="top",
                buttons=buttons,
                showactive=True,
                font=dict(size=12),  # height (bigger font = taller buttons)
                bgcolor="white",
                borderwidth=1,
                pad=dict(t=2, b=2, l=2, r=2),
            )
        ]
    )

    fig.show()
