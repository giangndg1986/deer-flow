# src/tools/file_tools.py

import os
import logging
import threading
from datetime import datetime
from typing import Annotated, Optional, Dict
from langchain_core.tools import tool
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# Use ContextVar for better async support (recommended for web apps)
current_session_id: ContextVar[Optional[str]] = ContextVar('current_session_id', default=None)

# Thread-safe storage for project folders per session/thread
_project_folders: Dict[str, str] = {}
_lock = threading.Lock()

def set_session_id(session_id: str):
    """Set the session ID for the current context (call this in your web handler)"""
    current_session_id.set(session_id)

def get_session_id() -> str:
    """Get the session identifier for the current context"""
    session_id = current_session_id.get()
    if session_id is None:
        # Fallback to thread ID if no session ID is set
        session_id = str(threading.get_ident())
        logger.warning(f"No session ID set, using thread ID: {session_id}")
    return session_id

def get_or_create_project_folder(project_name: str, session_id: Optional[str] = None) -> str:
    """Get existing project folder or create new one with timestamp for specific session"""
    if session_id is None:
        session_id = get_session_id()

    # Clean project name to be filesystem-safe
    clean_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    clean_name = clean_name.replace(' ', '_').lower()

    with _lock:
        # Check if we already have a project folder for this session
        session_key = f"{session_id}_{clean_name}"
        if session_key in _project_folders:
            return _project_folders[session_key]

        # Generate new timestamped folder name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Add session_id suffix to avoid conflicts between concurrent users
        # Use first 8 chars of session_id for uniqueness but readability
        session_suffix = session_id[:8] if len(session_id) >= 8 else session_id
        folder_name = f"{clean_name}_{timestamp}_{session_suffix}"

        # Store for reuse in this session
        _project_folders[session_key] = folder_name

        logger.info(f"Created new project folder: {folder_name} for session: {session_id}")
        return folder_name

def reset_project_session(session_id: Optional[str] = None):
    """Reset the current project session for specific session"""
    if session_id is None:
        session_id = get_session_id()

    with _lock:
        # Remove all project folders for this session
        keys_to_remove = [key for key in _project_folders.keys() if key.startswith(f"{session_id}_")]
        for key in keys_to_remove:
            del _project_folders[key]

@tool
def create_file_tool(
    file_path: Annotated[str, "The relative path where the file should be created"],
    content: Annotated[str, "The content to write to the file"],
    project_name: Annotated[str, "The project name for folder generation"] = "generated_project"
) -> str:
    """Create a file with the specified content in the output directory with timestamp."""
    try:
        session_id = get_session_id()

        # Get or create project folder (reuses existing folder in same session)
        project_folder = get_or_create_project_folder(project_name, session_id)

        # Create the full path: output/project_name_timestamp_sessionid/file_path
        base_path = os.path.join(os.getcwd(), "output", project_folder)
        os.makedirs(base_path, exist_ok=True)

        # Create the full file path
        full_path = os.path.join(base_path, file_path)

        # Create directory if it doesn't exist
        file_dir = os.path.dirname(full_path)
        if file_dir:  # Only create if there's a directory component
            os.makedirs(file_dir, exist_ok=True)

        # Write the file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Created file: {full_path} for session: {session_id}")
        return f"Successfully created file: {file_path} in project folder: output/{project_folder}"

    except Exception as e:
        error_msg = f"Error creating file {file_path}: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool
def create_folder_tool(
    folder_path: Annotated[str, "The relative path of the folder to create"],
    project_name: Annotated[str, "The project name for folder generation"] = "generated_project"
) -> str:
    """Create a folder in the output directory with timestamp."""
    try:
        session_id = get_session_id()

        # Get or create project folder (reuses existing folder in same session)
        project_folder = get_or_create_project_folder(project_name, session_id)

        # Create the full path: output/project_name_timestamp_sessionid/folder_path
        base_path = os.path.join(os.getcwd(), "output", project_folder)
        full_path = os.path.join(base_path, folder_path)

        os.makedirs(full_path, exist_ok=True)

        logger.info(f"Created folder: {full_path} for session: {session_id}")
        return f"Successfully created folder: {folder_path} in project folder: output/{project_folder}"

    except Exception as e:
        error_msg = f"Error creating folder {folder_path}: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool
def list_project_structure_tool(
    project_name: Annotated[str, "The project name to list structure for"] = "generated_project"
) -> str:
    """List the current project structure in the output directory."""
    try:
        session_id = get_session_id()

        # Get current project folder
        project_folder = get_or_create_project_folder(project_name, session_id)
        base_path = os.path.join(os.getcwd(), "output", project_folder)

        if not os.path.exists(base_path):
            return f"Project folder '{project_folder}' does not exist yet."

        structure = [f"Project structure for: output/{project_folder}/"]

        for root, dirs, files in os.walk(base_path):
            level = root.replace(base_path, '').count(os.sep)
            indent = '  ' * level
            folder_name = os.path.basename(root) if level > 0 else ""
            if folder_name:
                structure.append(f"{indent}{folder_name}/")

            subindent = '  ' * (level + 1)
            for file in files:
                structure.append(f"{subindent}{file}")

        return '\n'.join(structure)

    except Exception as e:
        error_msg = f"Error listing project structure: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool
def get_current_project_path_tool(
    project_name: Annotated[str, "The project name to get path for"] = "generated_project"
) -> str:
    """Get the current project path for reference."""
    try:
        session_id = get_session_id()

        # Get current project folder
        project_folder = get_or_create_project_folder(project_name, session_id)
        full_path = os.path.join(os.getcwd(), "output", project_folder)

        return f"Current project path: {full_path}"

    except Exception as e:
        error_msg = f"Error getting project path: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool
def start_new_project_tool(
    project_name: Annotated[str, "The name for the new project"] = "new_project"
) -> str:
    """Start a new project session (creates a new timestamped folder)."""
    try:
        session_id = get_session_id()

        # Reset the current session
        reset_project_session(session_id)

        # Create new project folder
        project_folder = get_or_create_project_folder(project_name, session_id)
        base_path = os.path.join(os.getcwd(), "output", project_folder)
        os.makedirs(base_path, exist_ok=True)

        logger.info(f"Started new project: {project_folder} for session: {session_id}")
        return f"Started new project session: output/{project_folder}"

    except Exception as e:
        error_msg = f"Error starting new project: {str(e)}"
        logger.error(error_msg)
        return error_msg


# Optional: Cleanup function for old sessions (can be called periodically)
def cleanup_old_sessions(max_age_hours: int = 24):
    """Clean up old session data to prevent memory leaks"""
    # This is a simple cleanup - in production you might want more sophisticated logic
    with _lock:
        # For now, just limit the total number of stored sessions
        if len(_project_folders) > 100:  # Arbitrary limit
            # Remove oldest half of sessions (simple FIFO)
            items = list(_project_folders.items())
            items_to_keep = items[50:]  # Keep newest 50
            _project_folders.clear()
            _project_folders.update(items_to_keep)
            logger.info(f"Cleaned up old sessions, kept {len(_project_folders)} sessions")