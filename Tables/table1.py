import pandas as pd
import os
from dataclean import get_combined_clean_data

# Set the directory and model prefixes
directory = r'C:\Users\nicop\anaconda3\Scraping\mpscraper\ScrapeFiles'
model_prefixes = {
    'iPhone 8': ['iphone_8_2024-'],
    'iPhone X/Xs/Xr': ['iphone_X_2024-', 'iphone_Xs_2024-', 'iphone_Xr_2024-'],
    'iPhone 11': ['iphone_11_2024-'],
    'iPhone 12': ['iphone_12_2024-'],
    'iPhone 13': ['iphone_13_2024-'],
    'iPhone 14': ['iphone_14_2024-'],
    'iPhone 15': ['iphone_15_2024-']
}

def generate_descriptive_stats(data):
    descriptives = data.groupby('Series')['listing_price'].describe()
    descriptives['cv'] = descriptives['std'] / descriptives['mean']  # Coefficient of variation
    
    # Apply formatting
    descriptives['count'] = descriptives['count'].round(0).astype(int)
    descriptives['mean'] = descriptives['mean'].round(2)
    descriptives['std'] = descriptives['std'].round(3)
    descriptives['min'] = descriptives['min'].round(0).astype(int)
    descriptives['25%'] = descriptives['25%'].round(0).astype(int)
    descriptives['50%'] = descriptives['50%'].round(0).astype(int)
    descriptives['75%'] = descriptives['75%'].round(0).astype(int)
    descriptives['max'] = descriptives['max'].round(0).astype(int)
    descriptives['cv'] = descriptives['cv'].round(3)
    
    return descriptives

def main():
    combined_data = get_combined_clean_data(directory, model_prefixes)
    descriptives = generate_descriptive_stats(combined_data)
    print(descriptives)

if __name__ == "__main__":
    main()
