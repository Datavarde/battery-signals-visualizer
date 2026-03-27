import pandas as pd
from app.dtos.models import PlotSignal
import plotly.graph_objects as go


def get_layout_y_axis_name(yaxis_name: str) -> str:
    # "y" -> "yaxis", "y2" -> "yaxis2", ...
    return "yaxis" if yaxis_name == "y" else f"yaxis{yaxis_name[1:]}"


def set_trace_visibility_mask_based_on_selected_signals(
    plot_signal_keys: set[str], number_of_traces: int, trace_index=dict[str, int]
) -> list[bool]:
    """
    Say there are 7 signals to chose from and 1st signal is chosen,
    then this function returns
    [True, False, False, False, False, False, False]
    """

    trace_visibility = [False] * number_of_traces
    for plot_signal_key in plot_signal_keys:
        trace_number = trace_index.get(plot_signal_key)
        if trace_number is not None:
            trace_visibility[trace_number] = True

    return trace_visibility


def set_axes_visibility_for_the_selected_signals(
    plot_signal_keys: set[str],
    trace_index: dict[str, int],
    plot_signals: list[PlotSignal],
    axis_defs: dict[str, dict],
) -> dict:
    """
    Looks at the selected signals, finds which of them are actually plotted,
    figures out which Y-axis each one uses, and collects those axes
    so Plotly knows which axes to turn on.
    """
    used_trace_axes = set()
    for plot_signal_key in plot_signal_keys:
        # Find PlotSignal for key (only if trace exists)
        if plot_signal_key not in trace_index:
            continue
        plot_signal = next(p for p in plot_signals if p.key == plot_signal_key)
        used_trace_axes.add(plot_signal.yaxis)

    # Convert trace yaxis ids -> layout keys
    used_layout_axes = {
        get_layout_y_axis_name(trace_axis) for trace_axis in used_trace_axes
    }

    updates = {}
    for ax_key in axis_defs.keys():
        axis_used = ax_key in used_layout_axes
        updates[f"{ax_key}.visible"] = axis_used
        updates[f"{ax_key}.showticklabels"] = axis_used

    return updates


def create_traces_for_signals(
    *,
    df_with_physical_and_estimated_signals: pd.DataFrame,
    signals_to_plot: list[PlotSignal],
) -> tuple[go.Figure, dict[str, int], dict[str, list[float]]]:
    """
    In this method, individual dataframes containing time_offset_s and signals
    defined in the plot_signals are created
    for example if the signal was defined like
     PlotSignal(
        key="soh_percent",
        df_column="soh",
        label="SOH (%)",
        yaxis="y3",
        ytitle="SOH (%)",
    )
    new dataframe is df[time_offset,soh]
    these goes into plotly's go.scatter(xaxis=time_offset and yaxis=soh)
    """

    fig = go.Figure()

    # Track which trace index corresponds to which signal key
    trace_index: dict[str, int] = {}
    y_axis_range: dict[str, list[float]] = {}

    for plot_signal in signals_to_plot:
        if plot_signal.df_column not in df_with_physical_and_estimated_signals.columns:
            continue

        df_signal_vs_time: pd.DataFrame = (
            df_with_physical_and_estimated_signals[
                ["time_offset_s", plot_signal.df_column]
            ]
            .dropna(subset=[plot_signal.df_column])
            .copy()
        )
        if df_signal_vs_time.empty:
            continue

        cleaned_plot_signal = df_signal_vs_time[plot_signal.df_column].astype(
            "float64"
        )
        y_axis_range[plot_signal.key] = (
            plot_signal.range_fn(cleaned_plot_signal)
            if plot_signal.range_fn
            else [float(cleaned_plot_signal.min()), float(cleaned_plot_signal.max())]
        )

        trace_index[plot_signal.key] = len(fig.data)
        fig.add_trace(
            go.Scatter(
                x=df_signal_vs_time["time_offset_s"],
                y=cleaned_plot_signal,
                mode="lines+markers",
                name=plot_signal.label,
                visible=(
                    plot_signal.key == signals_to_plot[0].key
                ),  # Make the first plot default
                yaxis=plot_signal.yaxis,  # "y", "y2", ...
                hovertemplate=(
                    f"Time: %{{x:.2f}} min<br>{plot_signal.label}: "
                    f"%{{y:{plot_signal.hover_yfmt}}}"
                ),
            )
        )
    return fig, trace_index, y_axis_range
