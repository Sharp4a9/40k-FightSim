import json
import os
from pathlib import Path

# Define the standard array of units we want to include, in specific order
STANDARD_ARRAY = [
    ("Tyranids", "Hormagaunts"),
    ("Orks", "Boyz"),
    ("Necrons", "Necron Warriors"),
    ("Adepta Sororitas", "Battle Sisters Squad"),
    ("Orks", "Nobz"),
    ("Space Marines", "Intercessor Squad"),
    ("Leagues of Votann", "Einhyr Hearthguard"),
    ("Space Marines","Aggressor Squad"),
    ("Space Marines", "Terminator Squad"),
    ("Adeptus Custodes", "Custodian Guard"),
    ("Orks", "Trukk"),
    ("Aeldari", "Falcon"),
    ("Imperial Knights", "Armiger Warglaive"),
    ("Space Marines", "Gladiator Lancer"),
    ("Necrons", "Transcendant C'tan"),
    ("Imperial Knights", "Knight Paladin")
]

def load_faction_data(faction_name):
    """Load data from a faction's JSON file by searching for the faction name in filenames."""
    json_path = Path("data/json")
    if not json_path.exists():
        print(f"Error: JSON directory not found at {json_path}")
        return None
    
    if faction_name == "Space Marines":
        file_path = json_path / "Space Marines.json"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {str(e)}")
            return None

    # Search through all JSON files in the directory
    for file_path in json_path.glob("*.json"):
        # Check if faction name is in the filename (case-insensitive)
        if faction_name.lower() in file_path.stem.lower():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading {file_path}: {str(e)}")
                return None
    
    print(f"Warning: Could not find file containing faction name '{faction_name}'")
    return None

def find_unit(faction_data, unit_name):
    """Find a specific unit in faction data using case-insensitive matching."""
    if not faction_data:
        return None
    
    # Normalize the search name
    search_name = unit_name.lower().strip()
    
    for unit in faction_data:
        # Normalize the unit name from the data
        current_name = unit["name"].lower().strip()
        if current_name == search_name:
            return unit
    
    # If exact match fails, try partial match
    for unit in faction_data:
        current_name = unit["name"].lower().strip()
        if search_name in current_name or current_name in search_name:
            print(f"Found partial match: '{unit['name']}' for search term '{unit_name}'")
            return unit
    
    return None

def main():
    # Create output directory if it doesn't exist
    output_dir = Path("data/json")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Collect all units in the specified order
    all_units = []
    for faction_name, unit_name in STANDARD_ARRAY:
        faction_data = load_faction_data(faction_name)
        if faction_data:
            unit = find_unit(faction_data, unit_name)
            if unit:
                all_units.append(unit)
            else:
                print(f"Warning: Could not find unit '{unit_name}' in {faction_name}")
    
    # Write to output file
    output_path = output_dir / "zz_standard_target_array.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_units, f, indent=2)
    
    print(f"Created standard array with {len(all_units)} units")
    print(f"Output written to: {output_path}")

if __name__ == "__main__":
    main() 