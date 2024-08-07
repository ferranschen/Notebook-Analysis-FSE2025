import pandas as pd


class DebugPatternAnalysis:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file

    def remove_duplicates(self):
        # Load the data from the CSV file
        df = pd.read_csv(self.input_file)

        # Drop duplicates based on 'Error_Cell' column  and  Original_Index column
        df.drop_duplicates(
            subset=["Error_Cell", "Original_Index"], keep="first", inplace=True
        )

        # Save the modified DataFrame to a new CSV file
        df.to_csv(self.output_file, index=False)


# Run the process
if __name__ == "__main__":
    analysis = DebugPatternAnalysis("error_analysis.csv", "error_analysis_primary.csv")
    analysis.remove_duplicates()
