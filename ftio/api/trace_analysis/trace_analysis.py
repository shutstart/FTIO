import os
import sys
import json
from rich.console import Console
from rich.progress import Progress
import numpy as np
import pandas as pd
from ftio.api.trace_analysis.trace_ftio_v2 import main as trace_ftio

console = Console()

def main(argv=sys.argv[1:]) -> None:
    pattern = "_signal_plafrim.csv"
    df = pd.DataFrame()

    # Handle command-line arguments properly
    if len(argv) > 0:
        folder_path = argv[0]
        argv.pop(0)
    else:
        # folder_path = os.getcwd()
        folder_path = "/d/github/FTIO/ftio/api/trace_analysis/platfrim"

    folder_path = os.path.abspath(folder_path)
    console.print(f"[bold green]Path is: {folder_path}[/]")

    # Create a list to store all matching csv files
    csv_files = []

    # Walk through all subdirectories and find matching files
    for dirpath, _, filenames in os.walk(folder_path):
        for filename in filenames:
            if filename.endswith(pattern):
                csv_files.append(os.path.join(dirpath, filename))

    if not csv_files:
        console.print("[bold red]No files matched the pattern![/]")
        return

    try:
        with Progress() as progress:
            task = progress.add_task("[green]Processing files...", total=len(csv_files))

            # Iterate over each csv file
            for file_path in csv_files:
                    # Display the file being processed
                progress.console.print(f"Processing: {file_path}")

                # Run the trace_ftio function
                
                
                res = trace_ftio([file_path]+argv,False)
                
                # Create the new file name by replacing the pattern
                base_name = os.path.basename(file_path)
                new_file_name = base_name.replace("_signal_plafrim.csv", "_freq_plafrim.json")
                new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)

                # Write the content to the new file
                # with open(new_file_path, "w", newline=") as file:
                #     file.write(str(res))
                # Convert NumPy arrays to lists
                data_converted = convert_dict(res)
                with open(new_file_path, "w") as file:
                    json.dump(data_converted, file, indent=4)

                flat_res = flatten_dict(res)
                try:
                    flat_res["job_id"] = base_name.split("_")[0]
                except:
                    flat_res["job_id"] = "??"
                new_row_df = pd.DataFrame([flat_res])
                # Append the new row DataFrame to the existing DataFrame
                df = pd.concat([df, new_row_df], ignore_index=True)

                # Update the progress bar
                progress.advance(task)
                
        progress.console.print("[bold green]All files processed successfully![/]")
        df.to_csv("ftio.csv", index=False)
        statisitcs(df)
    except KeyboardInterrupt:
        progress.console.print("[bold red]Keyboard interrupt![/]")
        statisitcs(df)
        sys.exit()
        

def convert_dict(data):
    """Convert NumPy arrays and sets to lists in the dictionary."""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, np.ndarray):
                data[key] = value.tolist()
            elif isinstance(value, set):
                data[key] = list(value)
            elif isinstance(value, dict):
                convert_dict(value)
    return data



def flatten_dict(d):
    """Flatten the dictionary for DataFrame insertion."""
    flat = {}
    for key, value in d.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, np.ndarray):
                    # Convert numpy arrays to lists
                    flat[f"{key}_{sub_key}"] = sub_value.tolist()
                elif isinstance(sub_value, set):
                    # Convert sets to lists
                    flat[f"{key}_{sub_key}"] = list(sub_value)
                else:
                    flat[f"{key}_{sub_key}"] = sub_value
        else:
            flat[key] = value
    return flat


def periodic_apps(df):
    values = ["read", "write", "both"]
    all = len(df[f'{values[0]}_dominant_freq'])
    for mode in values:
        n = df[f'{mode}_dominant_freq'].apply(lambda x: len(x)>0).sum()
        console.print(f"[blue]Periodic {mode.capitalize()}: {n:.2f}/{all:.2f} ({n/all*100}%)[/]")

def statisitcs(df):
    print(df)
    periodic_apps(df)
    dom_df = reduce_to_max_conf(df)
    # print(dom_df)
    min_max_mean(dom_df)
    min_max_mean(dom_df,"dominant_freq")
    


def min_max_mean(df,suffix="conf"):
    prefixes = ["read", "write", "both"]
    for prefix in prefixes:    
        conf_col = f"{prefix}_{suffix}"
        min = np.min(df[conf_col])
        max = np.max(df[conf_col])
        mean= np.mean(df[conf_col])
        median= np.median(df[conf_col])
        nanmean= np.nanmean(df[conf_col])
        nanmedian= np.nanmedian(df[conf_col])
        scale = 100 if "conf" in suffix else 1
        console.print(f"[green]{prefix.capitalize()} {suffix.capitalize()}:\n - range: [{min*scale:.2f},{max*scale:.2f}]\n - mean: {mean*scale:.2f}\n - nanmean: {nanmean*scale:.2f}\n - median:{median*scale:.2f}\n - nanmedian:{nanmedian*scale:.2f}\n[/]")
        
def reduce_to_max_conf(df):
    prefixes = ["read", "write", "both"]
    # Iterate over each row
    for i, row in df.iterrows():
        for prefix in prefixes:    
            conf_col = f"{prefix}_conf"
            freq_col = f"{prefix}_dominant_freq"
            freq = np.nan
            conf = np.nan
            if isinstance(row[conf_col], list) and len(row[conf_col]) > 0:  
                dominant_index = np.argmax(row[conf_col])
                freq = row[freq_col][dominant_index]
                conf = row[conf_col][dominant_index]
            df.at[i, conf_col] = conf
            df.at[i, freq_col] = freq
        
    return df

if __name__ == "__main__":
    main(sys.argv[1:])
