""" Recipe lib for Fed_up Project """

import os
import numpy as np
import pandas as pd
import ipdb
import regex as re
import warnings
import datetime

from Fed_up import review


NUTRITION_COLS = ['calories', 'total_fat', 'sugar', 'sodium',
                  'protein', 'saturated_fat', 'carbohydrates']

LIST_COLS = ['tags', 'nutrition', 'steps', 'ingredients']


def get_raw_data(folder="data/raw", filename="RAW_recipes.csv"):
    """ Reading recipe data from CSV and evaluating list cols """
    print('Reading recipe data from CSV and evaluating list cols...')

    converters = {col: eval for col in LIST_COLS}
    csv_path = os.path.join(os.path.dirname(__file__), folder)
    raw_df = pd.read_csv(f'{csv_path}/{filename}', converters=converters)
    return raw_df


def select_universe(df):
    """ Selecting relevant universe of recipes """
    print('Selecting relevant universe of recipes...')

    # Load recipes and reviews and merge both tables and grouping them; drop NaN
    print('> Loading review data for universe selection...')
    df.rename(columns={"id": "recipe_id"}, inplace=True)
    csv_path = os.path.join(os.path.dirname(__file__), "data/raw")
    reviews_df = pd.read_csv(f'{csv_path}/RAW_interactions.csv')
    merged_df = df.merge(reviews_df, on="recipe_id", how="inner")
    agg_df = merged_df.groupby(by="recipe_id").agg({"rating": ["mean", "count"]}).xs('rating', axis=1, drop_level=True)
    review_merge_df = df.merge(agg_df, on="recipe_id", how="inner").dropna()

    # Listing very specific ingredients
    print("> Creating lists for filtering...")
    ingredients = review_merge_df["ingredients"]

    ingredients_dict = {}
    for i in ingredients:
        for j in i:
            if j not in ingredients_dict.keys():
                ingredients_dict[j] = 1
            else:
                ingredients_dict[j] += 1

    # Recipes containing too specific ingredients will be removed
    low_use_ingredients = [i for i, count in ingredients_dict.items() if count < 2]
    # print(f"> Removing rows with too specific ingredients now ({len(low_use_ingredients)})...")
    # review_merge_df = __remove_list_from_df(review_merge_df, low_use_ingredients, "ingredients")

    # Removing drinks and icecream recipes using tags
    drink_tags = ["cocktails", "punch", "non-alcoholic", "ice-cream", "brewing", "beverages", "smoothies"]
    print(f"> Removing rows with drinks tags now ({len(drink_tags)})...")
    review_merge_df = __remove_list_from_df(review_merge_df, drink_tags, "tags")

    # Removing outliers by cooking time and number of ingredients
    print("> Removing rows with outliers from dataframe now...")
    review_merge_df = review_merge_df[(review_merge_df.minutes <= 300) & (review_merge_df.n_ingredients <= 20)]

    return review_merge_df


def __remove_list_from_df(df, tag_list, column):
    """ Removing row from a dataframe that contain items from a specific tag list """
    data = df.copy()
    data['str'] = data[column].map(lambda x: (' ').join(x))

    # for tag in tag_list:
    warnings.filterwarnings("ignore", 'This pattern has match groups')
    j_tag_list = ('|').join(tag_list)
    data = data[~data['str'].str.contains(j_tag_list, flags=re.IGNORECASE, regex=True)]

    data.drop(columns='str', inplace=True)
    return data


def clean_data(df):
    """ Cleaning and converting data for recipes """
    print('Cleaning and converting data for recipes...')

    # Generating nutrition columns
    df[NUTRITION_COLS] = __clean_nutrition(df)

    # Stringifying list columns
    for col in LIST_COLS:
        if col != 'nutrition':
            df[f"{col}_str"] = df[col].map(lambda x: (', ').join(x))

    # Converting date columns
    df['submitted'] = pd.to_datetime(df['submitted'])

    # Creating metadata column
    df['metadata'] = df['name'] + " " + df['tags_str'] + " " + df['ingredients_str'] # + " " + df['steps_str'] + " " + df['description_str']

    # Renaming contributor_id to user_id for coherence
    df.rename(columns = {'contributor_id': 'user_id', 'mean': 'rating_mean', 'count': 'rating_count'}, inplace = True)

    # Reorganizing column position (note: nutrition list column is dropped)
    ordered_cols = ['recipe_id', 'user_id', 'name', 'rating_mean', 'rating_count', 'minutes', 'n_steps',
                    'n_ingredients', 'calories', 'total_fat', 'sugar', 'sodium', 'protein', 'saturated_fat',
                    'carbohydrates', 'tags', 'ingredients', 'steps', 'description', 'metadata', 'submitted']

    target_df = pd.DataFrame(df, columns=ordered_cols)
    return target_df


def __clean_nutrition(df, col='nutrition'):
    """ Creating nutrition columns from list """
    print('Creating nutrition columns from list...')

    numpy_col = np.array(df[col].to_list())

    for index, nut_col in enumerate(NUTRITION_COLS):
        df[nut_col] = numpy_col[:, index].astype(float)

    return df[NUTRITION_COLS]


def get_data():
    """ Initial cleaning of recipe data """
    print('\n*** Initial cleaning of recipe data ***')

    return clean_data(select_universe(get_raw_data()))


def generate_sample_data(folder="data/samples", size=2000):
    """ Automatically generating samples for recipes and reviews """
    csv_path = os.path.join(os.path.dirname(__file__), folder)
    recipes = get_data()
    recipes_sample = recipes.sample(size)
    reviews_sample = review.get_data(recipes_sample)
    timestamp = '{:%Y%m%d_%H%M}'.format(datetime.datetime.now())
    recipes_sample.to_csv(f'{csv_path}/recipe_sample_{timestamp}.csv', index=False)
    reviews_sample.to_csv(f'{csv_path}/review_sample_{timestamp}.csv', index=False)


if __name__ == "__main__":
    data = get_data()
    generate_sample_data()

    print("")
    print("********************")
    print('Rows:', data.shape[0])
    print('Cols:', data.shape[1])
    print("")
    print(data.info())