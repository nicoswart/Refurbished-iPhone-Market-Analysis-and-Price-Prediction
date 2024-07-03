import pandas as pd
import os

def load_and_combine_csv(directory, prefixes):
    data_frames = []
    for prefix in prefixes:
        for filename in os.listdir(directory):
            if filename.startswith(prefix) and filename.endswith('.csv'):
                file_path = os.path.join(directory, filename)
                df = pd.read_csv(file_path)
                df.rename(columns={'Date': 'date', 'Price': 'listing_price'}, inplace=True)
                # Ensure listing_price is treated as string regardless of its content
                df['listing_price'] = df['listing_price'].astype(str).str.replace('€', '').str.replace(',', '.').astype(float)
                df['date'] = pd.to_datetime(df['date'], errors='coerce')  # Ensure date is in datetime format
                data_frames.append(df)
    if data_frames:
        combined_data = pd.concat(data_frames, ignore_index=True)
        return combined_data
    else:
        return pd.DataFrame()  # Return an empty DataFrame if no files were found

def remove_outliers(df, column='listing_price', min_listings=10):
    if df.empty or column not in df.columns:
        return df, 0
    
    initial_count = len(df)
    
    def filter_outliers(group):
        Q1 = group[column].quantile(0.25)
        Q3 = group[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return group[(group[column] >= lower_bound) & (group[column] <= upper_bound)]
    
    # Group by 'Model' and apply the outlier filter
    grouped = df.groupby(['Model'], group_keys=False)
    
    # Filter out groups with fewer than min_listings
    valid_groups = grouped.filter(lambda x: len(x) >= min_listings)
    
    filtered = valid_groups.groupby('Model', group_keys=False).apply(filter_outliers)
    
    final_count = len(filtered)
    removed_count = initial_count - final_count
    
    return filtered.reset_index(drop=True), removed_count

def get_combined_clean_data(directory, series_prefixes, min_listings=0):
    combined_data = {series: load_and_combine_csv(directory, prefixes) for series, prefixes in series_prefixes.items()}
    clean_data = {}
    total_removed = 0
    
    for series in combined_data:
        if not combined_data[series].empty:
            cleaned_df, removed_count = remove_outliers(combined_data[series], min_listings=min_listings)
            clean_data[series] = cleaned_df
            total_removed += removed_count
        else:
            clean_data[series] = pd.DataFrame()
    
    all_data = pd.concat([df.assign(Series=series) for series, df in clean_data.items()], ignore_index=True)
    
    print(f"Total listings removed by the outlier step: {total_removed}")
    
    return all_data

