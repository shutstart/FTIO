"""Helper function for frequency techniques    
"""

import plotly.graph_objects as go
from rich.console import Console


def get_mode(data, mode):
    """used after get_data() to extract df. The df
    contains all sims group by mode

    Args:
        data (Scales): simulation data
        mode (str): "read_sync", "write_sync", "read_async" or "write_async"

    Raises:
        Exception: unsupported mode

    Returns:
        df: pandas dataframe containing data group by mode
    """
    mode = mode.lower()
    if "read" in mode:
        if "async" in mode:
            return data.df_rat
        elif "sync" in mode:
            return data.df_rst
    if "write" in mode:
        if "async" in mode:
            return data.df_wat
        elif "sync" in mode:
            return data.df_wst
    raise Exception("undefined mode set")


def get_sim(data, mode):
    mode = mode.lower()
    if "read" in mode:
        if "async" in mode:
            return data.read_async_t
        elif "sync" in mode:
            return data.read_sync
    if "write" in mode:
        if "async" in mode:
            return data.write_async_t
        elif "sync" in mode:
            return data.write_sync
    raise Exception("undefined mode set")



def format_plot(fig) -> go.Figure:
    """makes plots uniform

    Args:
        fig (pltoly figure)
    """
    fig.update_layout(
        plot_bgcolor="white",
        legend=dict(
            bgcolor="rgba(255,255,255,.99)",
            bordercolor="Black",
            borderwidth=1,
        ),
        font=dict(family="Courier New, monospace", size=24, color="black"),
        # margin=dict(l=5, r=5, t=5, b=5) #IEEE
        margin=dict(t=25),
    )

    fig.update_xaxes(
        ticks="outside",
        # tickwidth=1,
        ticklen=10,
        showgrid=True,
        # gridwidth=1,
        mirror=True,
        showline=True,
        linecolor="black",
        gridcolor="lightgrey",
        minor_ticks="outside",
        minor=dict(ticklen=2),
    )

    fig.update_yaxes(
        ticks="outside",
        # tickwidth=1,
        ticklen=10,
        showgrid=True,
        # gridwidth=1,
        mirror=True,
        showline=True,
        linecolor="black",
        gridcolor="lightgrey",
        minor_ticks="outside",
        minor=dict(ticklen=2),
    )

    return fig


def merge_results(
    df0: tuple[list, list, list, list], df1: tuple[list, list, list, list]
) -> tuple[list, list, list, list]:
    """merges results for several files

    Args:
        df0 (list): _description_
        df1 (list): _description_

    Returns:
        list: _description_
    """
    for i in range(0, len(df0)):
        df0[i].extend(df1[i])

    return df0


class MyConsole(Console):
    """Console child class that overwrites
    the print method for silent version

    Args:
        Console (_type_): _description_
    """

    def __init__(self, verbose=False):
        super().__init__()
        self.verbose = verbose

    def set(self, flag):
        if flag:
            self.verbose = True
        else:
            self.verbose = False

    def print(self, *args,**kwargs):
        if self.verbose:
            super().print(*args,**kwargs)

    def info(self, s):
        Console.print(self, s)
