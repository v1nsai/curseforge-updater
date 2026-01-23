#!/bin/bash

set -eou pipefail

# Init and check vars
MOD_FOLDER="$1"
UPDATED_MODS=()
MOD_DATA_JSON="{}"

if [ -z "$CURSEFORGE_API_KEY" ]; then
  echo "Error: CURSEFORGE_API_KEY is not set in .env file."
  exit 1
fi
if [ -z "$MOD_FOLDER" ]; then
  echo "Usage: $0 <mod_folder>"
  exit 1
fi
if ! ls "$MOD_FOLDER"/*.jar &>/dev/null; then
  echo "No .jar files found in $MOD_FOLDER"
  exit 1
fi

# get filepaths of all .jar and .zip files in mod folder
echo "Scanning mod folder: $MOD_FOLDER"
MOD_FILEPATHS=$(find "$MOD_FOLDER" -type f \( -name "*.jar" -o -name "*.zip" \))

# Generate fingerprints for found mod files
for MOD_FILEPATH in $MOD_FILEPATHS; do
  if [ -f "$MOD_FILEPATH" ]; then
    echo "Processing mod file: $MOD_FILEPATH"
    MOD_FILENAME=$(basename "$MOD_FILEPATH")

    echo "Calculating fingerprint for: $MOD_FILENAME..."
    FINGERPRINT=$(python3 fingerprint.py "$MOD_FILEPATH")
    if [ -n "$FINGERPRINT" ]; then
      MOD_DATA_JSON=$(echo "$MOD_DATA_JSON" | jq --arg fingerprint "$FINGERPRINT" --arg filepath "$MOD_FILEPATH" '. + {($fingerprint): $filepath}')
    else
      echo "Error: Could not calculate fingerprint for $MOD_FILENAME."
      exit 1
    fi
  fi
done

FINGERPRINTS=($(echo "$MOD_DATA_JSON" | jq -r 'keys[]'))
if [ ${#FINGERPRINTS[@]} -eq 0 ]; then
  echo "No fingerprints were generated. Exiting."
  exit 1
fi
FINGERPRINT_STRING=$(IFS=,; echo "${FINGERPRINTS[*]}")

# Match fingerprints
echo "Querying CurseForge API for found fingerprints..."
FINGERPRINT_RESPONSE=$(curl -s -X POST "https://api.curseforge.com/v1/fingerprints" \
  -H "Accept: application/json" \
  -H "x-api-key: $CURSEFORGE_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"fingerprints\": [$FINGERPRINT_STRING]}")

if ! echo "$FINGERPRINT_RESPONSE" | jq -e '.data.unmatchedFingerprints == null' > /dev/null; then
  UNMATCHED_FINGERPRINTS=$(echo "$FINGERPRINT_RESPONSE" | jq -r '.data.unmatchedFingerprints | join(", ")')
  echo "Error: Some fingerprints did not match any mods on CurseForge."
  echo "Unmatched fingerprints: $UNMATCHED_FINGERPRINTS"
  exit 1
fi
echo "Checking for partial matches..."
readarray -t PARTIAL_MATCHES < <(echo "$FINGERPRINT_RESPONSE" | jq -c '.data.partialMatches[]')
if [ ${#PARTIAL_MATCHES[@]} -eq 0 ]; then
  echo "No partial matches found."
else
  echo "Partial matches found:"
  for PARTIAL in "${PARTIAL_MATCHES[@]}"; do
    PARTIAL_FINGERPRINT=$(echo "$PARTIAL" | jq -r ".fileFingerprint")
    PARTIAL_MOD_ID=$(echo "$PARTIAL" | jq -r ".id")
    PARTIAL_FILENAME=$(basename "$(echo "$MOD_DATA_JSON" | jq -r --arg fingerprint "$PARTIAL_FINGERPRINT" '.[$fingerprint]')")
    echo "- Mod ID: $PARTIAL_MOD_ID for file $PARTIAL_FILENAME did not match exactly. Please report this issue on the GitHub repo."
    exit 1
  done
fi 
echo "Checking for exact matches..."
readarray -t MATCHES < <(echo "$FINGERPRINT_RESPONSE" | jq -c '.data.exactMatches[]')
if [ ${#MATCHES[@]} -eq 0 ]; then
  echo "No mods found on CurseForge for the provided fingerprints."
fi

# Check for updates and download latest versions
echo "Checking for updates for matched mods..."
for MATCH in "${MATCHES[@]}"; do
  MOD_ID=$(echo "$MATCH" | jq -r ".id")
  LATEST_FILE=$(echo "$MATCH" | jq '.latestFiles[0]')
  LATEST_FILENAME=$(echo "$LATEST_FILE" | jq -r ".fileName")
  ORIGINAL_FINGERPRINT=$(echo "$MATCH" | jq -r '.file.fileFingerprint')

  ORIGINAL_FILEPATH=$(echo "$MOD_DATA_JSON" | jq -r --arg fingerprint "$ORIGINAL_FINGERPRINT" '.[$fingerprint]')
  if [ -z "$ORIGINAL_FILEPATH" ]; then
      echo "Could not find original file for fingerprint $ORIGINAL_FINGERPRINT. This should not happen."
      exit 1
  fi
  if [ ! -f "$ORIGINAL_FILEPATH" ]; then
    echo "Original mod file $ORIGINAL_FILEPATH does not exist."
    exit 1
  fi

  ORIGINAL_FILENAME=$(basename "$ORIGINAL_FILEPATH")
  if [ -z "$ORIGINAL_FILENAME" ]; then
    echo "Could not determine original filename from path $ORIGINAL_FILEPATH."
    exit 1
  fi

  if [ "$LATEST_FILENAME" == "$ORIGINAL_FILENAME" ]; then
    echo "Mod $ORIGINAL_FILENAME is already up to date."
    continue
  else
    echo "Found update for $ORIGINAL_FILENAME. New version is $LATEST_FILENAME."
    LATEST_DOWNLOAD_URL=$(echo "$LATEST_FILE" | jq -r ".downloadUrl")
    if [ -z "$LATEST_DOWNLOAD_URL" ] || [ "$LATEST_DOWNLOAD_URL" == "null" ]; then
      echo "No download URL found for the latest version of mod ID $MOD_ID"
      echo "Downloading file using file ID instead..."
      FILE_ID=$(echo "$LATEST_FILE" | jq -r ".id")
      LATEST_DOWNLOAD_URL="https://api.curseforge.com/v1/mods/$MOD_ID/files/$FILE_ID"
      if [ -z "$LATEST_DOWNLOAD_URL" ] || [ "$LATEST_DOWNLOAD_URL" == "null" ]; then
        echo "Error: Could not construct download URL for mod ID $MOD_ID file ID $FILE_ID."
        exit 1
      fi
    fi
    echo "Downloading latest version of mod ID $MOD_ID..."
    curl -L -o "$MOD_FOLDER/$LATEST_FILENAME" "$LATEST_DOWNLOAD_URL"
    echo "Downloaded latest mod to $MOD_FOLDER/$LATEST_FILENAME"
    UPDATED_MODS+=("$ORIGINAL_FILENAME updated to $LATEST_FILENAME")
    rm "$ORIGINAL_FILEPATH"
    echo "Removed old mod file: $ORIGINAL_FILEPATH"
  fi
done

echo "Update process completed."
if [ ${#UPDATED_MODS[@]} -eq 0 ]; then
  echo "All mods are already up to date."
else
  echo "Updated mods:"
  for MOD in "${UPDATED_MODS[@]}"; do
    echo "- $MOD"
  done
fi

exit 0