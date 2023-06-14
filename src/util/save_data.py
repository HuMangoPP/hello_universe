import numpy as np
import pandas as pd
import os, json

def write_entity_data_as_csv(generation: int, data: dict, csv_file: str) -> pd.DataFrame:
    fpath = f'./assets/data/{csv_file}.csv'
    if os.path.isfile(fpath) and os.path.getsize(fpath) > 0:
        old_df = pd.read_csv(fpath)
    else:
        old_df = pd.DataFrame()
    data = {
        key: np.array([value])
        for key, value in data.items()
    }
    df = pd.DataFrame.from_dict(data)
    df['gen'] = np.array([generation], dtype=np.int32)
    df = pd.concat([old_df, df])
    df.to_csv(fpath, index=False)
    return df

def write_entity_data_as_json(generation: int, data: dict, json_file: str) -> dict:
    fpath = f'./assets/data/{json_file}.json'
    with open(fpath, 'w+') as f:
        json_data = json.load(f)
        gen_key = f'gen_{generation}'
        if gen_key in json_data:
            json_data[gen_key].append(data)
        else:
            json_data[gen_key] = [data]
        json.dump(json_data, f)

