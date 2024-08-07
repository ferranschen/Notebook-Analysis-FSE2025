import subprocess
import pprint
import sys
import re
from tempfile import NamedTemporaryFile

# make it a command line tool

GUMTREE_BIN = "gumtree-3.1.0-SNAPSHOT/bin/gumtree"

# * webdiff: Web diff client
# * cluster: Extract action clusters
# * dotdiff: A dot diff client
# * htmldiff: Dump diff as HTML in stdout
# * list: List matchers, generators, clients and properties
# * parse: Parse file and dump result.
# * swingdiff: A swing diff client
# * textdiff: Dump actions in a textual format.
# * axmldiff: Dump annotated xml tree


# web diff
def webdiff(old, new):
    subprocess.call([GUMTREE_BIN, "webdiff", old, new])

# cluster


def cluster(old, new):
    subprocess.call([GUMTREE_BIN, "cluster", old, new])

# dot diff


def dotdiff(old, new):
    subprocess.call([GUMTREE_BIN, "dotdiff", old, new])

# html diff


def htmldiff(old, new):
    subprocess.call([GUMTREE_BIN, "htmldiff", old, new])

# list


def list():
    subprocess.call([GUMTREE_BIN, "list"])

# parse


def parse(old, new):
    subprocess.call([GUMTREE_BIN, "parse", old, new])

# swing diff


def swingdiff(old, new):
    subprocess.call([GUMTREE_BIN, "swingdiff", old, new])

# text diff


def textdiff(old, new):
    # save the result and pass it to the parse function
    output = subprocess.check_output([GUMTREE_BIN, "textdiff", old, new])
    # pprint.pprint(process_diff_output(output.decode('utf-8')))
    return output.decode('utf-8')

# annotated xml diff


def axmldiff(old, new):
    subprocess.call([GUMTREE_BIN, "axmldiff", old, new])


def count_matches(diff_output):
    matches = diff_output.count("match")
    return matches


def count_insertions(diff_output):
    insertions = diff_output.count("insert")
    return insertions


def count_deletions(diff_output):
    deletions = diff_output.count("delete")
    return deletions


def count_updates(diff_output):
    updates = diff_output.count("update")
    return updates


def count_move(diff_output):
    moves = diff_output.count("move")
    return moves


def process_diff_output(diff_output):
    num_matches = count_matches(diff_output)
    num_insertions = count_insertions(diff_output)
    num_deletions = count_deletions(diff_output)
    num_updates = count_updates(diff_output)
    num_moves = count_move(diff_output)

    insights = {
        'matches': num_matches,
        'insertions': num_insertions,
        'deletions': num_deletions,
        'updates': num_updates,
        'moves': num_moves
    }

    return insights


# main
def main():
    if len(sys.argv) < 3:
        print(
            "Usage: python GumTreeDiff.py [webdiff|cluster|dotdiff|htmldiff|list|parse|swingdiff|textdiff|axmldiff] old new")
        return
    if sys.argv[1] == "webdiff":
        webdiff(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "cluster":
        cluster(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "dotdiff":
        dotdiff(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "htmldiff":
        htmldiff(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "list":
        list()
    elif sys.argv[1] == "parse":
        parse(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "swingdiff":
        swingdiff(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "textdiff":
        textdiff(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "axmldiff":
        axmldiff(sys.argv[2], sys.argv[3])
    else:
        print(
            "Usage: python GumTreeDiff.py [webdiff|cluster|dotdiff|htmldiff|list|parse|swingdiff|textdiff|axmldiff] old new")

# export functions


def Textdiff(old_str, new_str):
    # Create temporary Python files for old_str and new_str
    with NamedTemporaryFile(mode="w", delete=False, suffix=".py") as old_file, NamedTemporaryFile(mode="w", delete=False, suffix=".py") as new_file:
        old_file.write(old_str)
        old_file.flush()
        new_file.write(new_str)
        new_file.flush()

        # Save the result and pass it to the parse function
        output = subprocess.check_output(
            [GUMTREE_BIN, "textdiff", old_file.name, new_file.name])
        # pprint.pprint(process_diff_output(output.decode('utf-8')))
        return output.decode('utf-8')


if __name__ == "__main__":
    main()
