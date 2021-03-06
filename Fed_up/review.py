""" Review lib for Fed_up Project """

import os
import numpy as np
import pandas as pd

from Fed_up import recipe


LIST_COLS = {}


def get_raw_data():
    """ Reading interaction data from CSV and evaluating list cols """
    print('Reading interaction data from CSV and evaluating list cols...')

    converters = {col: eval for col in LIST_COLS}
    csv_path = os.path.join(os.path.dirname(__file__), "data/raw")
    raw_df = pd.read_csv(f'{csv_path}/RAW_interactions.csv', converters=converters)
    return raw_df


def select_universe(df, recipe_df=None):
    """ Selecting relevant universe of reviews """
    print('Selecting relevant universe of reviews...')

    # Only keeping positive ratings
    df = df[df['rating'] > 0]

    # Removing reviews of excluded recipes
    if recipe_df is not None and isinstance(recipe_df, pd.DataFrame):
        recipe_ids = set(recipe_df['recipe_id'])
        df = df[df['recipe_id'].isin(recipe_ids)]

    # Removing recipes with unique user reviews
    count_df = df.groupby(by="user_id").count()
    count_df = count_df[count_df.rating < 2].reset_index()
    users_to_remove = set(count_df.user_id)
    df = df[~df.user_id.isin(users_to_remove)]

    return df.dropna()


def clean_data(df):
    """ Cleaning and converting data for reviews """
    print('Cleaning and converting data for reviews...')

    # Converting date columns
    df['date'] = pd.to_datetime(df['date'])

    # Creating liked column
    df['liked'] = df['rating'].map(lambda r: 1 if r >= 4 else 0).astype(int)

    # Reorganizing column position (note: nutrition list column is dropped)
    ordered_cols = ['recipe_id', 'user_id', 'rating', 'liked', 'review', 'date']

    target_df = pd.DataFrame(df, columns=ordered_cols)
    return target_df


def get_data(recipe_df=None):
    """ Initial cleaning of review data """
    print('\n*** Initial cleaning of review data ***')

    return clean_data(select_universe(get_raw_data(), recipe_df))


if __name__ == "__main__":
    recipe_df = recipe.get_data()
    data = get_data(recipe_df)

    print("")
    print("********************")
    print('Rows:', data.shape[0])
    print('Cols:', data.shape[1])
    print("")
    print(data.info())
