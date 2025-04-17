import os
import pandas as pd
from datetime import datetime

def merge_csv_files(root_dir, output_filename='merged_output.csv'):
    """
    Merge all CSV files found in year subdirectories of the root directory.
    
    Args:
        root_dir (str): Directory containing year folders with CSV files
        output_filename (str): Name for the merged output file
    """
    # Initialize an empty list to store DataFrames
    all_data = []
    
    # Track processed files and folders
    processed_files = 0
    processed_folders = 0
    skipped_files = 0
    
    print(f"Starting CSV merge process at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scanning directory: {root_dir}")
    
    # Get list of year folders (2000, 2001, etc.)
    try:
        year_folders = [f for f in os.listdir(root_dir) if f.isdigit() and os.path.isdir(os.path.join(root_dir, f))]
        year_folders.sort()
    except Exception as e:
        print(f"Error reading directory: {str(e)}")
        return
    
    if not year_folders:
        print("No year folders found in the directory.")
        return
    
    print(f"Found {len(year_folders)} year folders to process...")
    
    # Process each year folder
    for year in year_folders:
        year_path = os.path.join(root_dir, year)
        try:
            # Get all CSV files in the year folder
            csv_files = [f for f in os.listdir(year_path) if f.lower().endswith('.csv')]
            
            if not csv_files:
                print(f"No CSV files found in {year} folder")
                continue
            
            print(f"\nProcessing {year} folder ({len(csv_files)} files)...")
            
            # Process each CSV file in the year folder
            for csv_file in csv_files:
                file_path = os.path.join(year_path, csv_file)
                try:
                    # Read the CSV file
                    df = pd.read_csv(file_path)
                    
                    # Add columns for year and source file
                    df['year'] = year
                    df['source_file'] = csv_file
                    
                    all_data.append(df)
                    processed_files += 1
                    print(f"  Processed: {csv_file} ({len(df)} rows)")
                except Exception as e:
                    print(f"  Error reading {csv_file}: {str(e)}")
                    skipped_files += 1
            
            processed_folders += 1
            
        except Exception as e:
            print(f"Error processing {year} folder: {str(e)}")
            continue
    
    if not all_data:
        print("\nNo valid CSV files found to merge.")
        return
    
    # Concatenate all DataFrames
    try:
        merged_df = pd.concat(all_data, ignore_index=True)
    except Exception as e:
        print(f"\nError merging data: {str(e)}")
        return
    
    # Save the merged DataFrame to a new CSV file
    try:
        merged_df.to_csv(output_filename, index=False)
    except Exception as e:
        print(f"\nError saving output file: {str(e)}")
        return
    
    # Print summary
    print("\nMerge completed successfully!")
    print(f"Total year folders processed: {processed_folders}")
    print(f"Total CSV files merged: {processed_files}")
    if skipped_files > 0:
        print(f"Files skipped due to errors: {skipped_files}")
    print(f"Total rows in output: {len(merged_df)}")
    print(f"Merged file saved as: {output_filename}")

if __name__ == "__main__":
    # HARD-SET your root directory path here
    # Example for Windows: r'C:\Users\YourName\Documents\CSV_Folders'
    # Example for Mac/Linux: '/home/username/Documents/CSV_Folders'
    input_directory = r"C:\Users\User\Downloads\OneDrive_1_4-16-2025\PASIG [DONE '00-'24]"  # <<-- CHANGE THIS TO YOUR ACTUAL PATH
    
    # Verify the path exists
    if not os.path.exists(input_directory):
        print(f"Error: The specified directory does not exist: {input_directory}")
        exit()
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'merged_data_{timestamp}.csv'
    
    # Run the merge function
    merge_csv_files(input_directory, output_file)