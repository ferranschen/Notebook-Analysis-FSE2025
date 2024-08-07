import subprocess
import re
import regex
import ast

GUMTREE_BIN = "./gumtree/dist/build/install/gumtree/bin/gumtree"


class EditPatternClassifier:
    def __init__(self, old_code_path, new_code_path, gumtree_bin_path):
        self.old_code_path = old_code_path
        self.new_code_path = new_code_path
        self.textdiff = None

        self.gumtree_bin_path = GUMTREE_BIN
        self.updated_new_identifiers = []
        self.edit_patterns = []

    def run_executable(self, executable_path):
        self.textdiff = subprocess.check_output(
            [executable_path, "textdiff", self.old_code_path, self.new_code_path]
        )
        if self.textdiff == b"":
            print("Error: Gumtree could not parse the code.")
            self.textdiff = None
            return
        print("Gumtree output:")
        print(self.textdiff.decode("utf-8"))

    def run_executable_with_filenames(
        self, old_code_path, new_code_path, executable_path
    ):
        textdiff = subprocess.check_output(
            [executable_path, "textdiff", old_code_path, new_code_path]
        )
        return textdiff

    def analyze(self):
        # if textdiff equals b''
        if self.textdiff == None:
            is_fix_syntax_error, error_type = self.is_fix_syntax_error()
            label = "fix_syntax_error"
            if is_fix_syntax_error:
                label += "_" + error_type

            self.edit_patterns.append(label)
            return self.edit_patterns

        if self.is_identical():
            self.edit_patterns.append("identical")
            return self.edit_patterns

        is_variable_rename, updated_identifiers = self.is_variable_rename()
        if is_variable_rename:
            self.edit_patterns.append("rename_variable")
        is_lines_deleted = self.is_lines_deleted()
        if is_lines_deleted:
            self.edit_patterns.append("lines_deleted")

        is_lines_added = self.is_lines_added()
        if is_lines_added:
            self.edit_patterns.append("lines_added")

        is_add_new_method = self.is_add_new_method()
        if is_add_new_method[0]:
            print("add_new_method")
            self.edit_patterns.append("add_new_method")

        is_commented_out = self.is_commented_out()
        if is_commented_out:
            self.edit_patterns.append("code_commented_out")

        is_remove_method, remove_methods = self.is_remove_method()
        if is_remove_method:
            self.edit_patterns.append("remove_method")

        is_remove_attribute, remove_attributes = self.is_remove_attribute()
        if is_remove_attribute:
            self.edit_patterns.append("remove_attribute")

        is_add_new_attribute, add_attributes = self.is_add_new_attribute()
        if is_add_new_attribute:
            self.edit_patterns.append("add_attribute")

        is_change_search_key, search_keys = self.is_change_search_key()
        if is_change_search_key:
            self.edit_patterns.append("change_search_key")

        is_change_parameters, parameters = self.is_change_parameters()
        if is_change_parameters:
            self.edit_patterns.append("change_parameters")

        return self.edit_patterns

    def run_gumtree(self):
        self.run_executable(self.gumtree_bin_path)

    def is_variable_rename(self):
        # Pattern to match update-node entries in the diff tree
        # where only a name node is updated.
        pattern_rename_variable = re.compile(
            r"update-node\n---\nname: (\w+) \[\d+,\d+\]\nreplace (\w+) by (\w+)\n",
            re.MULTILINE,
        )

        # Extract all update-node entries
        updates = pattern_rename_variable.findall(self.textdiff.decode("utf-8"))
        print("updates", updates)
        # Store variable rename info
        variable_rename_info = []

        # Read the new code
        new_code = self.read_file(self.new_code_path)

        # Process each update-node entry
        for old_name, _, new_name in updates:
            # Regular expression pattern to find the new name followed by parenthesis
            pattern = re.compile(re.escape(new_name) + r"\s*\(")

            # Check if this update is within a function/method call in new code
            if not pattern.search(new_code):
                variable_rename_info.append(
                    f'Variable "{old_name}" was renamed to "{new_name}"'
                )
        old_variables = self.find_variables(self.old_code_path)
        new_variables = self.find_variables(self.new_code_path)

        print("old_variables", old_variables)
        print("new_variables", new_variables)

        # If variable renames were found, return True along with the information
        # make sure the variable is also changed in the new code
        if set(variable_rename_info) and set(old_variables) != set(new_variables):
            return True, variable_rename_info

        # If no entry indicates a variable rename, return False.
        return False, None

    def find_variables(self, code_path):
        code = self.read_file(code_path)
        # Pattern matches variables that are followed by '.' or '[' (indicating an attribute, method, or index)
        # and variables that are followed by an equal sign (indicating a variable definition)
        pattern = re.compile(r"(\b\w+\b)(?=\.\w+|\[\w+\]|\s*=)")
        variables = pattern.findall(code)
        return variables

    def is_fix_syntax_error(self):
        new_code = self.read_file(self.new_code_path)
        old_code = self.read_file(self.old_code_path)
        error_type = ""
        try:
            # Try to parse the old code
            ast.parse(old_code)
        except SyntaxError as e:
            error_message = str(e)
            print("error_message", error_message)
            # Handle common syntax errors and suggest fixes
            if "unexpected EOF while parsing" in error_message:
                print(
                    f"Looks like there's a missing parenthesis, bracket, or colon. In your new code, it seems like this error has been resolved."
                )
                error_type = "missing_parenthesis_bracket_colon"

            elif "invalid syntax" in error_message:
                print(
                    f"There's an invalid syntax in your old code. Check for missing or extra characters, incorrect indentation, or unsupported operation. It appears to be fixed in your new code."
                )
                error_type = "invalid_syntax"

            elif "'[' was never closed" in error_message:
                print(
                    f"There's an unclosed bracket '[' in your old code. Check for missing or extra characters, incorrect indentation, or unsupported operation. It appears to be fixed in your new code."
                )
                error_type = "unclosed_bracket"

            elif "'(' was never closed" in error_message:
                print(
                    f"There's an unclosed parenthesis '(' in your old code. Check for missing or extra characters, incorrect indentation, or unsupported operation. It appears to be fixed in your new code."
                )
                error_type = "unclosed_parenthesis"

            elif "invalid character" in error_message:
                print(
                    f"There's an invalid character in your old code. Check for missing or extra characters, incorrect indentation, or unsupported operation. It appears to be fixed in your new code."
                )
            elif "unterminated string literal" in error_message:
                print(
                    f"There's an unterminated string literal in your old code. Check for missing or extra characters, incorrect indentation, or unsupported operation. It appears to be fixed in your new code."
                )
                error_type = "unterminated_string_literal"

            elif "Missing parentheses in call to" in error_message:
                print(
                    f"There's a missing parenthesis in your old code when calling a function. Check for missing or extra characters, incorrect indentation, or unsupported operation. It appears to be fixed in your new code."
                )
                error_type = "missing_parenthesis"
            elif "unmatched ')'" in error_message:
                print(
                    f"There's an unmatched parenthesis ')' in your old code. Check for missing or extra characters, incorrect indentation, or unsupported operation. It appears to be fixed in your new code."
                )
                error_type = "unmatched_parenthesis"
            elif "expected ':'" in error_message:
                print(
                    f"There's a missing colon ':' in your old code. Check for missing or extra characters, incorrect indentation, or unsupported operation. It appears to be fixed in your new code."
                )
                error_type = "missing_colon"
            else:
                print(
                    f"An unexpected syntax error: {error_message}. It seems to be resolved in the new code."
                )
                error_type = "unknown"

        try:
            # Try to parse the new code
            ast.parse(new_code)
        except SyntaxError as e:
            print(f"A syntax error in the new code: {str(e)}")
            return False, "not_fixed"
        print("The new code has no syntax errors.")
        return True, error_type

    def is_lines_deleted(self):
        old_code = self.read_file(self.old_code_path)
        new_code = self.read_file(self.new_code_path)
        old_lines = set(old_code.split("\n"))
        new_lines = set(new_code.split("\n"))

        # Check if there are any lines from the old code that are not present in the new code
        deleted_lines = old_lines - new_lines

        return bool(deleted_lines) and len(old_lines) > len(new_lines)

    def is_lines_added(self):
        old_code = self.read_file(self.old_code_path)
        new_code = self.read_file(self.new_code_path)
        old_lines = set(old_code.split("\n"))
        new_lines = set(new_code.split("\n"))

        # Check if there are any lines from the new code that are not present in the old code
        added_lines = new_lines - old_lines

        return bool(added_lines) and len(new_lines) > len(old_lines)

    def is_add_new_method(self):
        added_methods = self.find_added_methods()
        print(added_methods)

        # if it's an empty set, return false
        if not added_methods:
            return False, None

        textdiff = self.textdiff.decode("utf-8")

        # Check the diff output for insert-tree operation related to a method
        pattern_insert_method = re.compile(
            r"insert-tree\n---\nname: (\w+)\s*\[\d+,\d+\]\n", re.DOTALL
        )
        inserted_methods = pattern_insert_method.findall(textdiff)

        # Check the diff output for update-node operation related to a method
        pattern_update_method = re.compile(
            r"update-node\n---\nname: (\w+) \[\d+,\d+\]\nreplace \1 by (\w+)\n",
            re.DOTALL,
        )
        updated_methods = pattern_update_method.findall(textdiff)
        updated_methods_dict = {old: new for old, new in updated_methods}
        print(updated_methods_dict)

        # Only return true if the methods in inserted_methods or updated_methods_dict are also included in added_methods
        for method in added_methods:
            if method in inserted_methods:
                print(f"Method '{method}' was added.")
                return True, f"Method '{method}' was added."

            # check if method in updated_methods_dict's values
            if method in updated_methods_dict.values():
                print(f"Method '{method}' was added.")
                return True, f"Method '{method}' was added."

        return False, None

    def is_commented_out(self):
        old_code = self.read_file(self.old_code_path)
        new_code = self.read_file(self.new_code_path)

        old_lines = old_code.split("\n")
        new_lines = new_code.split("\n")

        # Find all commented lines in the new code
        new_comment_lines = [line for line in new_lines if line.strip().startswith("#")]

        # Check if any of the old lines are found in the new commented lines
        for old_line in old_lines:
            # Normalize the spaces, replace double quotes with single quotes, and strip the line
            normalized_old_line = " ".join(old_line.split()).replace('"', "'").strip()
            for comment_line in new_comment_lines:
                # We strip the leading '#' and spaces from the commented line,
                # normalize the spaces, replace double quotes with single quotes, and compare it with the old code line
                normalized_comment_line = (
                    " ".join(comment_line[1:].split()).replace('"', "'").strip()
                )
                if normalized_old_line == normalized_comment_line:
                    return True  # If a match is found, we return True

        return False  # If no match is found, we return False

    def is_remove_method(self):
        old_methods = self.find_methods_in_code(self.old_code_path)
        new_methods = self.find_methods_in_code(self.new_code_path)

        remove_methods = old_methods - new_methods

        remove_methods_in_diff = []

        # Check the diff output for delete-tree operations
        textdiff = self.textdiff.decode("utf-8")
        pattern_delete_method = re.compile(r"delete-tree\n---\n(.*?)\n", re.DOTALL)
        deletes = pattern_delete_method.findall(textdiff)

        for method in remove_methods:
            if self.method_deleted_in_diff(method):
                remove_methods_in_diff.append(method)

        # Check if any delete-tree entries are related to a method
        for delete in deletes:
            if "name: " in delete:
                remove_methods_in_diff.append(delete)

        return len(remove_methods_in_diff) > 0, remove_methods_in_diff

    def is_remove_attribute(self):
        # Read the old code and the new code from file
        old_code = self.read_file(self.old_code_path)
        new_code = self.read_file(self.new_code_path)

        # Find all attributes in the old code (e.g. object.attribute)
        old_attributes = set(re.findall(r"\w+\.\w+", old_code))

        # Find all attributes in the new code
        new_attributes = set(re.findall(r"\w+\.\w+", new_code))

        # Find methods in old and new code
        old_methods = self.find_methods_in_code(self.old_code_path)
        new_methods = self.find_methods_in_code(self.new_code_path)
        removed_methods = old_methods - new_methods

        # Find the attributes that are present in the old code but not in the new code
        removed_attributes = old_attributes - new_attributes

        # Exclude method calls from removed_attributes
        for method in removed_methods:
            removed_attributes = {
                attr for attr in removed_attributes if not attr.endswith(f".{method}")
            }

        # Check the diff tree to verify that the attributes were indeed deleted
        removed_attributes_in_diff = set()
        for attribute in removed_attributes:
            if self.attribute_deleted_in_diff(attribute):
                removed_attributes_in_diff.add(attribute)

        # Return True and the removed attributes if there are any, otherwise return False and an empty set
        return len(removed_attributes_in_diff) > 0, removed_attributes_in_diff

    def attribute_deleted_in_diff(self, attribute):
        # Checking for a pattern that indicates deletion of an attribute in the diff tree
        pattern_delete_tree = (
            f"delete-tree\n---\n.*\n.*name: {attribute.split('.')[-1]}"
        )
        pattern_delete_node = (
            f"delete-node\n---\n.*\n.*name: {attribute.split('.')[-1]}"
        )
        if re.search(
            pattern_delete_tree, self.textdiff.decode("utf-8"), re.DOTALL
        ) or re.search(pattern_delete_node, self.textdiff.decode("utf-8"), re.DOTALL):
            return True
        return False

    def is_add_new_attribute(self):
        # Read the old code and the new code from file
        old_code = self.read_file(self.old_code_path)
        new_code = self.read_file(self.new_code_path)

        # Find all attributes in the old code (e.g. object.attribute)
        old_attributes = set(re.findall(r"\w+\.\w+", old_code))

        # Find all attributes in the new code
        new_attributes = set(re.findall(r"\w+\.\w+", new_code))
        # print("new_attributes: " + str(new_attributes))

        # Find methods in old and new code
        old_methods = self.find_methods_in_code(self.old_code_path)
        new_methods = self.find_methods_in_code(self.new_code_path)
        new_methods = new_methods - old_methods
        # print("new_methods: " + str(new_methods))

        # Find the attributes that are present in the new code but not in the old code
        added_attributes = new_attributes - old_attributes

        # Remove method calls from added_attributes
        for method in new_methods:
            added_attributes = {
                attr for attr in added_attributes if not attr.endswith(f".{method}")
            }

        # Check the diff tree to verify that the attributes were indeed added
        added_attributes_in_diff = set()
        for attribute in added_attributes:
            if self.attribute_added_in_diff(attribute):
                added_attributes_in_diff.add(attribute)

        # Return True and the added attributes if there are any, otherwise return False and an empty set
        return len(added_attributes_in_diff) > 0, added_attributes_in_diff

    def find_arguments_in_code(self, code_path):
        code = self.read_file(code_path)
        # Regex to match function calls and their arguments
        pattern = re.compile(r"\w+\(((?:[^()]*|\([^()]*\))*)\)")
        function_calls = pattern.findall(code)
        arguments = []
        # Extracting arguments from the function calls
        for function_call in function_calls:
            args = function_call.split(",")
            # Append all arguments
            arguments.extend([arg.strip() for arg in args])
        return arguments

    def is_change_parameters(self):
        # extract all arguments from the old code
        old_arguments = self.find_arguments_in_code(self.old_code_path)
        # extract all arguments from the new code
        new_arguments = self.find_arguments_in_code(self.new_code_path)

        print("old_arguments: " + str(old_arguments))
        print("new_arguments: " + str(new_arguments))

        pattern_update_node = re.compile(
            r'update-node\n---.*?replace "(.*?)" by "(.*?)"', re.DOTALL
        )
        matches = pattern_update_node.findall(self.textdiff.decode("utf-8"))
        print("---")
        for match in matches:
            print("old: " + str(match[0]))
            print("new: " + str(match[1]))

            old_param_in_new_args = any(
                str(match[0]) in argument.split("=")[-1].replace('"', "").strip()
                for argument in new_arguments
            )
            new_param_in_old_args = any(
                str(match[1]) in argument.split("=")[-1].replace('"', "").strip()
                for argument in old_arguments
            )

            if old_param_in_new_args or new_param_in_old_args:
                print("Mismatch detected in arguments!")
                return True, None  # Arguments changed

        if set(old_arguments) != set(new_arguments):
            print("Arguments are not the same!")
            return True, None  # Arguments changed

        return False, None

    def attribute_added_in_diff(self, attribute):
        # Checking for a pattern that indicates addition of an attribute in the diff tree
        pattern_insert_tree = (
            f"insert-tree\n---\n.*\n.*name: {attribute.split('.')[-1]}"
        )
        pattern_insert_node = (
            f"insert-node\n---\n.*\n.*name: {attribute.split('.')[-1]}"
        )
        if re.search(
            pattern_insert_tree, self.textdiff.decode("utf-8"), re.DOTALL
        ) or re.search(pattern_insert_node, self.textdiff.decode("utf-8"), re.DOTALL):
            return True
        return False

    def is_identical(self):
        old_code = self.read_file(self.old_code_path)
        new_code = self.read_file(self.new_code_path)

        # Check if the old code is exactly the same as the new code
        return old_code == new_code

    def is_change_search_key(self):
        # Read the old code and the new code from file.
        old_code = self.read_file(self.old_code_path)
        new_code = self.read_file(self.new_code_path)

        # Regular expression pattern to match keys inside brackets.
        pattern = re.compile(r"\[([^\]]+)\]")

        # Extract all keys inside brackets in old code.
        old_keys = pattern.findall(old_code)
        # Extract all keys inside brackets in new code.
        new_keys = pattern.findall(new_code)

        # Check update-node replace in the diff tree
        textdiff = self.textdiff.decode("utf-8")
        pattern_update_node = re.compile(
            r'update-node\n---.*?replace "(.*?)" by "(.*?)"', re.DOTALL
        )
        updates = pattern_update_node.findall(textdiff)

        # Check if there are any changes in keys inside brackets.
        for old_key, new_key in zip(old_keys, new_keys):
            if old_key.strip() != new_key.strip():
                return True, f"{old_key} replaced with {new_key}"

        # Check if any update-node entries are related to a change in search keys.
        for old_key, new_key in updates:
            if old_key in old_keys and new_key in new_keys:
                return True, f"{old_key} replaced with {new_key}"

        # If no changes were found, return False.
        return False, None

    def method_deleted_in_diff(self, method):
        pattern_delete_tree = f"delete-tree\n---\ntrailer.*\n.*name: {method}"
        pattern_delete_node = f"delete-node\n---\n.*\n.*name: {method}"
        if re.search(
            pattern_delete_tree, self.textdiff.decode("utf-8"), re.DOTALL
        ) or re.search(pattern_delete_node, self.textdiff.decode("utf-8"), re.DOTALL):
            return True
        return False

    def find_added_methods(self):
        new_code = self.read_file(self.new_code_path)
        old_code = self.read_file(self.old_code_path)
        # method = methodname + ( or "." + methodname + (
        new_methods = re.findall(r"(\w+)\(", new_code)
        old_methods = re.findall(r"(\w+)\(", old_code)
        print(f"New methods: {new_methods}")
        print(f"Old methods: {old_methods}")
        print(f"Added methods: {set(new_methods) - set(old_methods)}")
        added_methods = set(new_methods) - set(old_methods)
        return added_methods

    def find_methods_in_code(self, code_path):
        code = self.read_file(code_path)

        # Find all methods in the code
        methods = re.findall(r"(\w+)\(", code)

        return set(methods)

    def find_updated_identifiers(self):
        new_code = self.read_file(self.new_code_path)
        old_code = self.read_file(self.old_code_path)

        new_identifiers = re.findall(r"(\w+)", new_code)
        new_function_identifiers = re.findall(r"(\w+)\(", new_code)
        new_identifiers = list(set(new_identifiers) - set(new_function_identifiers))
        old_identifiers = re.findall(r"(\w+)", old_code)
        old_function_identifiers = re.findall(r"(\w+)\(", old_code)
        old_identifiers = list(set(old_identifiers) - set(old_function_identifiers))

        # print(f"New identifiers: {new_identifiers}")
        # print(f"Old identifiers: {old_identifiers}")

        updated_identifiers = set(new_identifiers) - set(old_identifiers)
        return updated_identifiers

    def read_file(self, file_path):
        with open(file_path, "r") as f:
            return f.read()


if __name__ == "__main__":
    old_code = "file1.py"
    new_code = "file2.py"
    gumtree_bin_path = GUMTREE_BIN

    epm = EditPatternClassifier(old_code, new_code, gumtree_bin_path)
    epm.run_gumtree()
    print(epm.analyze())
