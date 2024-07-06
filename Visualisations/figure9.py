import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from dataclean import get_combined_clean_data

# Set the directory and model prefixes
directory = r'C:\Users\nicop\anaconda3\Scraping\mpscraper\ScrapeFiles'
model_prefixes = {
    'iPhone 12': ['iphone_12_2024-']
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
    df_pivot.ffill(inplace=True)  # Forward fill missing values
    
    # Debugging step: print the first few rows of the pivot table
    print("Pivot Table (First few rows):")
    print(df_pivot.head())
    
    # Check the number of observations
    print(f"Number of observations: {len(df_pivot)}")
    
    # Filter data for the iPhone 12 model
    model_data = df_pivot['iPhone 12']
    
    # Ensure there are enough observations
    if len(model_data) < 15:
        print("Not enough observations to fit the ARIMA model reliably.")
        return

    # Fit ARIMA model with parameters (1, 1, 7)
    model = ARIMA(model_data, order=(1, 1, 7))
    model_fit = model.fit()
    
    # Forecast for the next 2 months (approximately 60 days)
    forecast_steps = 60
    forecast = model_fit.forecast(steps=forecast_steps)
    
    # Generate dates for the forecast
    last_date = model_data.index[-1]
    forecast_dates = pd.date_range(start=last_date, periods=forecast_steps + 1, freq='D')[1:]

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

    # Plot the actual data and the forecast from June 15th onwards
    start_date = '2024-06-15'
    plt.figure(figsize=(14, 7))
    plt.plot(model_data.loc[start_date:].index, model_data.loc[start_date:], label='Actual')
    plt.plot(forecast_dates, forecast, label='Forecast', linestyle='--', color='red')
    plt.title('ARIMA(1, 1, 7) Forecast for iPhone 12 - Next 2 Months')
    plt.xlabel('Date')
    plt.ylabel('Listing Price (€)')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
