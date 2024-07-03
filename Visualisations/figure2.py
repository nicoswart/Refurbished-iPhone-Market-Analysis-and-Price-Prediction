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
    'iPhone Xs': 'iphone_X_2024-',
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

# Debugging step: Check columns of the dataframe
print("Columns in data:", data.columns)

# Identify the correct price column name
price_column_name = 'listing_price' if 'listing_price' in data.columns else 'price'

# Check for NaN values in the price column
data = data.dropna(subset=[price_column_name])

# Filter for specific models
models = [
    'iPhone 8', 'iPhone 8 Plus', 'iPhone X', 'iPhone Xs', 'iPhone Xs Max',
    'iPhone 11', 'iPhone 11 Pro', 'iPhone 11 Pro Max',
    'iPhone 12', 'iPhone 12 Pro', 'iPhone 12 Mini', 'iPhone 12 Pro Max',
    'iPhone 13', 'iPhone 13 Pro', 'iPhone 13 Mini', 'iPhone 13 Pro Max',
    'iPhone 14', 'iPhone 14 Plus', 'iPhone 14 Pro', 'iPhone 14 Pro Max',
    'iPhone 15', 'iPhone 15 Plus', 'iPhone 15 Pro', 'iPhone 15 Pro Max'
]

# Initialize variables for storing results
results = {}
std_devs_by_days = {}

# Rollback days range
rollback_days_range = range(1, 15)

# For storing std devs for moving window 1 and 7 days
std_devs_window_1 = {}
std_devs_window_7 = {}

for rollback_days in rollback_days_range:
    std_devs = []
    for model in models:
        model_data = data[data['Model'].str.contains(model, case=False, na=False)]
        model_data = model_data.sort_values('Date')
        rolled_prices = []

        # Get unique dates sorted
        unique_dates = model_data['Date'].drop_duplicates().sort_values()

        rolled_data = calculate_rolled_prices(model_data, unique_dates, rollback_days)
        results[model] = rolled_data

        if not rolled_data.empty:
            std_dev = rolled_data['Rolled Price'].std()
            std_devs.append(std_dev)
            if rollback_days == 1:
                std_devs_window_1[model] = std_dev
            if rollback_days == 7:
                std_devs_window_7[model] = std_dev
    std_devs_by_days[rollback_days] = std_devs

# Create a DataFrame for the boxplot
std_devs_df = pd.DataFrame(std_devs_by_days)

plt.rcParams.update({
    'font.size': 12,          # Base font size
    'axes.titlesize': 20,     # Title font size
    'axes.labelsize': 14,     # Axes labels font size
    'xtick.labelsize': 12,    # X-axis tick labels font size
    'ytick.labelsize': 12,    # Y-axis tick labels font size
    'legend.fontsize': 12,    # Legend font size
    'figure.titlesize': 20    # Figure title font size
})

# Plotting the boxplots of standard deviations for different rollback days
plt.figure(figsize=(14, 7))
box = plt.boxplot(std_devs_df, patch_artist=True)
plt.xlabel('Window Size in Days')
plt.ylabel('Standard Deviation (€)')
plt.title('Boxplots of Standard Deviations for Different Window Sizes')
plt.grid(True)
plt.tight_layout()

# Set the facecolor of the boxes to green
for patch in box['boxes']:
    patch.set_facecolor('green')

# Set the color of the median line to light green
for median in box['medians']:
    median.set_color('#CCFFCC')

plt.show()

# Save standard deviations for window size 1 and 7 to an Excel file
std_devs_window_1_df = pd.DataFrame.from_dict(std_devs_window_1, orient='index', columns=['Std Dev Window 1'])
std_devs_window_7_df = pd.DataFrame.from_dict(std_devs_window_7, orient='index', columns=['Std Dev Window 7'])
std_devs_combined_df = pd.concat([std_devs_window_1_df, std_devs_window_7_df], axis=1)

# Save to Excel file
output_file = 'std_devs_window_1_and_7.xlsx'
std_devs_combined_df.to_excel(output_file)

print(f'Standard deviations for window sizes 1 and 7 days saved to {output_file}')
