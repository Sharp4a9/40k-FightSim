"""
This script converts one of the battlescribe project .cat files into a JSON file.

It has been tested on the Adeptus Custodes and works as well as possible, there.

I do not believe that I can correctly import the number of models in a unit or the special rules for the unit.
Importing Invulernable Saves and Feel No Pains is suspect and currently being worked on.
"""
import xml.etree.ElementTree as ET
import json
import os
import re
import logging
import unicodedata


def strip_non_integers(text):
    """Strip all non-integer characters from a string"""
    if text is None:
        return None
    return re.sub(r'[^0-9]', '', str(text))

def clean_text(text):
    """Remove special characters and normalize whitespace from text"""
    if text is None:
        return None
    
    # Normalize the string, converting unicode characters to their closest ASCII equivalent
    normalized = unicodedata.normalize('NFKD', text)
    
    # Convert to ASCII, ignoring any characters that can't be converted
    ascii_str = normalized.encode('ASCII', 'ignore').decode('ASCII')
    
    # Normalize whitespace
    ascii_str = ' '.join(ascii_str.split())
    
    return ascii_str

def clean_name(name):
    """Remove the ➤ symbol and any extra whitespace from names"""
    if name:
        return clean_text(name.replace('➤', '').strip())
    return name

def remove_empty_models(models):
    """Remove models that have no characteristics"""
    keys_to_remove = [model for model in models if models[model] == {}]
    for key in keys_to_remove:
        models.pop(key)
    return models

def remove_empty_weapons(weapons):
    """Remove weapons that have no characteristics"""
    keys_to_remove = [weapon for weapon in weapons if weapons[weapon] == {}]
    for key in keys_to_remove:
        weapons.pop(key)
    return weapons

def find_points_cost(selectionEntry,ns):
    """Find the cost of the unit"""
    try:
        if not selectionEntry.findall('./bs:costs', ns):
            logging.error(f"No costs found in selectionEntry: {selectionEntry.get('name', 'Unknown')}")
            return 0
            
        for costs in selectionEntry.findall('./bs:costs', ns):
            for cost in costs.findall('./bs:cost', ns):
                if cost.get('name') == 'pts':
                    return int(cost.get('value'))
                
        logging.error(f"No points cost found in selectionEntry: {selectionEntry.get('name', 'Unknown')}")
        return 0
    except Exception as e:
        logging.error(f"Error finding cost for selectionEntry {selectionEntry.get('name', 'Unknown')}: {str(e)}")
        return 0

def find_keywords(selectionEntry,ns):
    """Find the keywords of the unit"""
    keywords = []
    try:
        if not selectionEntry.findall('./bs:categoryLinks', ns):
            return []
        for categoryLinks in selectionEntry.findall('./bs:categoryLinks', ns):
            for categoryLink in categoryLinks.findall('./bs:categoryLink', ns):
                keyword = categoryLink.get('name')
                # Remove the string "Faction:" from the keyword if it exists.
                if keyword.startswith('Faction:'):
                    keyword = keyword.split(':', 1)[1].strip()
                keywords.append(keyword)            
        return keywords
    except Exception as e:
        logging.error(f"Error finding keywords for selectionEntry {selectionEntry.get('name', 'Unknown')}: {str(e)}")
        return []

def find_models_and_characteristics(element, ns, models=None, model_name=None, selection_entry_type=None):
    """Find the models and characteristics of the unit"""
    # Initialize models dictionary if None
    if models is None:
        models = {}
        
    # Units are formatted differently depending on if they are composed of a single model or multiple models.
    keys = ["M", "T", "SV", "W", "LD", "OC", "Inv", "Fnp"]
    
    # Initialize model_characteristics if we have a model name
    tag = element.tag.split('}')[-1]
    if tag == 'selectionEntry' and 'name' in element.attrib and 'type' in element.attrib:
        model_name = clean_name(element.get('name'))
        selection_entry_type = element.get('type')
        if model_name not in models and (element.get('type').lower() == 'unit' or element.get('type').lower() == 'model'):
            models[model_name] = {}

    if tag == 'profile' and (element.get('typeName').lower() == 'unit' or element.get('typeName').lower() == 'model') and (selection_entry_type.lower() == 'unit' or selection_entry_type.lower() == 'model'):
        characteristics = element.find('./bs:characteristics', ns)
        if characteristics is not None:
            for characteristic in characteristics.findall('./bs:characteristic', ns): 
                if characteristic.get('name') in keys:
                    try:
                        value = int(strip_non_integers(characteristic.text.strip()))
                        models[model_name][characteristic.get('name')] = value
                    except (ValueError, TypeError) as e:
                        value = characteristic.text.strip()
                        models[model_name][characteristic.get('name')] = value
                        logging.warning(f"Noninteger value for {model_name} characteristic: {characteristic.get('name')} = {value}")
    
    # Only process children if we're still within the same selectionEntry's subtree
    for child in element:
        find_models_and_characteristics(child, ns, models, model_name, selection_entry_type)

    return models

