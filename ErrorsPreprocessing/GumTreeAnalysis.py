import csv
import os
from GumTreeDiff import Textdiff
from distance import levenshtein_ratio_and_distance
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

today = date.today()
csv_file = "error_analysis.csv"
new_csv_file = "error_analysis_output_" + str(datetime.now().time()) + ".csv"


class GumTreeAnalysis:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.fieldnames = None
        self.reader = None
        self.writer = None
        self.plotter = Plotter()

    def clean(self):
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def open_files(self):
        self.input_csvfile = open(self.input_file, "r")
        self.output_csvfile = open(self.output_file, "w", newline='')

        self.reader = csv.DictReader(self.input_csvfile)
        self.fieldnames = self.reader.fieldnames
        self.reader.fieldnames = self.reader.fieldnames + ['gumtree_textdiff']
        self.reader.fieldnames = self.reader.fieldnames + ['num_steps']
        self.reader.fieldnames = self.reader.fieldnames + ['isLocalFix']

        self.writer = csv.DictWriter(
            self.output_csvfile, fieldnames=self.reader.fieldnames)
        self.writer.writeheader()

    def close_files(self):
        self.input_csvfile.close()
        self.output_csvfile.close()

    def create_textdiff_rows(self):
        print("Creating textdiff rows...")
        for row in self.reader:
            print("Processing row with filename: {} ...".format(row['File']))
            old_str = row['Error_Cell']
            new_str = row['Fixed_Cell']
            try:
                tdiff = Textdiff(old_str, new_str)
                row['gumtree_textdiff'] = tdiff
                self.writer.writerow(row)
            except Exception as e:
                print('-----------------')
                print(e)
        print("Done.")

    def create_num_steps(self):
        print("Creating num_steps rows...")
        self.fieldnames.append('num_steps')

        # Reopen files
        self.input_csvfile.close()
        self.output_csvfile.close()
        self.open_files()

        # Write modified data to the output file
        for row in self.reader:
            original_index = int(row['Original_Index'])
            fixed_index = int(row['Fixed_Index'])
            num_steps = fixed_index - original_index
            row['num_steps'] = num_steps
            self.writer.writerow(row)
        print("Done.")

    def create_isLocalFix_rows(self):
        print("Creating isLocalFix rows...")
        self.fieldnames.append('isLocalFix')

        # Reopen files
        self.input_csvfile.close()
        self.output_csvfile.close()
        self.open_files()

        for row in self.reader:
            # if two cells are the same => similarity = 1 => global fix
            similarity = levenshtein_ratio_and_distance(
                row['Error_Cell'], row['Fixed_Cell'], ratio_calc=True)
            if similarity == 1.0:
                row['isLocalFix'] = False
            else:
                row['isLocalFix'] = True
            self.writer.writerow(row)

    def plot_histogram(self, csv_file, column_name):
        self.plotter.plot_histogram(csv_file, column_name)

    def plot_piechart_global_fix(self, global_fix, local_fix):
        self.plotter.plot_piechart_global_fix(global_fix, local_fix)


class Plotter:

    def plot_histogram(self, csv_file, column_name):
        num_steps = []

        with open(csv_file, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                num_steps.append(int(row[column_name]))

        num_bins = 'auto'
        hist, bin_edges = np.histogram(num_steps, bins=num_bins)

        # Use integer bin edges and centers
        bin_edges = np.round(bin_edges).astype(int)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) // 2

        plt.hist(num_steps, bins=bin_edges, alpha=0.7, edgecolor='black')

        # Add the count and x value for each bar
        for i in range(len(hist)):
            plt.text(bin_centers[i], hist[i], f"{hist[i]}, {bin_centers[i]}",
                     ha='center', va='bottom', fontsize=8)

        plt.xlabel('Number of Steps')
        plt.ylabel('Frequency')
        plt.title(f'Histogram of {column_name}')
        plt.grid(True)
        plt.show()

    def plot_piechart_global_fix(self, global_fix, local_fix):
        labels = 'Global Fix', 'Local Fix'
        sizes = [global_fix, local_fix]
        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%',
                startangle=90)
        # Equal aspect ratio ensures that pie is drawn as a circle.
        ax1.axis('equal')
        plt.show()


if __name__ == "__main__":
    gumtree_analysis = GumTreeAnalysis(csv_file, new_csv_file)
    gumtree_analysis.plot_piechart_global_fix(258, 581)
