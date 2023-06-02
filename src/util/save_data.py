import numpy as np
import pandas as pd

def entity_data_to_df(generation: int, num_entities: int, data: dict, old_data: str) -> pd.DataFrame:
    old_df = pd.read_csv(f'./assets/data/{old_data}.csv')
    df = pd.DataFrame.from_dict(data)
    df['generation'] = np.full((num_entities, ), generation, dtype=np.int32)
    df = pd.concat([old_df, df])
    df.to_csv(f'./assets/data/{old_data}.csv', index=False)
    return df

