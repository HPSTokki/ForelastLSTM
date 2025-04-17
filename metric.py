import pandas as pd

def convert_weather_units(input_csv, output_csv):
    """
    Convert weather data columns from imperial to metric without renaming columns
    """
    # Read CSV with datetime parsing
    df = pd.read_csv(input_csv, parse_dates=['datetime'])
    
    # Temperature conversions (°F → °C)
    temp_cols = ['tempmax', 'tempmin', 'temp']
    for col in temp_cols:
        if col in df.columns:
            df[col] = (df[col] - 32) * 5/9
    
    # Precipitation (inches → mm)
    if 'precip' in df.columns:
        df['precip'] = df['precip'] * 25.4
    
    # Wind speed (mph → km/h)
    if 'windspeed' in df.columns:
        df['windspeed'] = df['windspeed'] * 1.60934
    
    # Save with original column names
    df.to_csv(output_csv, index=False)
    print(f"Converted data saved to {output_csv}")
    print("First 3 rows after conversion:")
    print(df.head(3))

# Example usage
if __name__ == "__main__":
    convert_weather_units(
        input_csv="data.csv",
        output_csv="weather_data_metric.csv"
    )