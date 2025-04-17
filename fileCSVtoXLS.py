import os
import pandas as pd
from datetime import datetime

def excel_to_csv(input_folder, output_folder=None):
    """
    Convert all Excel files in a folder to CSV format.
    
    Args:
        input_folder (str): Path to folder containing Excel files
        output_folder (str): Path to save CSV files (defaults to input_folder/CSV_Output)
    """
    # Set default output folder if not specified
    if output_folder is None:
        output_folder = os.path.join(input_folder, "CSV_Output")
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    print(f"Starting conversion at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Input folder: {input_folder}")
    print(f"Output folder: {output_folder}\n")
    
    # Get list of Excel files
    excel_files = [f for f in os.listdir(input_folder) 
                  if f.lower().endswith(('.xls', '.xlsx'))]
    
    if not excel_files:
        print("No Excel files found in the input folder.")
        return
    
    print(f"Found {len(excel_files)} Excel file(s) to convert:")
    
    # Process each Excel file
    for excel_file in excel_files:
        try:
            input_path = os.path.join(input_folder, excel_file)
            
            # Generate output filename (same name but with .csv extension)
            csv_file = os.path.splitext(excel_file)[0] + ".csv"
            output_path = os.path.join(output_folder, csv_file)
            
            # Read Excel file
            print(f"\nConverting: {excel_file}")
            df = pd.read_excel(input_path)
            
            # Save as CSV
            df.to_csv(output_path, index=False)
            print(f"Saved as: {csv_file}")
            print(f"Rows converted: {len(df)}")
            
        except Exception as e:
            print(f"Error converting {excel_file}: {str(e)}")
    
    print("\nConversion complete!")
    print(f"Successfully converted {len([f for f in os.listdir(output_folder) if f.endswith('.csv')])} files.")

if __name__ == "__main__":
    # Configuration - modify these values as needed
    input_directory = r"C:\Users\User\Downloads\OneDrive_1_4-16-2025\LAS PINAS [DONE '00-'24]"  # Replace with your folder path
    output_directory = "./CSV_Output"  # None will create a CSV_Output subfolder
    
    # Verify the input path exists
    if not os.path.exists(input_directory):
        print(f"Error: The specified directory does not exist: {input_directory}")
        exit()
    
    # Run the conversion
    excel_to_csv(input_directory, output_directory)