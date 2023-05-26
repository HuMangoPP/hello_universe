import numpy as np
import pandas as pd

def entity_data_to_df(generation: int, num_entities: int, entity_data: dict) -> pd.DataFrame:
    old_df = pd.read_csv('./assets/data/save.csv')
    df = pd.DataFrame.from_dict(entity_data)
    df['generation'] = np.full((num_entities, ), generation, dtype=np.int32)
    df = pd.concat([old_df, df])
    df.to_csv('./assets/data/save.csv', index=False)
    return df