def weapons_format(text):
    """Format weapon characteristics based on their content.
    Returns:
    - Integer if the input is a number with optional + or -
    - String if the input is a single string without commas
    - List of strings if the input contains commas
    """
    if text is None:
        return None
        
    # Try to convert to integer first (handles cases like "3+" or "-2")
    try:
        # Remove any + or - signs and convert to integer
        cleaned = text.replace('+', '').replace('-', '').replace('\"', '')
        return int(cleaned)
    except ValueError:
        # If not an integer return as string
        return text.strip()

def find_weapons(element, ns, catalog, weapons=None, weapon_name=None, selection_entry_type=None):
    """Find the weapons of the unit"""
    # Initialize models dictionary if None
    if weapons is None:
        weapons = {}
        
    # Units are formatted differently depending on if they are composed of a single model or multiple models.
    keys = ["Range", "type", "A", "WS", "BS", "S", "AP", "D", "Keywords"]
    
    # Find the weapons that are stored as part of the unit.
    tag = element.tag.split('}')[-1]
    if tag == 'profile' and 'name' in element.attrib and 'typeName' in element.attrib:
        if element.get('typeName') == 'Melee Weapons' or element.get('typeName') == 'Ranged Weapons':
            weapon_name_temp = clean_name(element.get('name'))
            selection_entry_type = element.get('typeName')
            weapon_name = weapon_name_temp + " - " + selection_entry_type.split(" ")[0]
            weapon_type = selection_entry_type.split(" ")[0]
            if weapon_name not in weapons:
                weapons[weapon_name] = {}
            weapons[weapon_name]["type"] = weapon_type

            characteristics = element.find('./bs:characteristics', ns)
            if characteristics is not None:
                for characteristic in characteristics.findall('./bs:characteristic', ns):
                    if characteristic.get('name') in keys:
                        if characteristic.get('name') == "Keywords":
                            value = weapons_format(characteristic.text.strip())
                            if "," in value:
                                value = [text.strip() for text in value.split(',')]
                                weapons[weapon_name][characteristic.get('name')] = value
                            elif value == "-":
                                value = []
                            else:
                                weapons[weapon_name][characteristic.get('name')] = [value]
                        else:
                            try:
                                value = weapons_format(characteristic.text.strip())
                                weapons[weapon_name][characteristic.get('name')] = value
                            except (ValueError, TypeError) as e:
                                logging.warning(f"Could not convert characteristic value for {weapon_name}: {str(e)}")
                if "Keywords" not in characteristics:
                    weapons[weapon_name]["Keywords"] = []
                
    
    # Find the weapons that are stored in a common profile.
    if tag == 'entryLink' and element.get('type') == 'selectionEntry':
        target_id = element.get('targetId')
        for selectionEntry in catalog.findall('.//bs:selectionEntry', ns):
            entry_id = selectionEntry.get('id')
            if entry_id == target_id:
                weapon_name_temp = clean_name(selectionEntry.get('name'))
                for profile in selectionEntry.findall('.//bs:profile', ns):
                    if not profile.get('typeName'):
                        continue
                    selection_entry_type = profile.get('typeName')
                    weapon_name = weapon_name_temp + " - " + selection_entry_type.split(" ")[0]
                    weapon_type = selection_entry_type.split(" ")[0]

                    if weapon_name not in weapons:
                        weapons[weapon_name] = {}
                    else:
                        continue
                    weapons[weapon_name]["type"] = weapon_type
                    for profile in selectionEntry.findall('.//bs:profile', ns):
                        if 'weapons' in profile.get('typeName').lower():
                            for characteristic in profile.findall('./bs:characteristics/bs:characteristic', ns):
                                if characteristic.get('name') in keys:
                                    if characteristic.get('name') == "Keywords":
                                        value = weapons_format(characteristic.text.strip())
                                        if "," in value:
                                            value = [text.strip() for text in value.split(',')]
                                            weapons[weapon_name][characteristic.get('name')] = value
                                        elif value == "-":
                                            value = []
                                        else:
                                            weapons[weapon_name][characteristic.get('name')] = [value]
                                    else:
                                        try:
                                            value = weapons_format(characteristic.text.strip())
                                            weapons[weapon_name][characteristic.get('name')] = value
                                        except (ValueError, TypeError) as e:
                                            logging.warning(f"Could not convert characteristic value for {weapon_name}: {str(e)}")
                            if "Keywords" not in profile.findall('./bs:characteristics/bs:characteristic', ns):
                                weapons[weapon_name]["Keywords"] = []
                            


    # Only process children if we're still within the same selectionEntry's subtree
    for child in element:
        find_weapons(child, ns, catalog, weapons, weapon_name, selection_entry_type)
    
    return weapons

