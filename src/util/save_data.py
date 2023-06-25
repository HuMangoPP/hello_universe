import numpy as np
import pandas as pd
import os, json

def get_df_from_csv(csv_file: str) -> pd.DataFrame:
    fpath = f'./assets/data/{csv_file}.csv'
    if os.path.isfile(fpath) and os.path.getsize(fpath) > 0:
        return pd.read_csv(fpath)
    return pd.DataFrame()

def write_entity_data_as_csv(sim_time: float, data: dict, csv_file: str) -> pd.DataFrame:
    old_df = get_df_from_csv(csv_file)
    data = {
        key: np.array([value])
        for key, value in data.items()
    }
    df = pd.DataFrame.from_dict(data)
    df['sim_time'] = np.array([sim_time], dtype=np.int32)
    df = pd.concat([old_df, df])
    fpath = f'./assets/data/{csv_file}.csv'
    df.to_csv(fpath, index=False)
    return df

def write_entity_data_as_json(sim_time: float, data: dict, json_file: str) -> dict:
    fpath = f'./assets/data/{json_file}.json'
    with open(fpath, 'r') as f:
        json_data = json.load(f)
        gen_key = f'@{sim_time}'
        if gen_key in json_data:
            json_data[gen_key].append(data)
        else:
            json_data[gen_key] = [data]
    
    with open(fpath, 'w') as f:
        f.write(json.dumps(json_data, indent=4))
        return json_data

