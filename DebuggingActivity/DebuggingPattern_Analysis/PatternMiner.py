from collections import Counter
from collections import defaultdict
import matplotlib.pyplot as plt
import random

import plotly.graph_objects as go


class PatternMiner:
    def __init__(self, input_file, output_file):
        self.debug_sequence_file = input_file
        self.debug_pattern_file = output_file
        self.all_sequences = []

    # the file format is:
    # Debug Sequence: ['SEb', 'Rb', 'Re', 'SEb', 'Rb', 'Re']
    def read_sequences(self):
        with open(self.debug_sequence_file, "r") as f:
            for line in f:
                if line.startswith("Debug Sequence:"):
                    # Remove the "Debug Sequence:" part and leading/trailing white space
                    line = line.replace("Debug Sequence:", "").strip()

                    # Remove the leading/trailing [ and ]
                    line = line.replace("[", "").replace("]", "")

                    # Split the remainder of the line into individual symbols
                    sequence = line.split(", ")

                    # for each element in the sequence, remove the leading/trailing ' and "
                    for i in range(len(sequence)):
                        sequence[i] = sequence[i].replace("'", "").replace('"', "")
                    # Convert the sequence to integers
                    self.all_sequences.append(
                        self._convert_symbos_to_integers(sequence)
                    )

    def _generate_subsequences(self, sequence, min_len, max_len):
        subsequences = []
        for i in range(len(sequence)):
            for length in range(min_len, min(max_len, len(sequence) - i) + 1):
                subsequences.append(tuple(sequence[i : i + length]))
        return subsequences

    def _convert_subsequence_to_symbols(self, subsequence):
        symbol_map = {
            1: "Rb",
            2: "Re",
            3: "Eb",
            4: "SEe",
            5: "SEb",
            6: "C",
            7: "error cell",
            8: "end",
        }
        return [symbol_map[i] for i in subsequence]

    def _convert_symbos_to_integers(self, subsequence):
        symbol_map = {
            "Rb": 1,
            "Re": 2,
            "Eb": 3,
            "SEe": 4,
            "SEb": 5,
            "C": 6,
            "error cell": 7,
            "end": 8,
        }
        return [symbol_map[i] for i in subsequence]

    def _group_and_sort_subsequences(self, subsequence_counts):
        subsequences_by_length = defaultdict(list)
        total_counts_by_length = defaultdict(int)

        for subsequence, count in subsequence_counts.items():
            length = len(subsequence)
            subsequences_by_length[length].append((subsequence, count))
            total_counts_by_length[length] += count

        for length, subsequences in subsequences_by_length.items():
            subsequences.sort(key=lambda x: x[1], reverse=True)

        return subsequences_by_length, total_counts_by_length

    def _print_top_subsequences(self, subsequences_by_length, total_counts_by_length):
        for length, subsequences in subsequences_by_length.items():
            print(
                f"Sequence with Length {length} (total:{total_counts_by_length[length]}):"
            )
            for subsequence, count in subsequences[:10]:
                print(
                    f"  Subsequence {self._convert_subsequence_to_symbols(subsequence)} occurs {count} times (ratio: {count / total_counts_by_length[length]:.2%})"
                )

    def mine(self, min_subsequence_length=1, max_subsequence_length=None):
        print("Mining...")
        print("Num sequences: {}".format(len(self.all_sequences)))

        if max_subsequence_length is None:
            # If not provided, set max_subsequence_length to the length of the longest sequence
            max_subsequence_length = max(len(s) for s in self.all_sequences)

        # Counter to store subsequence frequencies
        subsequence_counts = Counter()

        # For each sequence, generate all subsequences and update their count
        for sequence in self.all_sequences:
            subsequences = self._generate_subsequences(
                sequence, min_subsequence_length, max_subsequence_length
            )
            subsequence_counts.update(subsequences)

        # Group subsequences by length and sort them by frequency
        (
            subsequences_by_length,
            total_counts_by_length,
        ) = self._group_and_sort_subsequences(subsequence_counts)

        # Print the top 10 subsequences by frequency
        self._print_top_subsequences(subsequences_by_length, total_counts_by_length)

        # Return the dictionary of subsequence counts
        return subsequence_counts

    def modify_sequences_for_sankey(self):
        modified_sequences = []
        for sequence in self.all_sequences:
            modified_sequence = [7] + sequence + [8]
            modified_sequences.append(modified_sequence)
        return modified_sequences

    def draw_sankey(self):
        # Get the modified sequences
        modified_sequences = self.modify_sequences_for_sankey()

        # Count the links
        link_counts = Counter()
        for sequence in modified_sequences:
            for i in range(len(sequence) - 1):
                link_counts[(sequence[i], sequence[i + 1])] += 1

        # print link (source, target) and count
        for link, count in link_counts.items():
            print(f"Link {link} has count {count}")

        # Create the nodes and links for the Sankey diagram
        nodes = list(set([node for link in link_counts.keys() for node in link]))
        node_labels = [
            self._convert_subsequence_to_symbols([node])[0] for node in nodes
        ]

        links = list(link_counts.keys())
        link_values = list(link_counts.values())

        # Assign colors to the links
        color_mapping = {
            link: f"rgba({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)}, 0.7)"
            for link in links
        }
        link_colors = [color_mapping[link] for link in links]

        # Map links to node indices
        link_indices = [(nodes.index(link[0]), nodes.index(link[1])) for link in links]

        source = [link[0] for link in link_indices]
        target = [link[1] for link in link_indices]

        # # remove the edges that are too small
        # for i in range(len(link_values)):
        #     if link_values[i] < 10:
        #         link_values[i] = 0

        # Create the Sankey diagram
        fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=node_labels,
                        color="blue",
                    ),
                    link=dict(
                        source=source,
                        target=target,
                        value=link_values,
                        color=link_colors,  # Use assigned link colors
                    ),
                )
            ]
        )

        fig.update_layout(title_text="Flow Diagram of All Sequences", font_size=10)
        fig.show()


if __name__ == "__main__":
    input_file = "debug_sequence.txt"
    output_file = "debug_pattern.txt"
    miner = PatternMiner(input_file, output_file)
    miner.read_sequences()
    miner.mine()
    miner.draw_sankey()
