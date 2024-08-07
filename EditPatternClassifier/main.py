import EditPatternClassifier as epc
import csv
import os

GUMTREE_BIN = "./gumtree/dist/build/install/gumtree/bin/gumtree"


# read a csv file named error_analysis_primary.csv
with open("error_analysis_primary.csv", "r") as input_file:
    reader = csv.DictReader(input_file)
    rows = list(reader)
    for row, idx in zip(rows, range(len(rows))):
        print("Processing row", idx)
        print(row["Error_Cell"])
        with open("file1.py", "w") as file1:
            file1.write(row["Error_Cell"])
        with open("file2.py", "w") as file2:
            file2.write(row["Fixed_Cell"])
        epm = epc.EditPatternClassifier("file1.py", "file2.py", GUMTREE_BIN)
        epm.run_gumtree()
        # create a new column named edit_pattern
        row["edit_pattern"] = epm.analyze()
        os.remove("file1.py")
        os.remove("file2.py")

    # save the output of gumtree to a new csv file named error_analysis_primary_output.csv
    with open("error_analysis_primary_output.csv", "w") as output_file:
        reader.fieldnames.append("edit_pattern")
        writer = csv.DictWriter(output_file, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    edit_patterns = {}

    for row in rows:
        edit_pattern = row.get("edit_pattern")
        if edit_pattern:
            for ep in edit_pattern:
                edit_patterns[ep] = edit_patterns.get(ep, 0) + 1
        else:
            edit_patterns["Unknown"] = edit_patterns.get("Unknown", 0) + 1

    # find the top 5 edit patterns and their counts
    top_5_edit_patterns = sorted(
        edit_patterns.items(), key=lambda x: x[1], reverse=True
    )[:5]
    print("top_5_edit_patterns: ", top_5_edit_patterns)
    print("edit_patterns: ", edit_patterns)
