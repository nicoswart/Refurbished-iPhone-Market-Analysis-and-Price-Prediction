import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error, mean_squared_error
from dataclean import get_combined_clean_data

# Set the directory and model prefixes
directory = r'C:\Users\nicop\anaconda3\Scraping\mpscraper\ScrapeFiles'
model_prefixes = {
    'iPhone 8': ['iphone_8_2024-'],
    'iPhone X': ['iphone_X'],  # This will catch iPhone X, Xs, and Xr
    'iPhone 11': ['iphone_11_2024-'],
    'iPhone 12': ['iphone_12_2024-'],
    'iPhone 13': ['iphone_13_2024-'],
    'iPhone 14': ['iphone_14_2024-'],
    'iPhone 15': ['iphone_15_2024-']
}

def main():
    # Load and clean the data
    combined_data = get_combined_clean_data(directory, model_prefixes)
    
    # Ensure consistent casing for model names
    combined_data['Model'] = combined_data['Model'].str.replace('mini', 'Mini', case=False)
    combined_data['Model'] = combined_data['Model'].str.replace('xr', 'Xr', case=False)
    
    # Debugging step: print the first few rows of the data
    print("Combined Data (First few rows):")
    print(combined_data.head())
    
    # Ensure 'date' is the index and properly sorted
    combined_data['date'] = pd.to_datetime(combined_data['date'])
    combined_data.sort_values(by='date', inplace=True)
    
    # Group by date and model, then take the mean to remove duplicates
    numeric_data = combined_data.groupby(['date', 'Model']).agg({'listing_price': 'mean'}).reset_index()
    
    # Pivot the data to have models as columns
    df_pivot = numeric_data.pivot(index='date', columns='Model', values='listing_price')
    df_pivot = df_pivot.asfreq('D')  # Ensure the date index has a daily frequency
    df_pivot.fillna(method='ffill', inplace=True)  # Forward fill missing values
    
    # Debugging step: print the first few rows of the pivot table
    print("Pivot Table (First few rows):")
    print(df_pivot.head())
    
    # Check the number of observations
    print(f"Number of observations: {len(df_pivot)}")
    
    # Prepare the results storage
    results = []

    # Rolling forecast evaluation for each model
    for column in df_pivot.columns:
        train_size = int(len(df_pivot[column]) * 0.6)
        train, test = df_pivot[column].iloc[:train_size], df_pivot[column].iloc[train_size:]

        best_mae = float('inf')
        best_order = None
        best_model = None

        # Grid search for ARIMA parameters
        for p in range(1, 3):
            for d in range(1, 3):
                for q in range(7, 10):
                    try:
                        model = ARIMA(train, order=(p, d, q))
                        model_fit = model.fit()
                        predictions = model_fit.forecast(steps=len(test))
                        mae = mean_absolute_error(test, predictions)
                        if mae < best_mae:
                            best_mae = mae
                            best_order = (p, d, q)
                            best_model = model_fit
                    except:
                        continue

        # Calculate the range of actual values
        actual_range = test.max() - test.min()
        
        # Calculate the standardized MAE
        standardized_mae = best_mae / actual_range
        
        print(f'Best ARIMA order for {column}: {best_order} with MAE: {best_mae} and Standardized MAE: {standardized_mae}')

        # Store results
        results.append({
            'Model': column,
            'Best Order': best_order,
            'MAE': best_mae,
            'Standardized MAE': standardized_mae
        })

    # Print the results in a table format
    results_df = pd.DataFrame(results)
    print(results_df)

if __name__ == "__main__":
    main()
