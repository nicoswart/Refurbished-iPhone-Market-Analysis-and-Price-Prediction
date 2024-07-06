import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import timedelta
from dataclean import get_combined_clean_data
import numpy as np
import matplotlib.dates as mdates

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

# Set a specific value for rollback days
rollback_days = 7

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
results = []
ratios = []

for model in models:
    model_data = data[data['Model'].str.contains(model, case=False, na=False)]
    model_data = model_data.sort_values('Date')
    rolled_prices = []

    # Get unique dates sorted
    unique_dates = model_data['Date'].drop_duplicates().sort_values()

    rolled_data = calculate_rolled_prices(model_data, unique_dates, rollback_days)
    results.append(rolled_data)

    if not rolled_data.empty:
        first_price = rolled_data['Rolled Price'].iloc[0]
        last_price = rolled_data['Rolled Price'].iloc[-1]
        difference = last_price - first_price
        ratio = round(last_price / first_price, 3) if first_price != 0 else np.nan
        std_dev = rolled_data['Rolled Price'].std()
        
        ratios.append({
            'Model': model, 
            'First Price': first_price, 
            'Last Price': last_price, 
            'Difference': difference, 
            'Ratio': ratio,
            'Standard Deviation': std_dev
        })

# Create a DataFrame for the results
ratios_df = pd.DataFrame(ratios)

# Calculate averages before rounding
averages = ratios_df.mean(numeric_only=True)
averages['Model'] = 'Average'

# Create a new DataFrame for the averages with proper rounding
averages_rounded = {
    'Model': 'Average',
    'First Price': round(averages['First Price'], 2),
    'Last Price': round(averages['Last Price'], 2),
    'Difference': round(averages['Difference'], 2),
    'Ratio': round(averages['Ratio'], 3),
    'Standard Deviation': round(averages['Standard Deviation'], 2)
}

# Add the averages to the DataFrame
ratios_df = pd.concat([ratios_df, pd.DataFrame([averages_rounded])], ignore_index=True)

# Print the DataFrame with the ratios and standard deviations
print(ratios_df)

# Save the results to an Excel file
output_path = r'C:\Users\nicop\Desktop\Thesis\iphone_price_analysis.xlsx'
ratios_df.to_excel(output_path, index=False)
