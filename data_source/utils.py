import pandas as pd
import numpy as np
import ast  # For safely evaluating strings as literals
import json



# Function to calculate statistics for a list
def calculate_statistics(arr):
    if isinstance(arr, list) and len(arr) > 0:
        mean_val = np.mean(arr)
        median_val = np.median(arr)
        std_val = np.std(arr)
        return mean_val, median_val, std_val
    else:
        return np.nan, np.nan, np.nan
# Function to safely convert string representations of lists to actual lists
def convert_string_to_list(string):
    try:
        return ast.literal_eval(string)
    except (ValueError, SyntaxError):
        # Return the original string if it's not a valid representation of a list
        return string

# Function to convert lists of strings to lists of floats
def convert_to_float_list(lst):
    if isinstance(lst, list):
        try:
            return [float(item) for item in lst]
        except ValueError:
            # Return the original list if elements cannot be converted to float
            return lst
    return lst

# Function to remove outliers
def remove_outliers(arr):
    if isinstance(arr, list) and len(arr) > 0:
        quartile_1, quartile_3 = np.percentile(arr, [25, 75])
        iqr = quartile_3 - quartile_1
        lower_bound = quartile_1 - (1.5 * iqr)
        upper_bound = quartile_3 + (1.5 * iqr)
        return [x for x in arr if lower_bound <= x <= upper_bound]
    else:
        return arr


def process_save_results(json_file_path, output_path):
    # Read the JSON file
    with open(json_file_path, 'r') as file:
        json_data = json.load(file)
    # Initialize an empty list to store the rows
    expriment_metrics = []
    # Iterate through the list of dictionaries in the JSON data
    for item in json_data:
        # Access the "message" key and parse its JSON content
        metrics = json.loads(item["message"])
    
        # Append the parsed content to the data list
        expriment_metrics.append(metrics)
        # Create a DataFrame from the data
    expriment_metrics_df = pd.DataFrame(expriment_metrics)

    # Iterate through each column, convert to float arrays, remove outliers, and add statistics
    for column in expriment_metrics_df.columns:
        # Convert string representations of lists to actual lists
        expriment_metrics_df[column] = expriment_metrics_df[column].apply(convert_string_to_list)

        # Check if the column contains lists
        if expriment_metrics_df[column].apply(lambda x: isinstance(x, list)).any():
            # Convert lists of strings to lists of floats
            expriment_metrics_df[column] = expriment_metrics_df[column].apply(convert_to_float_list)

            # Now remove outliers if the column is a list of floats
            if expriment_metrics_df[column].apply(lambda x: isinstance(x, list) and all(isinstance(i, float) for i in x)).all():
                # Add column with outliers removed
                new_column_name = f"{column}_no_outliers"
                expriment_metrics_df[new_column_name] = expriment_metrics_df[column].apply(remove_outliers)

                # Calculate and add statistics for the original column
                original_stats = expriment_metrics_df[column].apply(calculate_statistics)
                expriment_metrics_df[f'{column}_mean'] = original_stats.apply(lambda x: x[0])
                expriment_metrics_df[f'{column}_median'] = original_stats.apply(lambda x: x[1])
                expriment_metrics_df[f'{column}_std'] = original_stats.apply(lambda x: x[2])

                # Calculate and add statistics for the no_outlier column
                no_outlier_stats = expriment_metrics_df[new_column_name].apply(calculate_statistics)
                expriment_metrics_df[f'{new_column_name}_mean'] = no_outlier_stats.apply(lambda x: x[0])
                expriment_metrics_df[f'{new_column_name}_median'] = no_outlier_stats.apply(lambda x: x[1])
                expriment_metrics_df[f'{new_column_name}_std'] = no_outlier_stats.apply(lambda x: x[2])

    # Save the DataFrame to a CSV file
    expriment_metrics_df.to_csv(output_path, index=False)