import pandas as pd

def handle_outliers_iqr(dataframe, columns):
    """
    Caps the upper-bound outliers of specified columns using the IQR method.
    We don't cap the lower bound here because years and income cannot be negative.
    """
    df_clean = dataframe.copy()
    
    for col in columns:
        Q1 = df_clean[col].quantile(0.25)
        Q3 = df_clean[col].quantile(0.75)
        IQR = Q3 - Q1
        
        # Define limits (Standard threshold is 1.5 * IQR)
        upper_limit = Q3 + 1.5 * IQR
        
        # Cap values above the upper limit
        df_clean[col] = df_clean[col].apply(lambda x: int(upper_limit) if x > upper_limit else x)
        
    return df_clean

def clean_data(data: pd.DataFrame):

    cleaned_data = data
    
    # convert to snake_case
    cleaned_data.columns = cleaned_data.columns.str.strip().str.lower().str.replace(
                                                                        r"[ -]", '_', regex=True)
    
    # handle outliers
    cleaned_data = handle_outliers_iqr(cleaned_data, ['years_at_company', 'monthly_income'])

    # drop all rows that violates the years_at_company and age
    cleaned_data = cleaned_data[cleaned_data['years_at_company'] <= cleaned_data['age'] - 18].reset_index(drop=True)

    # drop all rows that violates the education level and age
    education_levels = ['Associate Degree', 'Master’s Degree', 'Bachelor’s Degree', 'High School',
    'PhD']
    eligible_ages = ['22', '24', '22', '18', '30']

    masks = []

    for i in range(len(education_levels)):
        masks.append((cleaned_data['education_level'] == education_levels[i])
                & (cleaned_data['age'] < int(eligible_ages[i])))
    
    general_mask = masks[0]
    for i in range(1, len(masks)):
        general_mask = general_mask | masks[i]

    cleaned_data = cleaned_data[~general_mask].reset_index(drop=True)

    return cleaned_data