def find_abilities(element, ns):
    """Find the abilities of the unit"""
    abilities = []
    for profile in element.findall('.//bs:profile', ns):
        if profile.get('typeName').lower() == 'abilities':
            name = clean_text(profile.get('name'))
            for characteristic in profile.findall('./bs:characteristics/bs:characteristic', ns):
                if characteristic.get('name') == 'Description':
                    description = clean_text(characteristic.text.strip())
                    abilities.append(name + ":" + description)
    return abilities

def apply_invulnerable_save(element, ns, sharedProfiles, models):
    """Apply the invulnerable save to the models"""
    for infoLink in element.findall('.//bs:infoLink', ns):
        tag = infoLink.tag.split('}')[-1]
        if tag == 'infoLink' and infoLink.get('name') == 'Invulnerable Save' and 'targetId' in infoLink.attrib:
            invuln_target_id = infoLink.get('targetId')
            # Iterate through each sharedProfiles element
            for sharedProfile in sharedProfiles:
                # Find all profiles within this sharedProfiles element
                for profile in sharedProfile.findall('./bs:profile', ns):
                    if profile.get('id') == invuln_target_id:
                        # Find the description characteristic
                        characteristics = profile.find('./bs:characteristics', ns)
                        if characteristics is not None:
                            for characteristic in characteristics.findall('./bs:characteristic', ns):
                                if characteristic.get('name') == 'Description':
                                    # Extract the save value from the description
                                    desc = characteristic.text
                                    if desc:
                                        # Look for patterns like "X+" in the description
                                        match = re.search(r'(\d+)\+', desc)
                                        if match:
                                            inv_value = int(match.group(1))
                                            # Apply to all models
                                            for model in models:
                                                models[model]["Inv"] = inv_value
        elif tag == 'infoLink' and infoLink.get('name').startswith('Invulnerable Save'): ##### JUST ABOUT TO TEST THIS!!!!!
            desc = infoLink.get('name')
            if desc:
                # Look for patterns like "X+" in the description
                match = re.search(r'(\d+)\+', desc)
                if match:
                    inv_value = int(match.group(1))
                    # Apply to all models
                    for model in models:
                        models[model]["Inv"] = inv_value
    return models

def apply_feel_no_pain(element, ns, models):
    """Apply the feel no pain to the models"""
    for infoLink in element.findall('.//bs:infoLink', ns):
        tag = infoLink.tag.split('}')[-1]
        if tag == 'infoLink' and infoLink.get('name') == 'Feel No Pain':
            modifier = infoLink.find('./bs:modifiers/bs:modifier', ns)
            if modifier is not None:
                value = modifier.get('value').replace('+', '')
                for model in models:
                    models[model]["Fnp"] = int(value)
    return models

