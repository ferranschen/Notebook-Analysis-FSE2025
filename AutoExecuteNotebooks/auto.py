import os
import asyncio
import nbformat
from nbclient import NotebookClient
import nest_asyncio

# Directories for original and executed notebooks
original_dir = "original"
executed_dir = "executed"

# Create the executed directory if it does not exist
os.makedirs(executed_dir, exist_ok=True)

# Apply nest_asyncio to enable nested event loops
nest_asyncio.apply()

# Define an asynchronous function to execute the cells


async def execute_notebook(notebook_path):
    # Read the input notebook
    with open(notebook_path) as f:
        nb = nbformat.read(f, as_version=4)

    # Create a NotebookClient object
    client = NotebookClient(nb)
    client.allow_errors = True
    client.timeout = 120  # Set the cell execution timeout to 120 seconds

    # Execute cells in the original order while handling errors
    try:
        await client.async_execute()
    except Exception as e:
        print(f"Error executing notebook {notebook_filename}: {str(e)}")

    return client.nb

# Iterate over the files in the original directory
for notebook_filename in os.listdir(original_dir):
    # Check if the file is a Jupyter notebook
    if notebook_filename.endswith(".ipynb") and (notebook_filename not in os.listdir(executed_dir)):
        input_notebook = os.path.join(original_dir, notebook_filename)
        output_notebook = os.path.join(executed_dir, notebook_filename)

        # Run the asynchronous function
        executed_nb = asyncio.run(execute_notebook(input_notebook))

        # Save the executed notebook
        with open(output_notebook, 'w') as f:
            nbformat.write(executed_nb, f)

        print(f"Executed and saved: {notebook_filename}")
