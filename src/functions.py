import sys
import murmurhash2
import requests

from pathlib import Path

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

def generate_fingerprint(mod_filepath, mod_data):
    print(f"Processing mod file: {mod_filepath}")
    mod_filename = mod_filepath.name
    
    print(f"Calculating fingerprint for: {mod_filename}...")
    fingerprint = str(calculate_fingerprint(str(mod_filepath)))
    
    if fingerprint is not None:
        # Check if fingerprint already exists
        if fingerprint in mod_data:
            raise RuntimeError(
                f"Fingerprint collision detected! This should not happen.\n"
                f"  Fingerprint: {fingerprint}\n"
                f"  Existing file: {mod_data[fingerprint]}\n"
                f"  New file: {mod_filepath}\n"
                f"  These mods are likely to be duplicates with different filenames or zero bytes in size due to a transfer issue."
            )
        mod_data[fingerprint] = str(mod_filepath)
        return mod_data
    else:
        raise RuntimeError(f"Could not calculate fingerprint for {mod_filename}.")

def query_fingerprints(fingerprints, api_key, game_id):
    print("Querying CurseForge API for found fingerprints...")
    headers = {
        "Accept": "application/json",
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    fingerprint_request_data = {"fingerprints": [int(fp) for fp in fingerprints]}
    try:
        response = requests.post(
            f"https://api.curseforge.com/v1/fingerprints/{game_id}",
            headers=headers,
            json=fingerprint_request_data
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error querying CurseForge API: {e}") from e

def verify_fingerprint_matches(fingerprint_response, mod_data, fingerprints):
    # Check for unmatched fingerprints
    print("Checking for unmatched fingerprints...")
    unmatched = fingerprint_response.get("data", {}).get("unmatchedFingerprints")
    if unmatched:
        raise ValueError(
            f"Some fingerprints did not match any mods on CurseForge.\n"
            f"Unmatched fingerprints: {', '.join(map(str, unmatched))}"
        )
    else:
        print("No unmatched fingerprints found.")
    
    # Check for partial matches
    print("Checking for partial matches...")
    partial_matches = fingerprint_response.get("data", {}).get("partialMatches", [])
    if not partial_matches:
        print("No partial matches found.")
    else:
        partial_details = []
        for partial in partial_matches:
            partial_fingerprint = str(partial.get("fileFingerprint"))
            partial_mod_id = partial.get("id")
            partial_filename = Path(mod_data.get(partial_fingerprint, "")).name
            partial_details.append(f"- Mod ID: {partial_mod_id} for file {partial_filename} did not match exactly.")
        raise ValueError(
            f"Partial matches found:\n" + "\n".join(partial_details)
        )
    
    # Check that exact matches cover all fingerprints
    print("Checking for exact matches...")
    exact_matches = fingerprint_response.get("data", {}).get("exactMatches", [])
    if not exact_matches:
        print("No mods found on CurseForge for the provided fingerprints.")
    if len(exact_matches) < len(fingerprints):
        raise RuntimeError(
            "No unmatched or partial matches, but not all fingerprints matched exactly. This should not happen."
        )
    return exact_matches

def update_mod(match, mod_data, mod_folder):
    mod_id = match.get("id")
    latest_files = match.get("latestFiles", [])
    
    if not latest_files:
        raise ValueError(f"No latest files found for mod ID {mod_id}.")
        
    latest_file = latest_files[0]
    latest_filename = latest_file.get("fileName")
    original_fingerprint = str(match.get("file", {}).get("fileFingerprint"))
    
    original_filepath = mod_data.get(original_fingerprint)
    if not original_filepath or not Path(original_filepath).exists():
        raise FileNotFoundError(
            f"Could not find original file for fingerprint {original_fingerprint}. This should not happen."
        )
    
    original_filename = Path(original_filepath).name
    if not original_filename:
        raise ValueError(f"Could not determine original filename from path {original_filepath}.")
    
    if latest_filename == original_filename:
        print(f"Mod {original_filename} is already up to date.")
        return None
    else:
        print(f"Found update for {original_filename}. New version is {latest_filename}.")
        latest_download_url = latest_file.get("downloadUrl")
        
        if not latest_download_url or latest_download_url == "null":
            print(f"No download URL found for the latest version of mod ID {mod_id}")
            print("Constructing download URL directly from CurseForge CDN...")
            file_id = str(latest_file.get("id"))
            id_prefix = file_id[:4]
            id_suffix = file_id[4:]
            latest_download_url = f"https://edge.forgecdn.net/files/{id_prefix}/{id_suffix}/{latest_filename}"
            print(f"Constructed download URL: {latest_download_url}")
        
        print(f"Downloading latest version of mod ID {mod_id}...")
        try:
            download_response = requests.get(latest_download_url, allow_redirects=True)
            download_response.raise_for_status()
            
            new_filepath = Path(mod_folder) / latest_filename
            with open(new_filepath, "wb") as f:
                f.write(download_response.content)
            print(f"Downloaded latest mod to {new_filepath}")

            # Remove old mod file
            Path(original_filepath).unlink()
            print(f"Removed old mod file: {original_filepath}")
            
            return f"{original_filename} updated to {latest_filename}"

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error downloading mod: {e}") from e
