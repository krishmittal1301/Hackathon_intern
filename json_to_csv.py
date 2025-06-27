import pandas as pd
import json

def json_to_dataframe(json_file_path: str) -> pd.DataFrame:
    """
    Converts a JSON response file into a pandas DataFrame.
    Filters keys starting with 'new_' and handles case differences in attributes.
    
    Args:
        json_file_path (str): Path to the JSON file.
    
    Returns:
        pd.DataFrame: A DataFrame containing the filtered and processed data.
    """
    # Load JSON data
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Initialize a list to store processed rows
    processed_data = []
    
    # Iterate over each record in the JSON data
    for record in data:
        # Filter keys starting with 'new_' and normalize case
        filtered_record = {key: value for key, value in record.items() if key.startswith('new_')}
        processed_data.append(filtered_record)
    
    # Create a DataFrame from the processed data
    df = pd.DataFrame(processed_data)
    
    # Normalize column names to match the case of attributes in the CSV
    df.columns = [col.lower() for col in df.columns]
    
    return df

# Example usage
if __name__ == "__main__":
    json_file_path = "c:\\Hackahton Server Function\\response.json"
    dataframe = json_to_dataframe(json_file_path)
    print(dataframe.head())  # Display the first few rows of the DataFrame
