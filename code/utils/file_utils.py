"""
File Utilities for FSC Developer Plugin
Handles file operations including reading, writing, and searching for files
"""

import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import shutil
from datetime import datetime
import logging

# Setup logging
log = logging.getLogger(__name__)


def get_plugin_path() -> Path:
    """
    Get the root path of the plugin directory.
    
    Returns:
        Path: The plugin root directory path
    """
    # Go up three levels: file_utils.py -> utils/ -> code/ -> plugin_root/
    return Path(__file__).parent.parent.parent


def get_hara_inputs_path() -> Path:
    """
    Get the path to the HARA inputs directory.
    
    Returns:
        Path: Path to hara_inputs folder
    """
    return get_plugin_path() / "hara_inputs"


def get_output_path() -> Path:
    """
    Get the path to the generated documents directory.
    
    Returns:
        Path: Path to generated_documents folder
    """
    return get_plugin_path() / "generated_documents"


def get_templates_path() -> Path:
    """
    Get the path to the templates directory.
    
    Returns:
        Path: Path to templates folder
    """
    return get_plugin_path() / "templates"


def ensure_directory_exists(directory_path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        Path: The directory path
    """
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def find_files_by_extension(directory: Union[str, Path], extension: str) -> List[Path]:
    """
    Find all files with a specific extension in a directory.
    
    Args:
        directory: Directory to search
        extension: File extension (e.g., '.xlsx', '.csv', '.txt')
        
    Returns:
        List of Path objects for matching files
    """
    path = Path(directory)
    if not path.exists():
        return []
    
    # Normalize extension
    if not extension.startswith('.'):
        extension = f'.{extension}'
    
    return list(path.glob(f'*{extension}'))


def find_hara_files() -> Dict[str, List[Path]]:
    """
    Find all HARA input files in the hara_inputs directory.
    
    Returns:
        Dictionary with file types as keys and lists of file paths as values
    """
    hara_path = get_hara_inputs_path()
    
    if not hara_path.exists():
        return {}
    
    return {
        'excel': find_files_by_extension(hara_path, '.xlsx') + find_files_by_extension(hara_path, '.xls'),
        'csv': find_files_by_extension(hara_path, '.csv'),
        'text': find_files_by_extension(hara_path, '.txt') + find_files_by_extension(hara_path, '.md')
    }


def read_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
    """
    Read the contents of a text file.
    
    Args:
        file_path: Path to the file
        encoding: File encoding (default: utf-8)
        
    Returns:
        File contents as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Error reading file {file_path}: {str(e)}")


def write_file(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
    """
    Write content to a text file.
    
    Args:
        file_path: Path to the file
        content: Content to write
        encoding: File encoding (default: utf-8)
        
    Returns:
        True if successful
        
    Raises:
        IOError: If file cannot be written
    """
    path = Path(file_path)
    
    # Ensure parent directory exists
    ensure_directory_exists(path.parent)
    
    try:
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        raise IOError(f"Error writing file {file_path}: {str(e)}")


def read_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON content as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    content = read_file(file_path)
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {str(e)}", e.doc, e.pos)


def write_json(file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> bool:
    """
    Write data to a JSON file.
    
    Args:
        file_path: Path to the JSON file
        data: Data to write
        indent: JSON indentation (default: 2)
        
    Returns:
        True if successful
    """
    content = json.dumps(data, indent=indent, ensure_ascii=False)
    return write_file(file_path, content)


def backup_file(file_path: Union[str, Path]) -> Optional[Path]:
    """
    Create a backup copy of a file with timestamp.
    
    Args:
        file_path: Path to the file to backup
        
    Returns:
        Path to backup file, or None if original doesn't exist
    """
    path = Path(file_path)
    
    if not path.exists():
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.parent / f"{path.stem}_backup_{timestamp}{path.suffix}"
    
    try:
        shutil.copy2(path, backup_path)
        return backup_path
    except Exception as e:
        print(f"Warning: Could not create backup of {file_path}: {str(e)}")
        return None


def list_generated_documents() -> List[Dict[str, Any]]:
    """
    List all generated documents with metadata.
    
    Returns:
        List of dictionaries containing document info
    """
    output_path = get_output_path()
    
    if not output_path.exists():
        return []
    
    documents = []
    for file_path in output_path.iterdir():
        if file_path.is_file():
            stat = file_path.stat()
            documents.append({
                'name': file_path.name,
                'path': str(file_path),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'extension': file_path.suffix
            })
    
    # Sort by modification time, newest first
    documents.sort(key=lambda x: x['modified'], reverse=True)
    
    return documents


def generate_unique_filename(base_name: str, extension: str, directory: Optional[Union[str, Path]] = None) -> Path:
    """
    Generate a unique filename by adding a counter if file exists.
    
    Args:
        base_name: Base filename without extension
        extension: File extension (with or without dot)
        directory: Directory path (default: generated_documents)
        
    Returns:
        Unique file path
    """
    if directory is None:
        directory = get_output_path()
    
    directory = Path(directory)
    ensure_directory_exists(directory)
    
    # Normalize extension
    if not extension.startswith('.'):
        extension = f'.{extension}'
    
    # Try without counter first
    file_path = directory / f"{base_name}{extension}"
    if not file_path.exists():
        return file_path
    
    # Add counter
    counter = 1
    while True:
        file_path = directory / f"{base_name}_{counter}{extension}"
        if not file_path.exists():
            return file_path
        counter += 1


def clean_old_backups(directory: Union[str, Path], days_old: int = 7) -> int:
    """
    Remove backup files older than specified days.
    
    Args:
        directory: Directory to clean
        days_old: Remove backups older than this many days
        
    Returns:
        Number of files deleted
    """
    directory = Path(directory)
    if not directory.exists():
        return 0
    
    cutoff_time = datetime.now().timestamp() - (days_old * 86400)
    deleted_count = 0
    
    for file_path in directory.glob('*_backup_*'):
        if file_path.stat().st_mtime < cutoff_time:
            try:
                file_path.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"Warning: Could not delete {file_path}: {str(e)}")
    
    return deleted_count


def get_file_info(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information, or None if file doesn't exist
    """
    path = Path(file_path)
    
    if not path.exists():
        return None
    
    stat = path.stat()
    
    return {
        'name': path.name,
        'path': str(path.absolute()),
        'size': stat.st_size,
        'size_mb': round(stat.st_size / (1024 * 1024), 2),
        'created': datetime.fromtimestamp(stat.st_ctime),
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'extension': path.suffix,
        'is_file': path.is_file(),
        'is_directory': path.is_dir()
    }


def safe_filename(filename: str) -> str:
    """
    Convert a string to a safe filename by removing/replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename string
    """
    # Characters to remove or replace
    invalid_chars = '<>:"/\\|?*'
    
    # Replace invalid characters with underscore
    safe_name = ''.join(c if c not in invalid_chars else '_' for c in filename)
    
    # Remove leading/trailing spaces and dots
    safe_name = safe_name.strip('. ')
    
    # Limit length
    if len(safe_name) > 200:
        safe_name = safe_name[:200]
    
    return safe_name if safe_name else 'unnamed'