def convert_cat_to_json(cat_file_path, ns):
    print(f"Reading file: {cat_file_path}")
    
    # Read the file content
    with open(cat_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove any XML declarations
    content = re.sub(r'<\?xml[^>]*\?>', '', content)
    
    # Wrap the content in a root element to make it valid XML
    wrapped_content = f"<root>{content}</root>"
    
    try:
        root = ET.fromstring(wrapped_content)
    except ET.ParseError as e:
        print(f"XML Parse Error: {str(e)}")
        return None
    
    # Find the catalog element using the namespace
    catalog = root.find(".//bs:catalogue", ns)
    if catalog is None:
        print("No catalogue element found")
        return None
    
    # There is some information we need in profiles.
    sharedProfiles = catalog.findall('.//bs:sharedProfiles', ns)

    units = []

    for sharedSelectionEntries in catalog.findall('./bs:sharedSelectionEntries', ns):
        for selectionEntry in sharedSelectionEntries.findall('./bs:selectionEntry', ns):
            if selectionEntry.get('type').lower() == 'model' or selectionEntry.get('type').lower() == 'unit':
                # Skip units with [Legends] in their name
                if "[Legends]" in selectionEntry.get('name', ''):
                    continue
                print(f"Processing unit: {selectionEntry.get('name')}")

                keywords = find_keywords(selectionEntry,ns)
                if len(keywords) == 0:
                    print(f"Processing unit: {selectionEntry.get('name')} - No keywords found; skipping.")
                    continue

                models = remove_empty_models(find_models_and_characteristics(selectionEntry,ns))
                for model in models:
                    models[model]["Inv"] = None
                    models[model]["Fnp"] = None
                models = apply_invulnerable_save(selectionEntry, ns, sharedProfiles, models)
                models = apply_feel_no_pain(selectionEntry, ns, models)

                weapons = remove_empty_weapons(find_weapons(selectionEntry,ns,catalog))

                # Create base unit data
                unit_data = {
                    "name": clean_name(selectionEntry.get('name')), # String
                    "models": models, # Dictionary
                    "weapons": weapons, # Dictionary
                    "abilities": find_abilities(selectionEntry,ns), # List
                    "keywords": keywords, # List
                    "total_models": 1, # Integer
                    "points": find_points_cost(selectionEntry,ns), # Integer
                    "special_rules_attack": [], # List, always empty; must be manually added to the .json file.
                    "special_rules_defence": [] # List, always empty; must be manually added to the .json file.
                }
                # print(unit_data)
                units.append(unit_data)
            
    
    return units

def main():
    # Example usage
    cat_file_path = "C:\\Users\\andre\\OneDrive\\Documents\\Warhammer\\FightSim_2.0\\data\\wh40k-10e\\Imperium - White Scars.cat"
    
    # Extract faction name from cat file path
    cat_filename = os.path.basename(cat_file_path)
    if " - " in cat_filename:
        faction_name = cat_filename.split(' - ')[1].replace('.cat', '')
    else:
        faction_name = cat_filename.split('.')[0]
    
    # Remove "Library" from faction name if present
    faction_name = faction_name.replace('Library', '').strip()
    
    output_file_path = f"data/json/marine subchapters (ignore)/{faction_name}.json"
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    
    try:
        ns = {'bs': 'http://www.battlescribe.net/schema/catalogueSchema'}
        units_data = convert_cat_to_json(cat_file_path, ns)
        if units_data:
            # Write to JSON file with custom formatting
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json_str = json.dumps(units_data, indent=2)
                # Replace multi-line model characteristics with single-line format
                json_str = re.sub(r'(\s+)"([^"]+)":\s*{\n\s+"M":\s*(\d+),\n\s+"T":\s*(\d+),\n\s+"SV":\s*(\d+),\n\s+"W":\s*(\d+),\n\s+"LD":\s*(\d+),\n\s+"OC":\s*(\d+),\n\s+"Inv":\s*(\d+|null),\n\s+"Fnp":\s*(\d+|null)\n\s+}', r'\1"\2": {"M": \3, "T": \4, "SV": \5, "W": \6, "LD": \7, "OC": \8, "Inv": \9, "Fnp": \10}', json_str)
                f.write(json_str)
            
            print(f"Successfully converted {cat_file_path} to {output_file_path}")
            print(f"Processed {len(units_data)} units")
        else:
            print("No units were processed")
    
    except Exception as e:
        print(f"Error converting file: {str(e)}")

if __name__ == "__main__":
    main()