import os
import csv
import nbformat
from distance import levenshtein_ratio_and_distance

# 1. read the executed notebook files in the ./executed directory
executed_path = './executed'
files = os.listdir(executed_path)
files = [os.path.join(executed_path, f) for f in files if f.endswith('.ipynb')]

# Initialize the cache dictionary
similarity_cache = {}

# 2. Create a CSV file called error_analysis.csv (if not existed then create one)
csv_file = "error_analysis.csv"
csv_columns = ["File", "Original_Index", "Error_Cell",
               "Fixed_Index", "Fixed_Cell", "Error_Type"]
if not os.path.exists(csv_file):
    with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(csv_columns)

# Read the existing CSV file and store analyzed file names in a set
analyzed_files = set()
if os.path.exists(csv_file):
    with open(csv_file, 'r', newline='', encoding='utf-8') as csvfile:
        csv_reader = csv.reader(csvfile)
        next(csv_reader)  # Skip header row
        for row in csv_reader:
            analyzed_files.add(row[0])
print("Analyzed files: {}".format(analyzed_files))
# 3. Read the content of each notebook file
for f in files:
    # Print the file name
    print("Processing file: {} ...".format(f))

    if f not in analyzed_files:
        with open(f, 'r') as fp:
            nb = nbformat.read(fp, as_version=4)
        for cell in nb.cells:
            # Print the progress on a separate line
            print("\rpos: {} / {}".format(nb.cells.index(cell),
                  len(nb.cells)), end='', flush=True)
            if cell.cell_type == 'code':
                if cell.outputs:
                    for output in cell.outputs:
                        if output.output_type == 'error':
                            cell.source = ''.join(cell.source)
                            error_cells_content = cell.source
                            output = ''.join(output.traceback)
                            error_type = output.split(' ')[0]
                            error_cells_index = nb.cells.index(cell)

                            next_15_cells = nb.cells[nb.cells.index(
                                cell) + 1:nb.cells.index(cell) + 1 + 15]

                            for next_cell in next_15_cells:
                                cache_key = (
                                    cell.source, ''.join(next_cell.source))
                                if cache_key not in similarity_cache:
                                    similarity = levenshtein_ratio_and_distance(
                                        cell.source, ''.join(next_cell.source), ratio_calc=True)
                                    similarity_cache[cache_key] = similarity
                                else:
                                    similarity = similarity_cache[cache_key]

                                if similarity > 0.7 and next_cell.cell_type == 'code' and next_cell.outputs and next_cell.outputs[0].output_type != 'error':
                                    fixed_cells_index = nb.cells.index(
                                        next_cell)
                                    fixed_cells_content = ''.join(
                                        next_cell.source)

                                    # 4. Save the original index, the error cell, the fixed cells, and the error type as corresponding columns
                                    with open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
                                        csv_writer = csv.writer(csvfile)
                                        csv_writer.writerow(
                                            [f, error_cells_index, error_cells_content, fixed_cells_index, fixed_cells_content, error_type])
                                    break
