#!/usr/bin/env python3
"""
CurseForge mod updater script.
Scans a folder for mod files, checks for updates via CurseForge API, and downloads newer versions.
"""

import os
import sys
from pathlib import Path
import requests
import murmurhash2


def calculate_fingerprint(filepath):
    """Calculate CurseForge fingerprint for a mod file."""
    try:
        with open(filepath, "rb") as f:
            # CurseForge ignores whitespace characters: 0x9, 0xa, 0xd, 0x20
            content = f.read()
            filtered = bytearray(b for b in content if b not in [0x9, 0xa, 0xd, 0x20])
            return murmurhash2.murmurhash2(bytes(filtered), seed=1)
    except Exception as e:
        print(f"Error calculating fingerprint for {filepath}: {e}")
        return None

if __name__ == "__main__":
    # Init and check vars
    updated_mods = []
    mod_data = {}
    
    api_key = os.environ.get("CURSEFORGE_API_KEY")
    if not api_key:
        print("Error: CURSEFORGE_API_KEY is not set in .env file. Please check .env.example for example values.")
        sys.exit(1)

    game_id = os.environ.get("GAME_ID")
    if not game_id:
        print("ERROR: GAME_ID is not set in the .env file.  Please check .env.example for example values.")
        sys.exit(1)
    
    if len(sys.argv) < 2 or not sys.argv[1]:
        print(f"Usage: {sys.argv[0]} <mod_folder>")
        sys.exit(1)
    mod_folder = sys.argv[1]
    
    # Get filepaths of all .jar and .zip files in mod folder
    print(f"Scanning mod folder: {mod_folder}")
    mod_filepaths = []
    for pattern in ["*.jar", "*.zip"]:
        mod_filepaths.extend(Path(mod_folder).rglob(pattern))
    
    # Generate fingerprints for found mod files
    for mod_filepath in mod_filepaths:
        if mod_filepath.is_file():
            print(f"Processing mod file: {mod_filepath}")
            mod_filename = mod_filepath.name
            
            print(f"Calculating fingerprint for: {mod_filename}...")
            fingerprint = str(calculate_fingerprint(str(mod_filepath)))
            
            if fingerprint is not None:
                # Check if fingerprint already exists
                if fingerprint in mod_data:
                    print("ERROR: Fingerprint collision detected!  This should not happen.")
                    print(f"  Fingerprint: {fingerprint}")
                    print(f"  Existing file: {mod_data[fingerprint]}")
                    print(f"  New file: {mod_filepath}")
                    print("  These mods are likely to be duplicates with different filenames or zero bytes in size due to a transfer issue.")
                    sys.exit(1)
                mod_data[fingerprint] = str(mod_filepath)
            else:
                print(f"Error: Could not calculate fingerprint for {mod_filename}.")
                sys.exit(1)
    
    fingerprints = list(mod_data.keys())
    if not fingerprints:
        print("No fingerprints were generated. Exiting.")
        sys.exit(1)
    
    # Match fingerprints
    print("Querying CurseForge API for found fingerprints...")
    headers = {
        "Accept": "application/json",
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    fingerprint_data = {"fingerprints": [int(fp) for fp in fingerprints]}
    
    try:
        response = requests.post(
            f"https://api.curseforge.com/v1/fingerprints/{game_id}",
            headers=headers,
            json=fingerprint_data
        )
        response.raise_for_status()
        fingerprint_response = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying CurseForge API: {e}")
        sys.exit(1)
    
    # Check for unmatched fingerprints
    print("Checking for unmatched fingerprints...")
    unmatched = fingerprint_response.get("data", {}).get("unmatchedFingerprints")
    if unmatched:
        print("Error: Some fingerprints did not match any mods on CurseForge.")
        print(f"Unmatched fingerprints: {', '.join(map(str, unmatched))}")
        sys.exit(1)
    else:
        print("No unmatched fingerprints found.")
    
    # Check for partial matches
    print("Checking for partial matches...")
    partial_matches = fingerprint_response.get("data", {}).get("partialMatches", [])
    if not partial_matches:
        print("No partial matches found.")
    else:
        print("Partial matches found:")
        for partial in partial_matches:
            partial_fingerprint = str(partial.get("fileFingerprint"))
            partial_mod_id = partial.get("id")
            partial_filename = Path(mod_data.get(partial_fingerprint, "")).name
            print(f"- Mod ID: {partial_mod_id} for file {partial_filename} did not match exactly.")
            sys.exit(1)
    
    # Check for exact matches
    print("Checking for exact matches...")
    exact_matches = fingerprint_response.get("data", {}).get("exactMatches", [])
    if not exact_matches:
        print("No mods found on CurseForge for the provided fingerprints.")
    if len(exact_matches) < len(fingerprints):
        print("ERROR: No unmatched or partial matches, but not all fingerprints matched exactly. This should not happen.")
        sys.exit(1)
    
    # Check for updates and download latest versions
    print("Checking for updates for matched mods...")
    for match in exact_matches:
        mod_id = match.get("id")
        latest_files = match.get("latestFiles", [])
        
        if not latest_files:
            continue
            
        latest_file = latest_files[0]
        latest_filename = latest_file.get("fileName")
        original_fingerprint = str(match.get("file", {}).get("fileFingerprint"))
        
        original_filepath = mod_data.get(original_fingerprint)
        if not original_filepath or not Path(original_filepath).exists():
            print(f"Could not find original file for fingerprint {original_fingerprint}. This should not happen.")
            sys.exit(1)
        
        original_filename = Path(original_filepath).name
        if not original_filename:
            print(f"Could not determine original filename from path {original_filepath}.")
            sys.exit(1)
        
        if latest_filename == original_filename:
            print(f"Mod {original_filename} is already up to date.")
            continue
        else:
            print(f"Found update for {original_filename}. New version is {latest_filename}.")
            latest_download_url = latest_file.get("downloadUrl")
            
            if not latest_download_url or latest_download_url == "null":
                print(f"No download URL found for the latest version of mod ID {mod_id}")
                print("Downloading file using file ID instead...")
                file_id = latest_file.get("id")
                latest_download_url = f"https://api.curseforge.com/v1/mods/{mod_id}/files/{file_id}"
                
                if not latest_download_url or latest_download_url == "null":
                    print(f"Error: Could not construct download URL for mod ID {mod_id} file ID {file_id}.")
                    sys.exit(1)
            
            print(f"Downloading latest version of mod ID {mod_id}...")
            try:
                download_response = requests.get(latest_download_url, allow_redirects=True)
                download_response.raise_for_status()
                
                new_filepath = Path(mod_folder) / latest_filename
                with open(new_filepath, "wb") as f:
                    f.write(download_response.content)
                
                print(f"Downloaded latest mod to {new_filepath}")
                updated_mods.append(f"{original_filename} updated to {latest_filename}")
                
                # Remove old mod file
                Path(original_filepath).unlink()
                print(f"Removed old mod file: {original_filepath}")
            except requests.exceptions.RequestException as e:
                print(f"Error downloading mod: {e}")
                sys.exit(1)
    
    print("Update process completed.")
    if not updated_mods:
        print("All mods are already up to date.")
    else:
        print("Updated mods:")
        for mod in updated_mods:
            print(f"- {mod}")
    
    sys.exit(0)
