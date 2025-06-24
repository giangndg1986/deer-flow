# src/tools/file_tools.py

import os
import logging
from typing import Annotated
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

@tool
def create_file_tool(
    file_path: Annotated[str, "The relative path where the file should be created"],
    content: Annotated[str, "The content to write to the file"],
    project_folder: Annotated[str, "The base project folder name"] = "generated_project"
) -> str:
    """Create a file with the specified content in the project directory."""
    try:
        # Ensure the project folder exists
        base_path = os.path.join(os.getcwd(), project_folder)
        os.makedirs(base_path, exist_ok=True)

        # Create the full file path
        full_path = os.path.join(base_path, file_path)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Write the file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Created file: {full_path}")
        return f"Successfully created file: {file_path}"

    except Exception as e:
        error_msg = f"Error creating file {file_path}: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool
def create_folder_tool(
    folder_path: Annotated[str, "The relative path of the folder to create"],
    project_folder: Annotated[str, "The base project folder name"] = "generated_project"
) -> str:
    """Create a folder in the project directory."""
    try:
        # Create the full folder path
        base_path = os.path.join(os.getcwd(), project_folder)
        full_path = os.path.join(base_path, folder_path)

        os.makedirs(full_path, exist_ok=True)

        logger.info(f"Created folder: {full_path}")
        return f"Successfully created folder: {folder_path}"

    except Exception as e:
        error_msg = f"Error creating folder {folder_path}: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool
def list_project_structure_tool(
    project_folder: Annotated[str, "The base project folder name"] = "generated_project"
) -> str:
    """List the current project structure."""
    try:
        base_path = os.path.join(os.getcwd(), project_folder)

        if not os.path.exists(base_path):
            return f"Project folder '{project_folder}' does not exist yet."

        structure = []
        for root, dirs, files in os.walk(base_path):
            level = root.replace(base_path, '').count(os.sep)
            indent = ' ' * 2 * level
            structure.append(f"{indent}{os.path.basename(root)}/")

            subindent = ' ' * 2 * (level + 1)
            for file in files:
                structure.append(f"{subindent}{file}")

        return "Current project structure:\n" + '\n'.join(structure)

    except Exception as e:
        error_msg = f"Error listing project structure: {str(e)}"
        logger.error(error_msg)
        return error_msg