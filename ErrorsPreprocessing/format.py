import csv
import re

csv_file = "error_analysis.csv"

# Define a function to extract the error type using a regular expression


# List of common Python errors
common_errors = [
    "AttributeError",
    "IOError",
    "ImportError",
    "IndexError",
    "KeyError",
    "NameError",
    "OSError",
    "SyntaxError",
    "TypeError",
    "ValueError",
    "ZeroDivisionError",
    "NotFound",
    "BadRequest",
    "UnboundLocalError",
    "UFuncTypeError",
    "ModuleNotFoundError",
]

# Define a function to extract the error type by checking if the error string contains a common error


def extract_error_type(error_string):
    for error in common_errors:
        if error in error_string:
            return error
    return "Unknown"


# Read the error_analysis.csv file and store the rows in a list
with open(csv_file, 'r', newline='', encoding='utf-8') as csvfile:
    csv_reader = csv.DictReader(csvfile)
    data = [row for row in csv_reader]

# Update the 'Error_Type' column with extracted error types
for row in data:
    row['Error_type'] = extract_error_type(row['Error_Type'])

# Write the updated data back to error_analysis.csv
with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = data[0].keys()
    csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    csv_writer.writeheader()
    for row in data:
        csv_writer.writerow(row)
