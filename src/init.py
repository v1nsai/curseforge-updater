#!/usr/bin/env python3
"""
CurseForge mod updater script.
Scans a folder for mod files, checks for updates via CurseForge API, and downloads newer versions.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv('../.env')

from functions import *

if __name__ == "__main__":
    # Init and check vars
    mod_data = {}
    api_key = os.environ.get("CURSEFORGE_API_KEY")
    if not api_key:
        raise ValueError("CURSEFORGE_API_KEY is not set. Please check your environment variables.")

    game_id = os.environ.get("GAME_ID")
    if not game_id:
        raise ValueError("GAME_ID is not set. Please check your environment variables.")
    if len(sys.argv) < 2 or not sys.argv[1]:
        raise ValueError("Usage: {sys.argv[0]} <mod_folder>")
    mod_folder = sys.argv[1]
    
    # Get filepaths of all .jar and .zip files in mod folder
    print(f"Scanning mod folder: {mod_folder}")
    mod_filepaths = []
    for pattern in ["*.jar", "*.zip"]:
        mod_filepaths.extend(Path(mod_folder).rglob(pattern))
    
    # Generate fingerprints for found mod files
    for mod_filepath in mod_filepaths:
        if mod_filepath.is_file():
            mod_data = generate_fingerprint(mod_filepath, mod_data)
    fingerprints = list(mod_data.keys())
    if not fingerprints:
        raise ValueError("No fingerprints were generated. No mod files found or all fingerprint calculations failed.")
    
    # Match fingerprints with CurseForge mods
    fingerprint_response = query_fingerprints(fingerprints, api_key, game_id)
    exact_matches = verify_fingerprint_matches(fingerprint_response, mod_data, fingerprints)
    
    # Check for updates and download latest versions
    print("Checking for updates for matched mods...")
    updated_mods = []
    archived_mods = []
    for match in exact_matches:
        result = update_mod(match, mod_data, mod_folder)
        if result:
            updated_mods.append(result)
    
    print("Update process completed.")
    if not updated_mods:
        print("All mods are already up to date.")
    else:
        print("Updated mods:")
        for mod in updated_mods:
            print(f"- {mod}")
    if archived_mods:
        print("Archived mods (should be deleted):")
        for mod in archived_mods:
            print(f"- {mod}")
        
    sys.exit(0)
