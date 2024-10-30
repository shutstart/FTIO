import json
import pandas as pd 
import numpy as np
from rich.progress import (
    Progress,
    SpinnerColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TaskProgressColumn,
    TextColumn,
    BarColumn,
)

def extract_data(data):
    """Extracts relevant data that is not NaN 

    Args:
        data (_type_): _description_

    Returns:
        _type_: _description_
    """
    # Prepare the data for the plot
    data_points = []

    for d in data:
        if len(d['dominant_freq']) > 0 and len(d['conf']) > 0:
            max_conf_index = np.argmax(d['conf'])
            dominant_freq = d['dominant_freq'][max_conf_index]
            conf = d['conf'][max_conf_index]*100
            phi = d['phi'][max_conf_index] #np.degrees(d['phi'][max_conf_index])
            amp = d['amp'][max_conf_index]
            t_s = d['t_start']
            t_e = d['t_end']
            data_points.append((d['metric'], dominant_freq, conf, amp, phi, t_s, t_e))
        else:
            continue 
            data_points.append((d['metric'], np.NaN, np.NaN, np. NaN, np.NaN, np. NaN))

    # Create a DataFrame for the plot
    df = pd.DataFrame(data_points, columns=['Metric', 'Dominant Frequency', 'Confidence', 'Amp', 'Phi', 'time start', 'time end'])
    df.sort_values(by='Dominant Frequency',inplace=True)

    return df



class NpArrayEncode(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            np.nan_to_num(x=obj, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


def data_to_json(data: list[dict]) -> None:
    print(json.dumps(data, cls=NpArrayEncode))


def create_process_bar(total_files):

    
    # Create a progress bar
    progress = Progress(
        SpinnerColumn(),
        TextColumn(
            "[progress.description]{task.description} ({task.completed}/{task.total})"
        ),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        "[yellow]-- runtime",
        TimeElapsedColumn(),
    )
    return progress