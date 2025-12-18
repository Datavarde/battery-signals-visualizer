from app.dtos.models import PlotSignal


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
        updates[f"{ax_key}.visible"] = ax_key in used_layout_axes

    return updates
