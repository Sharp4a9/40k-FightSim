import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from typing import Dict, List
from pathlib import Path

class UnitBuilderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Warhammer Unit Builder")
        
        # Configure dark theme
        self.configure_dark_theme()
        
        # Load faction data
        self.faction_data = self.load_faction_data()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add info message at the top
        info_text = """This tool allows you to create and save unit configurations.
The first unit and weapon you include will be the first unit/weapon to activate.
Please report any bugs to Andrew White."""
        info_label = ttk.Label(self.main_frame, text=info_text, wraplength=600, justify=tk.LEFT)
        info_label.grid(row=0, column=0, columnspan=10, pady=10, sticky=tk.W)
        
        # Initialize widget lists
        self.attacker_units = []  # List to store attacker unit widgets
        self.weapon_widgets = []
        self.special_rule_widgets = []
        
        # Create save button first
        self.save_button = ttk.Button(self.main_frame, text="Save Unit Configuration", command=self.save_unit_config)
        
        # Attacker section
        self.create_attacker_section()
        
        # Position the save button
        self.update_button_position()
        
    def configure_dark_theme(self):
        """Configure the dark theme for the application"""
        # Configure root window
        self.root.configure(bg='#2b2b2b')
        
        # Configure style
        style = ttk.Style()
        
        # Configure colors
        style.configure('.',
            background='#2b2b2b',
            foreground='#000000',
            fieldbackground='#3c3f41',
            troughcolor='#3c3f41',
            selectbackground='#4b6eaf',
            selectforeground='#000000'
        )
        
        # Configure specific widget styles
        style.configure('TLabel',
            background='#2b2b2b',
            foreground='#ffffff'
        )
        
        style.configure('TButton',
            background='#3c3f41',
            foreground='#000000'
        )
        
        style.configure('TEntry',
            fieldbackground='#3c3f41',
            foreground='#000000',
            insertcolor='#000000'
        )
        
        # Configure Combobox style
        style.configure('TCombobox',
            fieldbackground='#3c3f41',
            background='#3c3f41',
            foreground='#000000',
            arrowcolor='#000000'
        )
        
        # Configure hover effects
        style.map('TButton',
            background=[('active', '#4b6eaf')],
            foreground=[('active', '#000000')]
        )
        
        style.map('TCombobox',
            fieldbackground=[('readonly', '#3c3f41')],
            selectbackground=[('readonly', '#4b6eaf')],
            selectforeground=[('readonly', '#000000')]
        )
        
        # Configure Frame style
        style.configure('TFrame',
            background='#2b2b2b'
        )
        
    def load_faction_data(self) -> Dict[str, Dict]:
        """Load all faction data from JSON files"""
        faction_data = {}
        data_dir = "data/json"
        for filename in os.listdir(data_dir):
            if filename.endswith(".json"):
                faction_name = filename[:-5]  # Remove .json extension
                with open(os.path.join(data_dir, filename), 'r') as f:
                    faction_data[faction_name] = json.load(f)
        return faction_data
    
    def create_attacker_section(self):
        """Create the unit selection interface"""
        # Unit label
        ttk.Label(self.main_frame, text="Unit Configuration", font=('Arial', 12, 'bold')).grid(row=1, column=0, columnspan=10, pady=5, sticky=tk.W)

        # Designation field
        ttk.Label(self.main_frame, text="Designation:").grid(row=2, column=0, sticky=tk.W)
        self.attacker_designation = ttk.Entry(self.main_frame, width=40)
        self.attacker_designation.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)

        # Points field
        ttk.Label(self.main_frame, text="Points:").grid(row=2, column=2, sticky=tk.W)
        self.attacker_points = ttk.Entry(self.main_frame, width=10)
        self.attacker_points.grid(row=2, column=3, sticky=(tk.W, tk.E), padx=5)

        # Distance field
        ttk.Label(self.main_frame, text="Distance to Target:").grid(row=2, column=4, sticky=tk.W)
        self.target_range = ttk.Entry(self.main_frame, width=10)
        self.target_range.grid(row=2, column=5, sticky=(tk.W, tk.E), padx=5)
        self.target_range.insert(0, "0")  # Set default value to 0

        # Faction selection
        ttk.Label(self.main_frame, text="Faction:").grid(row=3, column=0, sticky=tk.W)
        self.attacker_faction = ttk.Combobox(self.main_frame, values=sorted(self.faction_data.keys()), width=40)
        self.attacker_faction.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5)
        self.attacker_faction.bind('<<ComboboxSelected>>', self.update_attacker_units)
        self.attacker_faction.bind('<KeyRelease>', self.filter_attacker_faction)

        # Add Unit button
        self.add_unit_button = ttk.Button(self.main_frame, text="Add Unit", command=self.add_attacker_unit)
        self.add_unit_button.grid(row=3, column=2, padx=5, sticky=tk.W)

        # Frame to hold all unit frames in a row
        self.units_row_frame = ttk.Frame(self.main_frame)
        self.units_row_frame.grid(row=4, column=0, columnspan=10, sticky=(tk.W, tk.E), pady=2)

        # Add initial unit
        self.add_attacker_unit()

        # Place the initial unit frame in the units_row_frame
        self.update_unit_frames_in_row()

        # Special rules section
        ttk.Label(self.main_frame, text="Special Rules:", font=('Arial', 10)).grid(row=6, column=0, columnspan=10, sticky=tk.W, pady=(10,5))

        # Special rules frame
        self.special_rules_frame = ttk.Frame(self.main_frame)
        self.special_rules_frame.grid(row=7, column=0, columnspan=10, sticky=(tk.W, tk.E), pady=(0,10))

        # List to store special rule widgets
        self.special_rule_widgets = []

        # Add initial special rule row
        self.add_attacker_special_rule_row()

    def add_attacker_unit(self):
        """Add a new unit selection"""
        unit_index = len(self.attacker_units)

        # Create a frame for this unit
        unit_frame = ttk.Frame(self.units_row_frame)

        # Unit selection
        ttk.Label(unit_frame, text=f"Unit {unit_index + 1}:").grid(row=0, column=0, sticky=tk.W)
        unit_combo = ttk.Combobox(unit_frame, width=40)
        unit_combo.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        unit_combo.bind('<<ComboboxSelected>>', lambda e, idx=unit_index: self.update_attacker_weapons(e, idx))
        unit_combo.bind('<KeyRelease>', lambda e, idx=unit_index: self.filter_attacker_unit(e, idx))

        # Remove button
        remove_button = ttk.Button(unit_frame, text="-", width=3,
                                 command=lambda idx=unit_index: self.remove_attacker_unit(idx))

        # Weapon selection frame for this unit
        weapon_frame = ttk.Frame(unit_frame)
        weapon_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))

        # Store the unit widgets
        self.attacker_units.append({
            'frame': unit_frame,
            'unit_combo': unit_combo,
            'weapon_frame': weapon_frame,
            'weapon_widgets': [],
            'remove_button': remove_button
        })

        # Update available units based on selected faction
        faction = self.attacker_faction.get()
        if faction in self.faction_data:
            units = [unit['name'] for unit in self.faction_data[faction]]
            unit_combo['values'] = sorted(units)

        # Place all unit frames in a row and update remove buttons
        self.update_unit_frames_in_row()

    def remove_attacker_unit(self, unit_index):
        """Remove a unit and its widgets"""
        if unit_index < len(self.attacker_units):
            self.attacker_units[unit_index]['frame'].destroy()
            self.attacker_units.pop(unit_index)
            self.update_unit_frames_in_row()
            for i, unit in enumerate(self.attacker_units):
                for widget in unit['frame'].winfo_children():
                    if isinstance(widget, ttk.Label) and widget.cget("text").startswith("Unit "):
                        widget.config(text=f"Unit {i + 1}:")
            self.update_button_position()

    def update_unit_frames_in_row(self):
        """Place all unit frames in a single row"""
        for idx, unit in enumerate(self.attacker_units):
            unit['frame'].grid(row=0, column=idx, sticky=(tk.W, tk.E), padx=5)
            for widget in unit['frame'].grid_slaves():
                if isinstance(widget, ttk.Button) and widget.cget('text') == '-':
                    widget.grid_forget()
            unit['remove_button'].configure(command=lambda idx=idx: self.remove_attacker_unit(idx))
        if len(self.attacker_units) > 1:
            for idx, unit in enumerate(self.attacker_units):
                unit['remove_button'].grid(row=0, column=1, padx=5)

    def update_attacker_units(self, event=None):
        """Update available units based on selected faction"""
        faction = self.attacker_faction.get()
        if faction in self.faction_data:
            units = [unit['name'] for unit in self.faction_data[faction]]
            for unit in self.attacker_units:
                unit['unit_combo']['values'] = sorted(units)
                unit['unit_combo'].set('')

    def update_attacker_weapons(self, event=None, unit_index=None):
        """Update available weapons based on selected unit"""
        if unit_index is None:
            return
            
        unit_data = self.attacker_units[unit_index]
        faction = self.attacker_faction.get()
        unit = unit_data['unit_combo'].get()
        
        # Store current weapon selections
        current_selections = []
        for i in range(0, len(unit_data['weapon_widgets']), 3):
            if i + 1 < len(unit_data['weapon_widgets']):
                quantity = unit_data['weapon_widgets'][i].get()
                weapon = unit_data['weapon_widgets'][i + 1].get()
                if weapon:
                    current_selections.append((quantity, weapon))
        
        # Clear existing weapon widgets
        for widget in unit_data['weapon_widgets']:
            widget.destroy()
        unit_data['weapon_widgets'] = []
        
        if faction in self.faction_data:
            unit_data_obj = next((u for u in self.faction_data[faction] if u['name'] == unit), None)
            if unit_data_obj and 'weapons' in unit_data_obj:
                self.add_weapon_row(unit_data_obj['weapons'], unit_index)
                
                # Restore previous selections
                for quantity, weapon in current_selections:
                    if len(unit_data['weapon_widgets']) > 0:
                        unit_data['weapon_widgets'][0].delete(0, tk.END)
                        unit_data['weapon_widgets'][0].insert(0, quantity)
                        unit_data['weapon_widgets'][1].set(weapon)

    def add_weapon_row(self, weapons, unit_index):
        """Add a new row for weapon selection"""
        unit_data = self.attacker_units[unit_index]
        row = len(unit_data['weapon_widgets']) // 3
        
        weapon_row_frame = ttk.Frame(unit_data['weapon_frame'])
        weapon_row_frame.grid(row=row*2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2)
        
        quantity = ttk.Entry(weapon_row_frame, width=5)
        quantity.grid(row=0, column=0, padx=5)
        quantity.insert(0, "1")
        
        weapon_combo = ttk.Combobox(weapon_row_frame, values=sorted(weapons.keys()), width=40)
        weapon_combo.grid(row=0, column=1, padx=5)
        
        if row == 0:
            add_button = ttk.Button(weapon_row_frame, text="+", width=3, 
                                  command=lambda: self.add_weapon_row(weapons, unit_index))
            add_button.grid(row=0, column=2, padx=5)
        else:
            remove_button = ttk.Button(weapon_row_frame, text="-", width=3,
                                     command=lambda: self.remove_weapon_row(row, unit_index))
            remove_button.grid(row=0, column=2, padx=5)
        
        weapon_stats_label = ttk.Label(weapon_row_frame, text="", wraplength=400)
        weapon_stats_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5)
        
        special_rules_label = ttk.Label(weapon_row_frame, text="", wraplength=400)
        special_rules_label.grid(row=2, column=0, columnspan=3, sticky=tk.W, padx=5)
        
        def update_special_rules(event=None):
            selected_weapon = weapon_combo.get()
            if selected_weapon in weapons:
                weapon_special_rules = weapons[selected_weapon].get('Keywords', [])
                
                faction = self.attacker_faction.get()
                unit = unit_data['unit_combo'].get()
                unit_special_rules = []
                if faction in self.faction_data:
                    unit_data_obj = next((u for u in self.faction_data[faction] if u['name'] == unit), None)
                    if unit_data_obj:
                        unit_special_rules = unit_data_obj.get('special_rules_attack', [])
                
                selected_rules = []
                for i in range(0, len(self.special_rule_widgets), 2):
                    rule = self.special_rule_widgets[i].get()
                    if rule:
                        selected_rules.append(rule)
                
                all_special_rules = weapon_special_rules + unit_special_rules + selected_rules
                
                if all_special_rules:
                    special_rules_label.config(text=f"Special Rules: {', '.join(all_special_rules)}")
                else:
                    special_rules_label.config(text="No special rules")

                weapon_data = weapons[selected_weapon]
                stats = []
                if 'Range' in weapon_data:
                    stats.append(f"Range: {weapon_data['Range']}")
                if 'WS' in weapon_data:
                    stats.append(f"WS: {weapon_data['WS']}")
                elif 'BS' in weapon_data:
                    stats.append(f"BS: {weapon_data['BS']}")
                if 'A' in weapon_data:
                    stats.append(f"A: {weapon_data['A']}")
                if 'S' in weapon_data:
                    stats.append(f"S: {weapon_data['S']}")
                if 'AP' in weapon_data:
                    stats.append(f"AP: {weapon_data['AP']}")
                if 'D' in weapon_data:
                    stats.append(f"D: {weapon_data['D']}")
                
                if stats:
                    weapon_stats_label.config(text=f"Weapon Stats: {', '.join(stats)}")
                else:
                    weapon_stats_label.config(text="No weapon stats available")
            else:
                special_rules_label.config(text="")
                weapon_stats_label.config(text="")
        
        weapon_combo.bind('<<ComboboxSelected>>', update_special_rules)
        
        unit_data['weapon_widgets'].extend([quantity, weapon_combo, add_button if row == 0 else remove_button])
        
        self.update_button_position()
        
    def remove_weapon_row(self, row, unit_index):
        """Remove a weapon selection row"""
        unit_data = self.attacker_units[unit_index]
        start_idx = row * 3
        for widget in unit_data['weapon_widgets'][start_idx:start_idx + 3]:
            widget.destroy()
        unit_data['weapon_widgets'] = unit_data['weapon_widgets'][:start_idx] + unit_data['weapon_widgets'][start_idx + 3:]
        self.update_button_position()

    def add_attacker_special_rule_row(self):
        """Add a new row for special rule selection"""
        row = len(self.special_rule_widgets) // 2
        
        special_rule_combo = ttk.Combobox(self.special_rules_frame, 
                                        values=["Sustained Hits 1", "Lethal Hits", "Reroll Hits", 
                                               "Reroll Hits 1", "Reroll Wounds", "Reroll Wounds 1",
                                               "Critical Hits 5+", "Critical Wounds 5+", "Ignores Cover",
                                               "Devastating Wounds", "Reroll 1 Hit Roll", "Reroll 1 Wound Roll"],
                                        width=40)
        special_rule_combo.grid(row=row, column=0, padx=5, pady=2)
        
        if row == 0:
            add_button = ttk.Button(self.special_rules_frame, text="+", width=3,
                                  command=self.add_attacker_special_rule_row)
            add_button.grid(row=row, column=1, padx=5)
        else:
            remove_button = ttk.Button(self.special_rules_frame, text="-", width=3,
                                     command=lambda: self.remove_special_rule_row(row))
            remove_button.grid(row=row, column=1, padx=5)
        
        self.special_rule_widgets.extend([special_rule_combo, add_button if row == 0 else remove_button])
        
    def remove_special_rule_row(self, row):
        """Remove a special rule selection row"""
        start_idx = row * 2
        for widget in self.special_rule_widgets[start_idx:start_idx + 2]:
            widget.destroy()
        self.special_rule_widgets = self.special_rule_widgets[:start_idx] + self.special_rule_widgets[start_idx + 2:]
        self.update_button_position()

    def update_button_position(self):
        """Update the position of the Save button"""
        # Calculate the row based on the number of weapon rows and special rule rows
        max_weapon_rows = 0
        for unit_data in self.attacker_units:
            weapon_rows = len(unit_data['weapon_widgets']) // 3
            max_weapon_rows = max(max_weapon_rows, weapon_rows)
            
        attacker_special_rule_rows = len(self.special_rule_widgets) // 2
        
        # Find the next available row after special rules
        base_row = 7 + attacker_special_rule_rows
        
        # Remove button from current position if it exists
        self.save_button.grid_remove()
        
        # Place button in new position
        self.save_button.grid(row=base_row, column=0, columnspan=3, pady=10)

    def save_unit_config(self):
        """Save the unit configuration to a JSON file"""
        try:
            # Get designation
            designation = self.attacker_designation.get().strip()
            if not designation:
                messagebox.showerror("Error", "Please enter a designation!")
                return
            
            # Get points
            try:
                points = int(self.attacker_points.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Points must be a valid integer!")
                return
            
            # Get target range
            try:
                target_range = int(self.target_range.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Distance to Target must be a valid integer!")
                return
            
            # Get faction
            faction = self.attacker_faction.get()
            if not faction:
                messagebox.showerror("Error", "Please select a faction")
                return
            
            # Get units and their weapons
            units_data = []
            for unit_data in self.attacker_units:
                unit = unit_data['unit_combo'].get()
                if not unit:
                    continue
                
                # Get unit data from faction
                unit_obj = next((u for u in self.faction_data[faction] if u['name'] == unit), None)
                if not unit_obj:
                    continue
                
                # Get weapons for this unit
                weapons_data = []
                for i in range(0, len(unit_data['weapon_widgets']), 3):
                    if i + 1 < len(unit_data['weapon_widgets']):
                        try:
                            quantity = int(unit_data['weapon_widgets'][i].get())
                            weapon_name = unit_data['weapon_widgets'][i + 1].get()
                            if weapon_name:
                                weapons_data.append({
                                    'name': weapon_name,
                                    'quantity': quantity,
                                    'data': unit_obj['weapons'][weapon_name]
                                })
                        except ValueError:
                            messagebox.showerror("Error", "Weapon quantities must be integers")
                            return
                
                # Get selected special rules
                selected_rules = []
                for i in range(0, len(self.special_rule_widgets), 2):
                    rule = self.special_rule_widgets[i].get()
                    if rule:
                        selected_rules.append(rule)
                
                # Create unit configuration
                unit_config = {
                    'name': unit,
                    'weapons': weapons_data,
                    'special_rules': selected_rules + unit_obj.get('special_rules_attack', [])
                }
                units_data.append(unit_config)
            
            if not units_data:
                messagebox.showerror("Error", "Please select at least one unit")
                return
            
            # Create the configuration for this designation
            config = {
                'faction': faction,
                'points': points,
                'target_range': target_range,
                'units': units_data
            }
            
            # Create output directory if it doesn't exist
            output_dir = Path("data/configs")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Load existing configurations if file exists
            output_file = output_dir / "attacker_array.json"
            existing_configs = {}
            if output_file.exists():
                with open(output_file, 'r') as f:
                    existing_configs = json.load(f)
            
            # Add new configuration
            existing_configs[designation] = config
            
            # Save all configurations back to file
            with open(output_file, 'w') as f:
                json.dump(existing_configs, f, indent=2)
            
            messagebox.showinfo("Success", f"Configuration saved to {output_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            print(f"Error details: {str(e)}")
            import traceback
            traceback.print_exc()

    def filter_attacker_faction(self, event=None):
        """Filter faction combobox based on user input"""
        value = self.attacker_faction.get().lower()
        if value == '':
            self.attacker_faction['values'] = sorted(self.faction_data.keys())
        else:
            data = []
            for item in self.faction_data.keys():
                if value.lower() in item.lower():
                    data.append(item)
            self.attacker_faction['values'] = sorted(data)

    def filter_attacker_unit(self, event=None, unit_index=None):
        """Filter unit combobox based on user input"""
        if unit_index is None:
            return
            
        unit_data = self.attacker_units[unit_index]
        value = unit_data['unit_combo'].get().lower()
        faction = self.attacker_faction.get()
        
        if faction in self.faction_data:
            units = [unit['name'] for unit in self.faction_data[faction]]
            if value == '':
                unit_data['unit_combo']['values'] = sorted(units)
            else:
                data = []
                for item in units:
                    if value.lower() in item.lower():
                        data.append(item)
                unit_data['unit_combo']['values'] = sorted(data)

def main():
    root = tk.Tk()
    app = UnitBuilderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 