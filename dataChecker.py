import os
import pandas as pd
from datetime import datetime

def remove_duplicates_by_datetime(filenames, datetime_col='datetime', keep='last'):
    """
    Remove duplicates from a list of CSV files based on datetime column.
    Returns a dictionary with processing results for each file.
    
    Args:
        filenames (list): List of CSV filenames to process
        datetime_col (str): Name of datetime column
        keep (str): Which duplicate to keep ('first' or 'last')
    
    Returns:
        dict: Processing results for each file
    """
    results = {}
    
    for filename in filenames:
        try:
            # Read CSV file
            df = pd.read_csv(filename)
            
            # Initialize result entry
            file_result = {
                'original_rows': len(df),
                'duplicates_removed': 0,
                'final_rows': 0,
                'status': 'processed'
            }
            
            # Check if datetime column exists
            if datetime_col not in df.columns:
                file_result['status'] = f"missing '{datetime_col}' column"
                results[filename] = file_result
                continue
            
            # Convert to datetime and sort
            df[datetime_col] = pd.to_datetime(df[datetime_col])
            df.sort_values(datetime_col, inplace=True)
            
            # Count duplicates before removal
            duplicates = df.duplicated(subset=[datetime_col], keep=False)
            initial_duplicates = duplicates.sum()
            
            # Remove duplicates
            df.drop_duplicates(subset=[datetime_col], keep=keep, inplace=True)
            
            # Calculate duplicates removed
            duplicates_removed = initial_duplicates - df.duplicated(subset=[datetime_col], keep=False).sum()
            
            # Update results
            file_result.update({
                'duplicates_removed': duplicates_removed,
                'final_rows': len(df),
                'processed_df': df
            })
            
            results[filename] = file_result
            
        except Exception as e:
            results[filename] = {
                'status': f'error: {str(e)}',
                'original_rows': 0,
                'duplicates_removed': 0,
                'final_rows': 0
            }
    
    return results

def save_deduplicated_files(results, output_dir='deduplicated'):
    """
    Save the deduplicated DataFrames to CSV files in output directory.
    
    Args:
        results (dict): Processing results from remove_duplicates_by_datetime()
        output_dir (str): Output directory path
    """
    os.makedirs(output_dir, exist_ok=True)
    
    for filename, result in results.items():
        if 'processed_df' in result:
            output_path = os.path.join(output_dir, os.path.basename(filename))
            result['processed_df'].to_csv(output_path, index=False)
            result['output_path'] = output_path

def print_summary_report(results):
    """
    Print a summary report of the deduplication process.
    
    Args:
        results (dict): Processing results from remove_duplicates_by_datetime()
    """
    total_files = len(results)
    processed_files = sum(1 for r in results.values() if 'processed_df' in r)
    error_files = total_files - processed_files
    total_duplicates = sum(r['duplicates_removed'] for r in results.values() if 'processed_df' in r)
    
    print("\n=== Deduplication Summary Report ===")
    print(f"Total files processed: {total_files}")
    print(f"Successfully processed: {processed_files}")
    print(f"Files with errors: {error_files}")
    print(f"Total duplicates removed: {total_duplicates}")
    
    if error_files > 0:
        print("\nFiles with errors:")
        for filename, result in results.items():
            if 'processed_df' not in result:
                print(f"- {filename}: {result['status']}")

if __name__ == "__main__":
    # Configuration
    csv_files = [
        './WeatherData/Pasay City Weather Data.csv',
        
    ]
    
    datetime_column = 'datetime'  # Your datetime column name
    keep_preference = 'last'      # 'last' (most recent) or 'first' (oldest)
    output_directory = 'deduplicated_output'
    
    print(f"Starting deduplication at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Processing {len(csv_files)} files...")
    print(f"Using datetime column: '{datetime_column}'")
    print(f"Keeping {keep_preference} occurrence of duplicates\n")
    
    # Process files
    results = remove_duplicates_by_datetime(
        filenames=csv_files,
        datetime_col=datetime_column,
        keep=keep_preference
    )
    
    # Save results
    save_deduplicated_files(results, output_directory)
    
    # Print report
    print_summary_report(results)
    
    print(f"\nDeduplicated files saved to: {output_directory}")