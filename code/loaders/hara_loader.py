# loaders/hara_loader.py
# Main HARA loading orchestration with multiple source support

import os
from typing import Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.models import HaraData
from parsers.excel_parser import ExcelHARAParser
from parsers.csv_parser import CSVHARAParser
from parsers.text_parser import TextHARAParser


class HARALoader:
    """
    Main HARA loader that orchestrates loading from multiple sources.
    
    Search priority:
    1. Working memory (if HARA just generated)
    2. hara_inputs/ folder (uploaded files)
    3. generated_documents/ folder (recently generated HARA)
    """
    
    def __init__(self, plugin_folder: str):
        """
        Initialize HARA loader.
        
        Args:
            plugin_folder: Path to plugin root folder
        """
        self.plugin_folder = plugin_folder
        self.hara_inputs_folder = os.path.join(plugin_folder, "hara_inputs")
        self.generated_folder = os.path.join(
            plugin_folder, "..", "AI_Agent-HARA_Assistant", "generated_documents"
        )
    
    def load_hara(self, item_name: str, cat) -> Optional[HaraData]:
        """
        Find and load HARA data for FSC development.
        
        Args:
            item_name: Name of the item/system to find HARA for
            cat: Cheshire Cat instance with working memory
            
        Returns:
            HaraData object if found, None otherwise
        """
        # SOURCE 1: Check Working Memory
        hara_data = self._load_from_working_memory(cat, item_name)
        if hara_data:
            return hara_data
        
        # SOURCE 2: Check hara_inputs/ folder
        hara_data = self._load_from_hara_inputs_folder(item_name)
        if hara_data:
            return hara_data
        
        # SOURCE 3: Check generated_documents/ folder
        hara_data = self._load_from_generated_documents(item_name)
        if hara_data:
            return hara_data
        
        return None
    
    def _load_from_working_memory(self, cat, item_name: str) -> Optional[HaraData]:
        """
        Load HARA from working memory (recently generated).
        
        Args:
            cat: Cheshire Cat instance
            item_name: Item name
            
        Returns:
            HaraData object or None
        """
        # Implementation would check cat.working_memory for safety goals
        # This is a placeholder - actual implementation depends on Cat framework
        return None
    
    def _load_from_hara_inputs_folder(self, item_name: str) -> Optional[HaraData]:
        """
        Load HARA from hara_inputs/ folder.
        
        Args:
            item_name: Item name
            
        Returns:
            HaraData object or None
        """
        # Create folder if it doesn't exist
        if not os.path.exists(self.hara_inputs_folder):
            os.makedirs(self.hara_inputs_folder)
        
        # Search for HARA files
        hara_files = self._find_hara_files(self.hara_inputs_folder, item_name)
        
        if hara_files:
            for hara_file in hara_files:
                hara_data = self._parse_file(hara_file, item_name)
                if hara_data:
                    return hara_data
        
        return None
    
    def _load_from_generated_documents(self, item_name: str) -> Optional[HaraData]:
        """
        Load HARA from generated_documents/ folder.
        
        Args:
            item_name: Item name
            
        Returns:
            HaraData object or None
        """
        if os.path.exists(self.generated_folder):
            hara_files = self._find_hara_files(self.generated_folder, item_name)
            
            if hara_files:
                for hara_file in hara_files:
                    hara_data = self._parse_file(hara_file, item_name)
                    if hara_data:
                        return hara_data
        
        return None
    
    def _find_hara_files(self, folder_path: str, item_name: str) -> list:
        """
        Find HARA files in a folder that match the item name.
        
        Args:
            folder_path: Path to folder to search
            item_name: Item name to match
            
        Returns:
            List of file paths, sorted by modification time (newest first)
        """
        if not os.path.exists(folder_path):
            return []
        
        matching_files = []
        item_name_normalized = item_name.lower().replace(" ", "_").replace("-", "_")
        
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            if not os.path.isfile(file_path):
                continue
            
            # Check file extension
            _, ext = os.path.splitext(filename.lower())
            if ext not in ['.xlsx', '.xls', '.csv', '.txt']:
                continue
            
            # Check if filename matches
            filename_normalized = filename.lower().replace(" ", "_").replace("-", "_")
            
            if (item_name_normalized in filename_normalized or 
                'hara' in filename_normalized or 
                'hazard' in filename_normalized):
                
                matching_files.append(file_path)
        
        # Sort by modification time (newest first)
        matching_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        return matching_files
    
    def _parse_file(self, file_path: str, item_name: str) -> Optional[HaraData]:
        """
        Parse HARA file using appropriate parser.
        
        Args:
            file_path: Path to HARA file
            item_name: Item name for the system
            
        Returns:
            HaraData object or None if parsing fails
        """
        _, ext = os.path.splitext(file_path.lower())
        
        try:
            # Select parser based on file extension
            if ext in ['.xlsx', '.xls']:
                parser = ExcelHARAParser(file_path, item_name)
            elif ext == '.csv':
                parser = CSVHARAParser(file_path, item_name)
            elif ext == '.txt':
                parser = TextHARAParser(file_path, item_name)
            else:
                return None
            
            # Check if parser can handle the file
            if not parser.can_parse():
                return None
            
            # Parse the file
            return parser.parse()
            
        except Exception as e:
            # Log error but don't raise - try next file
            print(f"Error parsing {file_path}: {e}")
            return None


# ====================================================================================
# Convenience function for backward compatibility
# ====================================================================================

def find_hara_data(cat, item_name: str) -> Optional[HaraData]:
    """
    Convenience function to maintain backward compatibility.
    
    Args:
        cat: Cheshire Cat instance
        item_name: Name of the item/system
        
    Returns:
        HaraData object or None
    """
    plugin_folder = os.path.dirname(__file__)
    loader = HARALoader(plugin_folder)
    return loader.load_hara(item_name, cat)