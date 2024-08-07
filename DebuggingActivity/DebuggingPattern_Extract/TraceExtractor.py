import csv
import nbformat
from distance import levenshtein_ratio_and_distance
from datetime import datetime


input_file = "error_analysis_primary.csv"
output_file = "error_analysis_output_" + str(datetime.now().time()) + ".csv"

SIMILARITY_THRESHOLD_NEW_CELL = 0.5
SIMILARITY_THRESHOLD_SMALL_EDIT = 0.7


class TraceExtractor:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.fieldnames = None
        self.reader = None
        self.writer = None
        self.rows = []
        self.cell_similarity = {}

    def run(self):
        with open(self.input_file, "r") as input_file:
            self.reader = csv.DictReader(input_file)
            self.fieldnames = self.reader.fieldnames
            self.fieldnames += ["debug_history", "debug_history_idx", "debug_pattern"]

            self.extract_pattern()
            self.analyze_pattern()
            self.store_pattern()

    def extract_pattern(self):
        file = None
        nb = None
        for row in self.reader:
            print(
                "Extracting: Processing row with filename: {} ...".format(row["File"])
            )
            # if the file is new
            if file != row["File"]:
                file = row["File"]
                fp = open(file, "r")
                nb = nbformat.read(fp, as_version=4)
            # init a list of debug history
            debug_history = []
            debug_history_idx = []
            original_idx = row["Original_Index"]
            fixed_idx = row["Fixed_Index"]

            # read the cells from original index(not included) to fixed index
            for i in range(int(original_idx) + 1, int(fixed_idx) + 1):
                cell = nb["cells"][i]
                if cell["cell_type"] == "code":
                    debug_history.append(cell["source"])
                    debug_history_idx.append(i)
            row["debug_history"] = debug_history
            row["debug_history_idx"] = debug_history_idx

            self.rows.append(row)

    def analyze_pattern(self):
        file = None
        nb = None
        with open(
            "debug_sequence_" + str(datetime.now().time()) + ".txt", "w"
        ) as output_file:  # Open the output file
            for row in self.rows:
                pattern = []
                print(
                    "Analyzing: Processing row with filename: {} original index: {} ...".format(
                        row["File"], row["Original_Index"]
                    )
                )
                if file != row["File"]:
                    file = row["File"]
                    fp = open(file, "r")
                    nb = nbformat.read(fp, as_version=4)

                debug_range = row["debug_history_idx"]

                for i in debug_range:
                    if self.is_repeat_error_cell(row["Original_Index"], i, nb):
                        pattern.append("Re")
                    elif self.is_repeat_before_cell(row["Original_Index"], i, nb):
                        pattern.append("Rb")
                    elif self.is_newly_created_cell(row["Original_Index"], i, nb):
                        pattern.append("C")
                    elif self.is_small_edit_of_error_cell(row["Original_Index"], i, nb):
                        pattern.append("SEe")
                    elif self.is_small_edit_of_previous_cell(
                        row["Original_Index"], i, nb
                    ):
                        pattern.append("SEb")
                    else:
                        pattern.append("Eb")

                row["debug_pattern"] = pattern
                print("Pattern: {}".format(pattern))

                # Write the pattern to the file immediately after it's generated
                output_file.write("File: {}\n".format(row["File"]))
                output_file.write("Original Index: {}\n".format(row["Original_Index"]))
                output_file.write("Debug Sequence: {}\n".format(pattern))
                output_file.write("\n")
                output_file.flush()  # Make sure the data is written to the file

                self.rows.append(row)

    def store_pattern(self):
        with open(self.output_file, "w", newline="") as output_file:
            self.writer = csv.DictWriter(output_file, fieldnames=self.fieldnames)
            self.writer.writeheader()
            self.writer.writerows(self.rows)

    def is_repeat_error_cell(self, error_cell_idx, cell_idx, nb):
        # Ensure error_cell_idx is an integer
        error_cell_idx = int(error_cell_idx)
        cell_idx = int(cell_idx)

        similarity = levenshtein_ratio_and_distance(
            nb["cells"][error_cell_idx]["source"],
            nb["cells"][cell_idx]["source"],
            ratio_calc=True,
        )

        if similarity == 1.0:
            return True
        return False

    def is_repeat_before_cell(self, error_cell_idx, cell_idx, nb):
        # Ensure error_cell_idx is an integer
        error_cell_idx = int(error_cell_idx)
        cell_idx = int(cell_idx)  # Ensure cell_idx is an integer

        # Iterate over all previous cells before the error cell
        for i in range(0, cell_idx):
            if i == error_cell_idx:
                print("Skipping error cell")
                continue
            else:
                similarity = levenshtein_ratio_and_distance(
                    nb["cells"][i]["source"],
                    nb["cells"][cell_idx]["source"],
                    ratio_calc=True,
                )
                if similarity == 1.0:
                    return True
        return False

    def is_newly_created_cell(self, error_cell_idx, cell_idx, nb):
        # Ensure error_cell_idx is an integer
        error_cell_idx = int(error_cell_idx)
        cell_idx = int(cell_idx)  # Ensure cell_idx is an integer

        # Iterate over all previous cells before the error cell
        for i in range(0, cell_idx):
            if i == error_cell_idx:
                print("Skipping error cell")
                continue
            else:
                similarity = levenshtein_ratio_and_distance(
                    nb["cells"][i]["source"],
                    nb["cells"][cell_idx]["source"],
                    ratio_calc=True,
                )
                # If the cell is similar to any previous cell, it is not newly created
                if similarity > SIMILARITY_THRESHOLD_NEW_CELL:
                    return False
        # If we've gone through all previous cells and found no similar cell,
        # it's a newly created cell
        return True

    def is_small_edit_of_error_cell(self, error_cell_idx, cell_idx, nb):
        # Ensure error_cell_idx is an integer
        error_cell_idx = int(error_cell_idx)
        cell_idx = int(cell_idx)

        similarity = levenshtein_ratio_and_distance(
            nb["cells"][error_cell_idx]["source"],
            nb["cells"][cell_idx]["source"],
            ratio_calc=True,
        )
        if SIMILARITY_THRESHOLD_SMALL_EDIT < similarity < 1.0:
            return True
        return False

    def is_small_edit_of_previous_cell(self, error_cell_idx, cell_idx, nb):
        # Ensure error_cell_idx is an integer
        error_cell_idx = int(error_cell_idx)
        cell_idx = int(cell_idx)  # Ensure cell_idx is an integer

        # Iterate over all previous cells before the error cell
        for i in range(0, cell_idx):
            if i == error_cell_idx:
                print("Skipping error cell")
                continue
            else:
                similarity = levenshtein_ratio_and_distance(
                    nb["cells"][i]["source"],
                    nb["cells"][cell_idx]["source"],
                    ratio_calc=True,
                )
                # If the cell is a small edit of a previous cell, return True
                if SIMILARITY_THRESHOLD_SMALL_EDIT < similarity < 1.0:
                    return True

        return False


if __name__ == "__main__":
    analysis = TraceExtractor(input_file, output_file)
    analysis.run()
