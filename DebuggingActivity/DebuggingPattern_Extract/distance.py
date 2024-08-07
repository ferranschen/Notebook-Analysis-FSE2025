import numpy as np

def levenshtein_ratio_and_distance(s, t, ratio_calc=False):
    """ levenshtein_ratio_and_distance:
        Calculates levenshtein distance between two strings.
        If ratio_calc = True, the function computes the
        levenshtein distance ratio of similarity between two strings
        For all i and j, distance[i,j] will contain the Levenshtein
        distance between the first i characters of s and the
        first j characters of t
    """
    # turn multilines into single lines
    s = s.replace("\n", " ")
    t = t.replace("\n", " ")

    # Initialize matrix of zeros
    rows = len(s)+1
    cols = len(t)+1
    distance = np.zeros((rows, cols), dtype=int)

    # Populate matrix of zeros with the indeces of each character of both strings
    for i in range(1, rows):
        for k in range(1, cols):
            distance[i][0] = i
            distance[0][k] = k

    # Iterate over the matrix to compute the cost of deletions,insertions and/or substitutions
    for col in range(1, cols):
        for row in range(1, rows):
            if s[row-1] == t[col-1]:
                # If the characters are the same in the two strings in a given position [i,j] then the cost is 0
                cost = 0
            else:
                # In order to align the results with those of the Python Levenshtein package, if we choose to calculate the ratio
                # the cost of a substitution is 2. If we calculate just distance, then the cost of a substitution is 1.
                if ratio_calc == True:
                    cost = 2
                else:
                    cost = 1
            distance[row][col] = min(distance[row-1][col] + 1,      # Cost of deletions
                                     # Cost of insertions
                                     distance[row][col-1] + 1,
                                     distance[row-1][col-1] + cost)     # Cost of substitutions
    if ratio_calc == True:
        # Computation of the Levenshtein Distance Ratio
        Ratio = ((len(s) + len(t)) - distance[row - 1][col - 1]) / (len(s) + len(t))
        return Ratio
    else:
        # This is the minimum number of edits needed to convert string a to string b
        return "The strings are {} edits away".format(distance[row - 1][col - 1])


def exist_similar_code(code, compact_cells):
    for compact_cell in compact_cells:
        similarity = levenshtein_ratio_and_distance(
            code, compact_cell, ratio_calc=True)
        if similarity > 0.8:
            return True
    return False


def compress_ratio(cells, compact_cells):
    total = 0
    for cell in cells:
        total += len(cell)
    compact_total = 0
    for cell in compact_cells:
        compact_total += len(cell)
    return compact_total / total
