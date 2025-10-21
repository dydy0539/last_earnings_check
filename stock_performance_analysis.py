import pandas as pd
import numpy as np

# Define the dates and their corresponding close prices and NEXT day's close prices
# Data extracted from nflx_historical_data.csv
data = {
    'Date': [
        'April 17, 2025',
        'January 21, 2025', 
        'October 17, 2024',
        'July 18, 2024',
        'April 18, 2024',
        'January 23, 2024',
        'October 18, 2023',
        'July 19, 2023'
    ],
    'Close_Price': [
        973.03,  # Apr 17, 2025
        869.68,  # Jan 21, 2025
        687.65,  # Oct 17, 2024
        643.04,  # Jul 18, 2024
        610.56,  # Apr 18, 2024
        492.19,  # Jan 23, 2024
        346.19,  # Oct 18, 2023
        477.59   # Jul 19, 2023
    ],
    'Next_Day_Close': [
        987.91,  # Apr 21, 2025 (next trading day after Apr 17)
        953.99,  # Jan 22, 2025 (next trading day after Jan 21)
        763.89,  # Oct 18, 2024 (next trading day after Oct 17)
        633.34,  # Jul 19, 2024 (next trading day after Jul 18)
        555.04,  # Apr 19, 2024 (next trading day after Apr 18)
        544.87,  # Jan 24, 2024 (next trading day after Jan 23)
        401.77,  # Oct 19, 2023 (next trading day after Oct 18)
        437.42   # Jul 20, 2023 (next trading day after Jul 19)
    ]
}

# Create DataFrame
df = pd.DataFrame(data)

# Calculate price change and percentage change
df['Price_Change'] = df['Next_Day_Close'] - df['Close_Price']
df['Percentage_Change'] = (df['Price_Change'] / df['Close_Price']) * 100

# Format the results for display
df['Close_Price_Formatted'] = df['Close_Price'].apply(lambda x: f"${x:,.2f}")
df['Next_Day_Formatted'] = df['Next_Day_Close'].apply(lambda x: f"${x:,.2f}")
df['Price_Change_Formatted'] = df['Price_Change'].apply(lambda x: f"${x:+,.2f}")
df['Percentage_Change_Formatted'] = df['Percentage_Change'].apply(lambda x: f"{x:+.2f}%")

# Display results in tabular format
print("Netflix Stock Performance Analysis - Next Day Comparison")
print("=" * 85)
print(f"{'Date':<20} {'Close Price':<15} {'Next Day Close':<18} {'Price Change':<15} {'% Change':<12}")
print("-" * 85)

for _, row in df.iterrows():
    print(f"{row['Date']:<20} {row['Close_Price_Formatted']:<15} {row['Next_Day_Formatted']:<18} "
          f"{row['Price_Change_Formatted']:<15} {row['Percentage_Change_Formatted']:<12}")

print("-" * 85)

# Summary statistics
print("\nSummary Statistics:")
print(f"Average next-day change: {df['Percentage_Change'].mean():.2f}%")
print(f"Largest next-day gain: {df['Percentage_Change'].max():.2f}% on {df.loc[df['Percentage_Change'].idxmax(), 'Date']}")
print(f"Largest next-day loss: {df['Percentage_Change'].min():.2f}% on {df.loc[df['Percentage_Change'].idxmin(), 'Date']}")
print(f"Number of positive next-day moves: {(df['Percentage_Change'] > 0).sum()}")
print(f"Number of negative next-day moves: {(df['Percentage_Change'] < 0).sum()}") 