import json
import os
from pathlib import Path

def combine_space_marine_files():
    # Get the data directory path
    data_dir = Path("data/json")
    
    # List to store all units from all files
    all_files = ["Raven Guard.json", "Salamanders.json", "Space Wolves.json", "Blood Angels.json", "Dark Angels.json",
                 "Space Marines.json","Ultramarines.json","White Scars.json","Deathwatch.json","Black Templars.json"]
    all_units = []
    seen_units = set()  # Set to track unit names we've already processed
    duplicates = []  # List to track duplicate entries
    
    # Iterate through all JSON files in the data directory
    for filename in all_files:
        file_path = data_dir / filename
        
        # Read and parse the JSON file
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
                # If the data is a list, process each unit
                if isinstance(data, list):
                    for unit in data:
                        unit_name = unit.get('name', '')
                        if unit_name and unit_name not in seen_units:
                            all_units.append(unit)
                            seen_units.add(unit_name)
                        elif unit_name:
                            duplicates.append((unit_name, filename))
                # If it's a dictionary, process as a single unit
                elif isinstance(data, dict):
                    unit_name = data.get('name', '')
                    if unit_name and unit_name not in seen_units:
                        all_units.append(data)
                        seen_units.add(unit_name)
                    elif unit_name:
                        duplicates.append((unit_name, filename))
            except json.JSONDecodeError:
                print(f"Error reading {filename}: Invalid JSON format")
                continue
    
    # Sort units by name for consistency
    all_units.sort(key=lambda x: x.get('name', ''))
    
    # Write the combined data to a new file
    output_path = data_dir / "Space Marines.json"
    with open(output_path, 'w') as f:
        json.dump(all_units, f, indent=2)
    
    # Print summary
    print(f"Successfully combined {len(all_units)} unique units into {output_path}")
    if duplicates:
        print("\nDuplicate entries found:")
        for unit_name, filename in duplicates:
            print(f"- {unit_name} (from {filename})")
    else:
        print("No duplicate entries found.")

if __name__ == "__main__":
    combine_space_marine_files() 