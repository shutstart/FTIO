""" Helper functions"""
from __future__ import annotations
import json
import os
import numpy as np
from rich.console import Console

def get_dominant(prediction: dict) -> float:
    """Gets the dominant frequency based on the confidence

    Args:
        prediction (dict): prediction contacting the dominant frequencies and their confidence

    Returns:
        float: dominant frequency (only one value!)
    """
    dominant_freq = prediction["dominant_freq"]
    conf = prediction["conf"]
    dominant_index = -1
    out = np.nan
    if len(dominant_freq) != 0:
        dominant_index = np.argmax(conf)
        out = dominant_freq[dominant_index]

    return out


def get_dominant_and_conf(prediction: dict) -> tuple[float, float]:
    """Gets the dominant frequency and its confidence based on the confidence

    Args:
        prediction (dict): prediction contacting the dominant frequencies and their confidence

    Returns:
        tuple[float, float]: dominant frequency (only one value!) and corresponding confidence 
    """
    
    dominant_freq = prediction["dominant_freq"]
    conf = prediction["conf"]
    dominant_index = -1
    out_freq = np.nan
    out_conf = np.nan
    if len(dominant_freq) != 0:
        dominant_index = np.argmax(conf)
        out_freq = dominant_freq[dominant_index]
        out_conf = conf[dominant_index]

    return out_freq, out_conf


def print_data(data: list[dict]) -> None:
    """Prints the predictions in a nice format

    Args:
        data [dict]: contacting the predictions
    """
    print("Data collected is:")
    for pred in data:
        string = ""
        for keys, values in pred.items():
            if isinstance(values, float):
                string += f"'{keys}': {values:.2f}, "
            else:
                string += f"'{keys}': {values}, "
        print("{" + string[:-2] + "}")


def get_hits(prediction: dict, count: int, hits):
    """Manges the hit variable. In case a dominant frequency is found, hits is increased. 

    Args:
        prediction (dict): prediction up till now
        count (int): number of the prediction
        hits (Value): how often a dominant frequency was found

    Returns:
        hits: increased value if a dominant frequency was found, otherwise it is reset to 0
    """
    console = Console()
    text = ''
    text += f'[purple][PREDICTOR] (#{count}):[/] Freq candidates: \n'
    for i in range(0,len(prediction['dominant_freq'])):
        text += (
            f'[purple][PREDICTOR] (#{count}):[/]    {i}) '
            f'{prediction["dominant_freq"][i]:.2f} Hz -- conf {prediction["conf"][i]:.2f}\n'
        )
    if  len(prediction["dominant_freq"]) == 1:
        hits.value += 1
        text += f'[purple][PREDICTOR] (#{count}):[/] Current hits {hits.value}\n'
    else:
        hits.value = 0
        text += f'[purple][PREDICTOR] (#{count}):[/][red bold] Resetting hits {hits.value}[/]\n'

    console.print(text[:-1])

    return hits


def export_extrap(data: list[dict], name:str="./freq.jsonl"):
    """Generates measurement points for Extra-p out of the frequency 
    collected at different phases

    Args:
        data (list[dict]): List of predictions
        name (str, optional): Name of the output file. Defaults to "./freq.jsonl".
    """
    extrap_string, ranks = format_jsonl(data)

    if not np.isnan(ranks):
        name = f"./freq_{ranks}.jsonl"
    file = open(name, "w",encoding="utf-8")
    file.write(extrap_string)


def format_jsonl(data: list[dict]) -> tuple[str,str]:
    """Formats the metric as in the JSONL format for Extra-P

    Args:
        data (list[dict]): List of predictions

    Returns:
        tuple[str, str]: formatted string and number of ranks
        
    """
    string = ""
    out_ranks = np.nan
    for pred in data:
        ranks = np.nan
        call_path = "main"
        dominant_freq = np.nan
        for keys, values in pred.items():
            if "dominant_freq" in keys:
                dominant_freq,_ = get_dominant_and_conf(pred)
            if "ranks" in keys:
                ranks = values
            if not np.isnan(dominant_freq) and not np.isnan(ranks):
                string +=f'{{"params":{{"Processes":{ranks}}},"callpath":"{call_path}","metric":"Frequency (Hz)","value":{dominant_freq:e} }}\n'
                out_ranks = ranks
                if dominant_freq > 0:
                    string +=f'{{"params":{{"Processes":{ranks}}},"callpath":"{call_path}","metric":"Period (s)","value":{1/dominant_freq:e} }}\n'
                break

    return string,out_ranks


def dump_json(b:np.ndarray,t:np.ndarray, filename:str="bandwidth.json") -> None:

    data = {
        "b": b.tolist(),
        "t": t.tolist()
    }
    json_file_path = os.path.join(os.getcwd(), filename)

    # Dump the dictionary to a JSON file in the current directory
    with open(json_file_path, "w") as json_file:
        json.dump(data, json_file)