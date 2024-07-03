import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import timedelta
from dataclean import get_combined_clean_data
import matplotlib.dates as mdates

# Set the directory and rollback days
directory = r'C:\Users\nicop\anaconda3\Scraping\mpscraper\ScrapeFiles'
rollback_days = 1

# Define model prefixes for iPhone 12 models
model_prefixes = {
    'iPhone 12': 'iphone_12_2024-',
    'iPhone 12 Pro': 'iphone_12_2024-',
    'iPhone 12 Mini': 'iphone_12_2024-',
    'iPhone 12 Pro Max': 'iphone_12_2024-'
}

def load_data(directory, model_prefixes):
    combined_data = get_combined_clean_data(directory, model_prefixes)
    combined_data.rename(columns={'date': 'Date'}, inplace=True)
    return combined_data

# Load and prepare data
data = load_data(directory, model_prefixes)
data = data.dropna(subset=['listing_price'])

# Filter for specific models
models = ['iPhone 12', 'iPhone 12 Pro', 'iPhone 12 Mini', 'iPhone 12 Pro Max']
results = {}
colors = ['blue', 'green', 'red', 'cyan']

for model, color in zip(models, colors):
    model_data = data[data['Model'].str.contains(model, case=False, na=False)]
    model_data = model_data.sort_values('Date')

    rolled_prices = []

    # Get unique dates sorted
    unique_dates = model_data['Date'].drop_duplicates().sort_values()

    for current_date in unique_dates:
        count = 0
        date_list = []
        temp_date = current_date

        # Collect enough dates
        while count < rollback_days and temp_date >= unique_dates.min():
            if temp_date in unique_dates.values:
                date_list.append(temp_date)
                count += 1
            temp_date -= timedelta(days=1)

        # Only add data if we have complete data for the specified rollback period
        if len(date_list) == rollback_days:
            relevant_data = model_data[model_data['Date'].isin(date_list)]
            if not relevant_data.empty:
                avg_price = relevant_data['listing_price'].mean()
                rolled_prices.append({'Date': current_date, 'Rolled Price': avg_price})

    results[model] = pd.DataFrame(rolled_prices)

# Set font sizes for the plot
plt.rcParams.update({
    'font.size': 12,
    'axes.titlesize': 20,
    'axes.labelsize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.titlesize': 20
})

# Plotting the results
plt.figure(figsize=(14, 7))
for model, color in zip(models, colors):
    df = results[model]
    if not df.empty:
        plt.plot(df['Date'], df['Rolled Price'], label=model, color=color)

plt.title('Daily Average Prices of iPhone 12 Models Over Time')
plt.xlabel('Date')
plt.ylabel('Average Price (€)')
plt.legend(loc='lower left')
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
