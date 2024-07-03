import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error
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

output_directory = r'C:\Users\nicop\Desktop\Thesis\Fotos'

def save_plot(fig, filename):
    fig.savefig(f'{output_directory}\\{filename}', bbox_inches='tight')
    plt.close(fig)

def main():
    # Load and clean the data
    combined_data = get_combined_clean_data(directory, model_prefixes)
    
    # Ensure consistent casing for model names
    combined_data['Model'] = combined_data['Model'].str.replace('mini', 'Mini', case=False)
    combined_data['Model'] = combined_data['Model'].str.replace('xr', 'Xr', case=False)
    
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
    all_residuals = []

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

        mean_actual = test.mean()
        sMAE = best_mae / mean_actual

        print(f'Best ARIMA order for {column}: {best_order} with MAE: {best_mae} and sMAE: {sMAE}')

        # Store results
        results.append({
            'Model': column,
            'Best Order': best_order,
            'MAE': best_mae,
            'sMAE': sMAE
        })

        # Store residuals with the correct dates
        residuals = pd.Series(test.values - predictions, index=test.index)
        all_residuals.append(residuals)

        # Plotting for iPhone 12 and iPhone Xs Max
        if column in ['iPhone 12', 'iPhone Xs']:
            fig, ax = plt.subplots(figsize=(14, 7))
            ax.plot(test.index, test, label='Actual')
            ax.plot(test.index, predictions, label='Predicted', linestyle='--')
            ax.set_title(f'ARIMA Model Rolling Forecast for {column}')
            ax.set_xlabel('Date')
            ax.set_ylabel('Listing Price (€)')
            ax.legend()
            ax.grid(True)
            save_plot(fig, f'{column}_forecast.png')

            fig, ax = plt.subplots(figsize=(14, 7))
            residuals.plot(ax=ax)
            ax.set_title(f'Residuals for {column}')
            ax.set_xlabel('Date')
            ax.set_ylabel('Residuals')
            save_plot(fig, f'{column}_residuals.png')

            fig, ax = plt.subplots(figsize=(14, 7))
            residuals.plot(kind='kde', ax=ax)
            ax.set_title(f'Residual Density for {column}')
            ax.set_xlabel('Residuals')
            save_plot(fig, f'{column}_residual_density.png')

    # Combine residuals from all models
    combined_residuals = pd.concat(all_residuals, axis=1)
    mean_residuals = combined_residuals.mean(axis=1)

    # Remove NaN values
    mean_residuals = mean_residuals.dropna()

    # Set font sizes for the plot
    plt.rcParams.update({
        'font.size': 12,          # Base font size
        'axes.titlesize': 20,     # Title font size
        'axes.labelsize': 14,     # Axes labels font size
        'xtick.labelsize': 12,    # X-axis tick labels font size
        'ytick.labelsize': 12,    # Y-axis tick labels font size
        'legend.fontsize': 12,    # Legend font size
        'figure.titlesize': 20    # Figure title font size
    })

    # Plot mean residuals
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(mean_residuals.index, mean_residuals)
    ax.set_title('Mean Residuals for All iPhone Models')
    ax.set_xlabel('Date')
    ax.set_ylabel('Residuals')
    ax.grid(True)
    save_plot(fig, 'combined_mean_residuals.png')

    # Plot density of mean residuals
    fig, ax = plt.subplots(figsize=(14, 7))
    mean_residuals.plot(kind='kde', ax=ax)
    ax.set_title('Residual Density for All iPhone Models')
    ax.set_xlabel('Residuals')
    save_plot(fig, 'combined_mean_residual_density.png')

if __name__ == "__main__":
    main()
