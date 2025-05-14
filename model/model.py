import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib
import os
from dotenv import load_dotenv

load_dotenv()
path = os.getenv('DATA_PATH')
df = pd.read_csv(path)


print(df)
df['date_x'] = pd.to_datetime(df['date_x'])
df = df.sort_values(by=['date_x'])

released_part = df[df['status'] == ' Released']
non_released = df[df['status'] != ' Released']

released_part = released_part.reset_index().drop(columns=['index'])
released_part = released_part.dropna()
LabEncoder = LabelEncoder()



def preprocessing(table, encoder):
    table['genre'] = table['genre'].apply(lambda x: ',\xa0'.join(sorted(x.split(',\xa0'))))
    df_copy = table.drop(columns=['date_x', 'revenue', 'overview', 'crew', 'orig_title', 'names']).copy()
    # genre_enc, country_enc, orig_lang_enc = joblib.load('genre_enc.pkl'), joblib.load(
    #     'country_enc.pkl'), joblib.load('orig_lang_enc.pkl')
    # df_copy['genre'] = genre_enc.fit_transform(df_copy['genre'])
    # df_copy['orig_lang'] = orig_lang_enc.fit_transform(df_copy['orig_lang'])
    # df_copy['country'] = country_enc.fit_transform(df_copy['country'])

    for col in df_copy.columns[df_copy.dtypes == 'object']:
        new_enc = encoder.fit(df_copy[col])
        df_copy[col] = new_enc.transform(df_copy[col])
        joblib.dump(new_enc, f"{col}_enc.pkl")
    prepared_df = df_copy.copy()
    return prepared_df


new_df = preprocessing(released_part, LabEncoder)
X, y = new_df.drop(columns=['score']), new_df['score']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=17)
model = RandomForestRegressor(n_estimators=2000, max_depth=32, min_samples_split=13, min_samples_leaf=25, n_jobs=-1, random_state=17)
model.fit(X_train, y_train)
print(X.columns)
joblib.dump(model, 'model.pkl')
joblib.dump(new_df['score'], 'ratings.pkl')
