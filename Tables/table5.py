import pandas as pd
import os
from datetime import timedelta
from dataclean import get_combined_clean_data
import numpy as np

# Set the directory
directory = r'C:\Users\nicop\anaconda3\Scraping\mpscraper\ScrapeFiles'

# Define model prefixes for all iPhone models
model_prefixes = {
    'iPhone 8': 'iphone_8_2024-',
    'iPhone 8 Plus': 'iphone_8_2024-',
    'iPhone X': 'iphone_X_2024-',
    'iPhone Xr': 'iphone_Xr_2024-',
    'iPhone Xs Max': 'iphone_X_2024-',
    'iPhone 11': 'iphone_11_2024-',
    'iPhone 11 Pro': 'iphone_11_2024-',
    'iPhone 11 Pro Max': 'iphone_11_2024-',
    'iPhone 12': 'iphone_12_2024-',
    'iPhone 12 Pro': 'iphone_12_2024-',
    'iPhone 12 Mini': 'iphone_12_2024-',
    'iPhone 12 Pro Max': 'iphone_12_2024-',
    'iPhone 13': 'iphone_13_2024-',
    'iPhone 13 Pro': 'iphone_13_2024-',
    'iPhone 13 Mini': 'iphone_13_2024-',
    'iPhone 13 Pro Max': 'iphone_13_2024-',
    'iPhone 14': 'iphone_14_2024-',
    'iPhone 14 Plus': 'iphone_14_2024-',
    'iPhone 14 Pro': 'iphone_14_2024-',
    'iPhone 14 Pro Max': 'iphone_14_2024-',
    'iPhone 15': 'iphone_15_2024-',
    'iPhone 15 Plus': 'iphone_15_2024-',
    'iPhone 15 Pro': 'iphone_15_2024-',
    'iPhone 15 Pro Max': 'iphone_15_2024-'
}

def load_data(directory, model_prefixes):
    combined_data = get_combined_clean_data(directory, model_prefixes)
    combined_data.rename(columns={'date': 'Date'}, inplace=True)
    return combined_data

def calculate_rolled_prices(data, unique_dates, rollback_days):
    rolled_prices = []
    for current_date in unique_dates:
        count = 0
        date_list = []
        temp_date = current_date

        while count < rollback_days and temp_date >= unique_dates.min():
            if temp_date in unique_dates.values:
                date_list.append(temp_date)
                count += 1
            temp_date -= timedelta(days=1)

        if len(date_list) == rollback_days:
            relevant_data = data[data['Date'].isin(date_list)]
            if not relevant_data.empty:
                avg_price = relevant_data['listing_price'].mean()
                rolled_prices.append({'Date': current_date, 'Rolled Price': avg_price})

    return pd.DataFrame(rolled_prices)

# Load and prepare data
data = load_data(directory, model_prefixes)
data = data.dropna(subset=['listing_price'])

# Filter for specific models
models = [
    'iPhone 8', 'iPhone 8 Plus', 'iPhone X', 'iPhone Xr', 'iPhone Xs Max',
    'iPhone 11', 'iPhone 11 Pro', 'iPhone 11 Pro Max',
    'iPhone 12', 'iPhone 12 Pro', 'iPhone 12 Mini', 'iPhone 12 Pro Max',
    'iPhone 13', 'iPhone 13 Pro', 'iPhone 13 Mini', 'iPhone 13 Pro Max',
    'iPhone 14', 'iPhone 14 Plus', 'iPhone 14 Pro', 'iPhone 14 Pro Max',
    'iPhone 15', 'iPhone 15 Plus', 'iPhone 15 Pro', 'iPhone 15 Pro Max'
]

# Initialize variables for storing results
results_1_day = {}
results_7_days = {}
std_devs = []

for model in models:
    model_data = data[data['Model'].str.contains(model, case=False, na=False)]
    model_data = model_data.sort_values('Date')
    
    # Get unique dates sorted
    unique_dates = model_data['Date'].drop_duplicates().sort_values()
    
    # Calculate for 1-day window
    rolled_data_1_day = calculate_rolled_prices(model_data, unique_dates, 1)
    results_1_day[model] = rolled_data_1_day
    std_dev_1_day = rolled_data_1_day['Rolled Price'].std() if not rolled_data_1_day.empty else np.nan
    
    # Calculate for 7-day window
    rolled_data_7_days = calculate_rolled_prices(model_data, unique_dates, 7)
    results_7_days[model] = rolled_data_7_days
    std_dev_7_days = rolled_data_7_days['Rolled Price'].std() if not rolled_data_7_days.empty else np.nan
    
    std_devs.append({'Model': model, 'Standard Deviation (1-day)': std_dev_1_day, 'Standard Deviation (7-day)': std_dev_7_days})

# Create a DataFrame for the standard deviations
std_devs_df = pd.DataFrame(std_devs)

# Save the results to an Excel file
output_path = r'C:\Users\nicop\Desktop\Thesis\iphone_standard_deviations.xlsx'
std_devs_df.to_excel(output_path, index=False)

# Print the DataFrame with standard deviations
print(std_devs_df)
