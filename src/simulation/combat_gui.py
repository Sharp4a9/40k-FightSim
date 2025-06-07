import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from typing import Dict, List
from combat_engine import CombatEngine, Model, Weapon
from unit_combat_simulator import UnitCombatSimulator
from attacker_special_rules import SPECIAL_RULES
from pathlib import Path

class CombatSimulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Warhammer Combat Simulator")
        
        # Configure dark theme
        self.configure_dark_theme()
        
        # Initialize combat engine and simulator
        self.combat_engine = CombatEngine()
        self.simulator = UnitCombatSimulator(num_simulations=1000, debug=False)
        
        # Load faction data
        self.faction_data = self.load_faction_data()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add info message at the top
        info_text = """Faction names that include dates have had special rules added by hand; all other factions just have stats and weapon keywords.
Cover is implemented as a Defender Special Rule.
The first unit and weapon you include will be the first unit/weapon to activate.
Rapid Fire and Melta activate under half range, as normal; the melta bonus applies after damage reduction.
Please report any bugs to Andrew White."""
        info_label = ttk.Label(self.main_frame, text=info_text, wraplength=600, justify=tk.LEFT)
        info_label.grid(row=0, column=0, columnspan=10, pady=10, sticky=tk.W)
        
        # Initialize widget lists
        self.attacker_units = []  # List to store attacker unit widgets
        self.weapon_widgets = []
        self.special_rule_widgets = []
        self.defender_special_rule_widgets = []
        
        # Create run button first
        self.run_button = ttk.Button(self.main_frame, text="Run Simulation", command=self.run_simulation)
        
        # Attacker section
        self.create_attacker_section()
        
        # Defender section
        self.create_defender_section()
        
        # Output options section
        self.create_output_section()
        
        # Debug toggle
        self.create_debug_section()
        
        # Position the run button and dynamic sections
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
        # Use Path to handle paths in a cross-platform way
        # Go up two levels from the current file to reach project root
        data_dir = Path(__file__).parent.parent.parent / "data" / "json"
        
        # Ensure the directory exists
        if not data_dir.exists():
            raise FileNotFoundError(f"Data directory not found at {data_dir}")
            
        for json_file in data_dir.glob("*.json"):
            faction_name = json_file.stem  # Get filename without extension
            with open(json_file, 'r') as f:
                faction_data[faction_name] = json.load(f)
        return faction_data
    
    def create_attacker_section(self):
        """Create the attacker selection interface"""
        # Attacker label
        ttk.Label(self.main_frame, text="Attacker", font=('Arial', 12, 'bold')).grid(row=1, column=0, columnspan=10, pady=5, sticky=tk.W)

        # Faction selection
        ttk.Label(self.main_frame, text="Faction:").grid(row=2, column=0, sticky=tk.W)
        self.attacker_faction = ttk.Combobox(self.main_frame, values=sorted(self.faction_data.keys()), width=40)
        self.attacker_faction.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        self.attacker_faction.bind('<<ComboboxSelected>>', self.update_attacker_units)
        self.attacker_faction.bind('<KeyRelease>', self.filter_attacker_faction)

        # Add Unit button
        self.add_unit_button = ttk.Button(self.main_frame, text="Add Unit", command=self.add_attacker_unit)
        self.add_unit_button.grid(row=2, column=2, padx=5, sticky=tk.W)

        # Frame to hold all unit frames in a row (must be before add_attacker_unit)
        self.units_row_frame = ttk.Frame(self.main_frame)
        self.units_row_frame.grid(row=3, column=0, columnspan=10, sticky=(tk.W, tk.E), pady=2)

        # Add initial unit
        self.add_attacker_unit()

        # Place the initial unit frame in the units_row_frame
        self.update_unit_frames_in_row()

        # Distance to Defender (always below all units)
        ttk.Label(self.main_frame, text="Distance to Defender:").grid(row=4, column=0, sticky=tk.W)
        self.attacker_range = ttk.Entry(self.main_frame, width=5)
        self.attacker_range.grid(row=4, column=1, sticky=tk.W, padx=5)
        self.attacker_range.insert(0, "0")  # Default range

        # Special rules section
        ttk.Label(self.main_frame, text="Attacker Special Rules:", font=('Arial', 10)).grid(row=5, column=0, columnspan=10, sticky=tk.W, pady=(10,5))

        # Special rules frame
        self.special_rules_frame = ttk.Frame(self.main_frame)
        self.special_rules_frame.grid(row=6, column=0, columnspan=10, sticky=(tk.W, tk.E), pady=(0,10))

        # List to store special rule widgets
        self.special_rule_widgets = []

        # Add initial special rule row
        self.add_attacker_special_rule_row()

    def add_attacker_unit(self):
        """Add a new attacker unit selection"""
        unit_index = len(self.attacker_units)

        # Create a frame for this unit (will be placed in units_row_frame)
        unit_frame = ttk.Frame(self.units_row_frame)
        # Do not grid here; will be handled by update_unit_frames_in_row

        # Unit selection
        ttk.Label(unit_frame, text=f"Unit {unit_index + 1}:").grid(row=0, column=0, sticky=tk.W)
        unit_combo = ttk.Combobox(unit_frame, width=40)
        unit_combo.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        unit_combo.bind('<<ComboboxSelected>>', lambda e, idx=unit_index: self.update_attacker_weapons(e, idx))
        unit_combo.bind('<KeyRelease>', lambda e, idx=unit_index: self.filter_attacker_unit(e, idx))

        # Remove button (will be managed after appending)
        remove_button = ttk.Button(unit_frame, text="-", width=3,
                                 command=lambda idx=unit_index: self.remove_attacker_unit(idx))
        # Don't grid yet

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
        """Remove an attacker unit and its widgets"""
        if unit_index < len(self.attacker_units):
            # Destroy all widgets in the unit's frame
            self.attacker_units[unit_index]['frame'].destroy()
            # Remove the unit from our list
            self.attacker_units.pop(unit_index)
            # Update remaining unit positions and labels
            self.update_unit_frames_in_row()
            for i, unit in enumerate(self.attacker_units):
                for widget in unit['frame'].winfo_children():
                    if isinstance(widget, ttk.Label) and widget.cget("text").startswith("Unit "):
                        widget.config(text=f"Unit {i + 1}:")
            # Update button position
            self.update_button_position()

    def update_unit_frames_in_row(self):
        """Place all unit frames in a single row inside units_row_frame and manage remove buttons."""
        for idx, unit in enumerate(self.attacker_units):
            unit['frame'].grid(row=0, column=idx, sticky=(tk.W, tk.E), padx=5)
            # Remove any existing remove button
            for widget in unit['frame'].grid_slaves():
                if isinstance(widget, ttk.Button) and widget.cget('text') == '-':
                    widget.grid_forget()
            # Always update the remove button's command to the current index
            unit['remove_button'].configure(command=lambda idx=idx: self.remove_attacker_unit(idx))
        # Only show remove buttons if more than one unit
        if len(self.attacker_units) > 1:
            for idx, unit in enumerate(self.attacker_units):
                unit['remove_button'].grid(row=0, column=1, padx=5)

    def update_attacker_units(self, event=None):
        """Update available units based on selected faction"""
        faction = self.attacker_faction.get()
        if faction in self.faction_data:
            # Extract unit names from the array of units
            units = [unit['name'] for unit in self.faction_data[faction]]
            # Update all unit comboboxes
            for unit in self.attacker_units:
                unit['unit_combo']['values'] = sorted(units)
                unit['unit_combo'].set('')  # Clear current selection
            
    def update_attacker_weapons(self, event=None, unit_index=None):
        """Update available weapons based on selected unit"""
        if unit_index is None:
            return
            
        unit_data = self.attacker_units[unit_index]
        faction = self.attacker_faction.get()
        unit = unit_data['unit_combo'].get()
        
        print(f"Selected faction: {faction}")
        print(f"Selected unit: {unit}")
        
        # Store current weapon selections before clearing
        current_selections = []
        for i in range(0, len(unit_data['weapon_widgets']), 3):
            if i + 1 < len(unit_data['weapon_widgets']):  # Check if we have a weapon combo
                quantity = unit_data['weapon_widgets'][i].get()
                weapon = unit_data['weapon_widgets'][i + 1].get()
                if weapon:  # Only store if a weapon was selected
                    current_selections.append((quantity, weapon))
        
        # Clear existing weapon widgets
        for widget in unit_data['weapon_widgets']:
            widget.destroy()
        unit_data['weapon_widgets'] = []
        
        if faction in self.faction_data:
            print("Faction found in data")
            # Find the selected unit in the faction data
            unit_data_obj = next((u for u in self.faction_data[faction] if u['name'] == unit), None)
            print(f"Unit data found: {unit_data_obj is not None}")
            if unit_data_obj:
                print(f"Unit data keys: {unit_data_obj.keys()}")
                if 'weapons' in unit_data_obj:
                    print(f"Available weapons: {list(unit_data_obj['weapons'].keys())}")
                    # Create initial weapon selection row
                    self.add_weapon_row(unit_data_obj['weapons'], unit_index)
                    
                    # Restore previous selections
                    for quantity, weapon in current_selections:
                        if len(unit_data['weapon_widgets']) > 0:  # If we have at least one row
                            # Set the quantity
                            unit_data['weapon_widgets'][0].delete(0, tk.END)
                            unit_data['weapon_widgets'][0].insert(0, quantity)
                            # Set the weapon
                            unit_data['weapon_widgets'][1].set(weapon)
                else:
                    print("No weapons found in unit data")
            else:
                print("Unit data not found")
        else:
            print("Faction not found in data")
            print(f"Available factions: {list(self.faction_data.keys())}")

    def add_weapon_row(self, weapons, unit_index):
        """Add a new row for weapon selection"""
        unit_data = self.attacker_units[unit_index]
        row = len(unit_data['weapon_widgets']) // 3  # Each row now has 3 widgets (quantity, weapon, button)
        
        # Create a frame for this weapon row
        weapon_row_frame = ttk.Frame(unit_data['weapon_frame'])
        weapon_row_frame.grid(row=row*2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2)
        
        # Quantity entry
        quantity = ttk.Entry(weapon_row_frame, width=5)
        quantity.grid(row=0, column=0, padx=5)
        quantity.insert(0, "1")  # Default quantity
        
        # Weapon selection
        weapon_combo = ttk.Combobox(weapon_row_frame, values=sorted(weapons.keys()), width=40)
        weapon_combo.grid(row=0, column=1, padx=5)
        
        # Add button for first row only
        if row == 0:
            add_button = ttk.Button(weapon_row_frame, text="+", width=3, 
                                  command=lambda: self.add_weapon_row(weapons, unit_index))
            add_button.grid(row=0, column=2, padx=5)
        else:
            remove_button = ttk.Button(weapon_row_frame, text="-", width=3,
                                     command=lambda: self.remove_weapon_row(row, unit_index))
            remove_button.grid(row=0, column=2, padx=5)
        
        # Create label for weapon stats
        weapon_stats_label = ttk.Label(weapon_row_frame, text="", wraplength=400)
        weapon_stats_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5)
        
        # Create label for special rules
        special_rules_label = ttk.Label(weapon_row_frame, text="", wraplength=400)
        special_rules_label.grid(row=2, column=0, columnspan=3, sticky=tk.W, padx=5)
        
        # Function to update special rules display
        def update_special_rules(event=None):
            selected_weapon = weapon_combo.get()
            if selected_weapon in weapons:
                # Get weapon's own special rules
                weapon_special_rules = weapons[selected_weapon].get('Keywords', [])
                
                # Get unit's special rules
                faction = self.attacker_faction.get()
                unit = unit_data['unit_combo'].get()
                unit_special_rules = []
                if faction in self.faction_data:
                    unit_data_obj = next((u for u in self.faction_data[faction] if u['name'] == unit), None)
                    if unit_data_obj:
                        unit_special_rules = unit_data_obj.get('special_rules_attack', [])
                
                # Get selected attacker special rules
                selected_rules = []
                for i in range(0, len(self.special_rule_widgets), 2):
                    rule = self.special_rule_widgets[i].get()
                    if rule:
                        selected_rules.append(rule)
                
                # Combine all special rules
                all_special_rules = weapon_special_rules + unit_special_rules + selected_rules
                
                if all_special_rules:
                    special_rules_label.config(text=f"Special Rules: {', '.join(all_special_rules)}")
                else:
                    special_rules_label.config(text="No special rules")

                # Update weapon stats display
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
        
        # Bind the update function to weapon selection
        weapon_combo.bind('<<ComboboxSelected>>', update_special_rules)
        
        # Store widgets and their values
        unit_data['weapon_widgets'].extend([quantity, weapon_combo, add_button if row == 0 else remove_button])
        
        # Update button position
        self.update_button_position()
        
    def remove_weapon_row(self, row, unit_index):
        """Remove a weapon selection row"""
        unit_data = self.attacker_units[unit_index]
        start_idx = row * 3
        # Destroy all widgets in the row (quantity, weapon, and remove button)
        for widget in unit_data['weapon_widgets'][start_idx:start_idx + 3]:
            widget.destroy()
        # Remove the widgets from our list
        unit_data['weapon_widgets'] = unit_data['weapon_widgets'][:start_idx] + unit_data['weapon_widgets'][start_idx + 3:]
        
        # Update button position
        self.update_button_position()

    def create_defender_section(self):
        """Create the defender selection interface"""
        # Defender label
        ttk.Label(self.main_frame, text="Defender", font=('Arial', 12, 'bold')).grid(row=7, column=0, columnspan=2, pady=5)
        
        # Faction selection
        ttk.Label(self.main_frame, text="Faction:").grid(row=8, column=0, sticky=tk.W)
        self.defender_faction = ttk.Combobox(self.main_frame, values=sorted(self.faction_data.keys()), width=40)
        self.defender_faction.grid(row=8, column=1, sticky=(tk.W, tk.E), padx=5)
        self.defender_faction.bind('<<ComboboxSelected>>', self.update_defender_units)
        self.defender_faction.bind('<KeyRelease>', self.filter_defender_faction)
        
        # Unit selection
        ttk.Label(self.main_frame, text="Unit:").grid(row=9, column=0, sticky=tk.W)
        self.defender_unit = ttk.Combobox(self.main_frame, width=40)
        self.defender_unit.grid(row=9, column=1, sticky=(tk.W, tk.E), padx=5)
        self.defender_unit.bind('<<ComboboxSelected>>', self.update_defender_models)
        self.defender_unit.bind('<KeyRelease>', self.filter_defender_unit)
        
        # Model selection
        ttk.Label(self.main_frame, text="Model:").grid(row=10, column=0, sticky=tk.W)
        self.defender_model = ttk.Combobox(self.main_frame, width=40)
        self.defender_model.grid(row=10, column=1, sticky=(tk.W, tk.E), padx=5)
        self.defender_model.bind('<KeyRelease>', self.filter_defender_model)
        
        # Add label for defender model stats
        self.defender_model_stats_label = ttk.Label(self.main_frame, text="", wraplength=400)
        self.defender_model_stats_label.grid(row=11, column=0, columnspan=2, sticky=tk.W, padx=5)
        
        # Add label for defender special rules
        self.defender_special_rules_label = ttk.Label(self.main_frame, text="", wraplength=400)
        self.defender_special_rules_label.grid(row=12, column=0, columnspan=2, sticky=tk.W, padx=5)
        
        # Defender special rules section
        ttk.Label(self.main_frame, text="Defender Special Rules:", font=('Arial', 10)).grid(row=13, column=0, columnspan=2, sticky=tk.W, pady=(10,5))
        
        # Defender special rules frame
        self.defender_special_rules_frame = ttk.Frame(self.main_frame)
        self.defender_special_rules_frame.grid(row=14, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0,10))
        
        # List to store defender special rule widgets
        self.defender_special_rule_widgets = []
        
        # Add initial defender special rule row
        self.add_defender_special_rule_row()
        
    def update_defender_units(self, event=None):
        """Update available units based on selected faction"""
        faction = self.defender_faction.get()
        if faction in self.faction_data:
            # Extract unit names from the array of units
            units = [unit['name'] for unit in self.faction_data[faction]]
            self.defender_unit['values'] = sorted(units)
            self.defender_unit.set('')  # Clear current selection
            self.defender_model.set('')  # Clear model selection
            
    def update_defender_models(self, event=None):
        """Update available models based on selected unit"""
        faction = self.defender_faction.get()
        unit = self.defender_unit.get()
        
        print(f"Selected defender faction: {faction}")
        print(f"Selected defender unit: {unit}")
        
        if faction in self.faction_data:
            print("Defender faction found in data")
            # Find the selected unit in the faction data
            unit_data = next((u for u in self.faction_data[faction] if u['name'] == unit), None)
            print(f"Defender unit data found: {unit_data is not None}")
            if unit_data:
                print(f"Defender unit data keys: {unit_data.keys()}")
                # Get models from the unit data
                if 'models' in unit_data:
                    models = list(unit_data['models'].keys())
                    print(f"Available defender models: {models}")
                    self.defender_model['values'] = sorted(models)
                    # Select the model with the shortest name as default
                    if models:
                        default_model = min(models, key=len)
                        self.defender_model.set(default_model)
                        # Update model stats display for default model
                        self.update_defender_model_stats(unit_data['models'][default_model])
                else:
                    print("No models found in unit data, using unit name as model")
                    self.defender_model['values'] = [unit]  # Use unit name as model name
                    self.defender_model.set(unit)  # Set default to unit name
                    # Update model stats display for unit
                    self.update_defender_model_stats(unit_data)
            else:
                print("Defender unit data not found")
                self.defender_model_stats_label.config(text="")
                self.defender_special_rules_label.config(text="")
        else:
            print("Defender faction not found in data")
            print(f"Available factions: {list(self.faction_data.keys())}")
            self.defender_model_stats_label.config(text="")
            self.defender_special_rules_label.config(text="")
            
        # Bind the model selection event to update stats
        self.defender_model.bind('<<ComboboxSelected>>', self.on_defender_model_selected)
            
    def on_defender_model_selected(self, event=None):
        """Handle defender model selection"""
        faction = self.defender_faction.get()
        unit = self.defender_unit.get()
        model = self.defender_model.get()
        
        if faction in self.faction_data:
            unit_data = next((u for u in self.faction_data[faction] if u['name'] == unit), None)
            if unit_data and 'models' in unit_data and model in unit_data['models']:
                self.update_defender_model_stats(unit_data['models'][model])
            else:
                self.defender_model_stats_label.config(text="")
                self.defender_special_rules_label.config(text="")
            
    def update_defender_model_stats(self, model_data):
        """Update the defender model stats display"""
        stats = []
        if 'T' in model_data:
            stats.append(f"T: {model_data['T']}")
        if 'SV' in model_data:
            stats.append(f"SV: {model_data['SV']}")
        if 'W' in model_data:
            stats.append(f"W: {model_data['W']}")
        if 'Inv' in model_data:
            stats.append(f"Inv: {model_data['Inv']}")
        if 'Fnp' in model_data:
            stats.append(f"FNP: {model_data['Fnp']}")
        
        if stats:
            self.defender_model_stats_label.config(text=f"Model Stats: {', '.join(stats)}")
        else:
            self.defender_model_stats_label.config(text="No model stats available")
            
        # Update special rules display
        faction = self.defender_faction.get()
        unit = self.defender_unit.get()
        if faction in self.faction_data:
            unit_data = next((u for u in self.faction_data[faction] if u['name'] == unit), None)
            if unit_data:
                special_rules = unit_data.get('special_rules_defence', [])
                if special_rules:
                    self.defender_special_rules_label.config(text=f"Unit Special Rules: {', '.join(special_rules)}")
                else:
                    self.defender_special_rules_label.config(text="No unit special rules")
            else:
                self.defender_special_rules_label.config(text="")
        else:
            self.defender_special_rules_label.config(text="")

    def filter_defender_faction(self, event=None):
        """Filter defender faction combobox based on user input"""
        value = self.defender_faction.get().lower()
        if value == '':
            self.defender_faction['values'] = sorted(self.faction_data.keys())
        else:
            data = []
            for item in self.faction_data.keys():
                if value.lower() in item.lower():
                    data.append(item)
            self.defender_faction['values'] = sorted(data)

    def filter_defender_unit(self, event=None):
        """Filter defender unit combobox based on user input"""
        value = self.defender_unit.get().lower()
        faction = self.defender_faction.get()
        if faction in self.faction_data:
            units = [unit['name'] for unit in self.faction_data[faction]]
            if value == '':
                self.defender_unit['values'] = sorted(units)
            else:
                data = []
                for item in units:
                    if value.lower() in item.lower():
                        data.append(item)
                self.defender_unit['values'] = sorted(data)

    def filter_defender_model(self, event=None):
        """Filter defender model combobox based on user input"""
        value = self.defender_model.get().lower()
        faction = self.defender_faction.get()
        unit = self.defender_unit.get()
        if faction in self.faction_data:
            unit_data = next((u for u in self.faction_data[faction] if u['name'] == unit), None)
            if unit_data and 'models' in unit_data:
                models = list(unit_data['models'].keys())
                if value == '':
                    self.defender_model['values'] = sorted(models)
                else:
                    data = []
                    for item in models:
                        if value.lower() in item.lower():
                            data.append(item)
                    self.defender_model['values'] = sorted(data)
                    
                # Update model stats if a model is selected
                selected_model = self.defender_model.get()
                if selected_model in unit_data['models']:
                    self.update_defender_model_stats(unit_data['models'][selected_model])
                else:
                    self.defender_model_stats_label.config(text="")
                    self.defender_special_rules_label.config(text="")
            else:
                self.defender_model_stats_label.config(text="")
                self.defender_special_rules_label.config(text="")
        else:
            self.defender_model_stats_label.config(text="")
            self.defender_special_rules_label.config(text="")

    def add_attacker_special_rule_row(self):
        """Add a new row for special rule selection"""
        row = len(self.special_rule_widgets) // 2  # Each row has 2 widgets
        
        # Special rule selection
        special_rule_options = SPECIAL_RULES
        special_rule_combo = ttk.Combobox(self.special_rules_frame, 
                                        values=special_rule_options,
                                        width=40)
        special_rule_combo.grid(row=row, column=0, padx=5, pady=2)
        
        # Add button for first row only
        if row == 0:
            add_button = ttk.Button(self.special_rules_frame, text="+", width=3,
                                  command=self.add_attacker_special_rule_row)
            add_button.grid(row=row, column=1, padx=5)
        else:
            remove_button = ttk.Button(self.special_rules_frame, text="-", width=3,
                                     command=lambda: self.remove_special_rule_row(row))
            remove_button.grid(row=row, column=1, padx=5)
        
        # Store widgets
        self.special_rule_widgets.extend([special_rule_combo, add_button if row == 0 else remove_button])
        
    def remove_special_rule_row(self, row):
        """Remove a special rule selection row"""
        start_idx = row * 2
        # Destroy all widgets in the row (special rule combo and remove button)
        for widget in self.special_rule_widgets[start_idx:start_idx + 2]:
            widget.destroy()
        # Remove the widgets from our list
        self.special_rule_widgets = self.special_rule_widgets[:start_idx] + self.special_rule_widgets[start_idx + 2:]
        
        # Update button position
        self.update_button_position()

    def add_defender_special_rule_row(self):
        """Add a new row for defender special rule selection"""
        row = len(self.defender_special_rule_widgets) // 2  # Each row has 2 widgets
        
        # Special rule selection
        special_rule_options = [""] + sorted(["-1 AP (Armor of Contempt)", "-1 Damage", "-1 to be Hit",
                                               "-1 to be Wounded", "Cover", "Feel No Pain 4+",
                                               "Feel No Pain 5+", "Feel No Pain 6+", "Half Damage","Smoke",
                                               "Invulnerable Save 4+","Invulnerable Save 5+","Invulnerable Save 6+"])
        special_rule_combo = ttk.Combobox(self.defender_special_rules_frame, 
                                        values=special_rule_options,
                                        width=40)
        special_rule_combo.grid(row=row, column=0, padx=5, pady=2)
        
        # Add button for first row only
        if row == 0:
            add_button = ttk.Button(self.defender_special_rules_frame, text="+", width=3,
                                  command=self.add_defender_special_rule_row)
            add_button.grid(row=row, column=1, padx=5)
        else:
            remove_button = ttk.Button(self.defender_special_rules_frame, text="-", width=3,
                                     command=lambda: self.remove_defender_special_rule_row(row))
            remove_button.grid(row=row, column=1, padx=5)
        
        # Store widgets
        self.defender_special_rule_widgets.extend([special_rule_combo, add_button if row == 0 else remove_button])
        
    def remove_defender_special_rule_row(self, row):
        """Remove a defender special rule selection row"""
        start_idx = row * 2
        # Destroy all widgets in the row (special rule combo and remove button)
        for widget in self.defender_special_rule_widgets[start_idx:start_idx + 2]:
            widget.destroy()
        # Remove the widgets from our list
        self.defender_special_rule_widgets = self.defender_special_rule_widgets[:start_idx] + self.defender_special_rule_widgets[start_idx + 2:]
        
        # Update button position
        self.update_button_position()

    def update_button_position(self):
        """Update the position of the Run Simulation button and Debug Options section"""
        # Calculate the row based on the number of weapon rows and special rule rows
        max_weapon_rows = 0
        for unit_data in self.attacker_units:
            weapon_rows = len(unit_data['weapon_widgets']) // 3
            max_weapon_rows = max(max_weapon_rows, weapon_rows)
            
        attacker_special_rule_rows = len(self.special_rule_widgets) // 2
        defender_special_rule_rows = len(self.defender_special_rule_widgets) // 2
        
        # Find the next available row after defender special rules
        # Defender special rules frame is at row 14, so add the number of defender special rule rows
        base_row = 14 + defender_special_rule_rows
        
        # Place Output Options section
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ttk.Label) and widget.cget("text") == "Output Options":
                widget.grid(row=base_row, column=0, columnspan=2, pady=(15,5))
            elif isinstance(widget, ttk.Label) and widget.cget("text") == "Histogram Type:":
                widget.grid(row=base_row+1, column=0, sticky=tk.W)
            elif isinstance(widget, ttk.Combobox) and widget == self.histogram_type:
                widget.grid(row=base_row+1, column=1, sticky=(tk.W, tk.E), padx=5)
            elif isinstance(widget, ttk.Label) and widget.cget("text") == "Data Type:":
                widget.grid(row=base_row+2, column=0, sticky=tk.W)
            elif isinstance(widget, ttk.Combobox) and widget == self.data_type:
                widget.grid(row=base_row+2, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Place Debug Options section
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ttk.Label) and widget.cget("text") == "Debug Options":
                widget.grid(row=base_row+3, column=0, columnspan=2, pady=(15,5))
            elif isinstance(widget, ttk.Checkbutton) and widget.cget("text") == "Enable Debug Output":
                widget.grid(row=base_row+4, column=0, columnspan=2, sticky=tk.W, pady=(0,10))
        
        # Remove button from current position if it exists
        self.run_button.grid_remove()
        
        # Place button in new position
        self.run_button.grid(row=base_row+5, column=0, columnspan=3, pady=10)

    def run_simulation(self):
        """Run the combat simulation with the selected options"""
        try:
            # Get attacker data
            attacker_faction = self.attacker_faction.get()
            attacker_range = int(self.attacker_range.get())  # Get the range from the new field
            
            # Get defender data
            defender_faction = self.defender_faction.get()
            defender_unit = self.defender_unit.get()
            defender_model = self.defender_model.get()
            
            # Get output options
            histogram_type = self.histogram_type.get()
            data_type = self.data_type.get()
            
            # Validate inputs
            if not all([attacker_faction, defender_faction, defender_unit, defender_model]):
                messagebox.showerror("Error", "Please select all required fields")
                return
            
            # Get weapons data from all attacker units
            all_weapons_data = []
            for unit_data in self.attacker_units:
                unit = unit_data['unit_combo'].get()
                if not unit:
                    continue
                    
                # Get weapons and quantities for this unit
                for i in range(0, len(unit_data['weapon_widgets']), 3):
                    if i + 1 < len(unit_data['weapon_widgets']):
                        try:
                            quantity = int(unit_data['weapon_widgets'][i].get())
                            weapon_name = unit_data['weapon_widgets'][i + 1].get()
                            if weapon_name:  # Only add if a weapon was selected
                                all_weapons_data.append((quantity, weapon_name, attacker_range))
                        except ValueError:
                            messagebox.showerror("Error", "Weapon quantities must be integers")
                            return
            
            if not all_weapons_data:
                messagebox.showerror("Error", "Please select at least one weapon")
                return
            
            # Get selected attacker special rules
            selected_attacker_special_rules = []
            for i in range(0, len(self.special_rule_widgets), 2):
                rule = self.special_rule_widgets[i].get()
                if rule:  # Only add if a rule was selected
                    selected_attacker_special_rules.append(rule)
            
            # Get selected defender special rules
            selected_defender_special_rules = []
            for i in range(0, len(self.defender_special_rule_widgets), 2):
                rule = self.defender_special_rule_widgets[i].get()
                if rule:  # Only add if a rule was selected
                    selected_defender_special_rules.append(rule)
            
            # Get unit data
            defender_unit_data = next((u for u in self.faction_data[defender_faction] if u['name'] == defender_unit), None)
            
            if not defender_unit_data:
                messagebox.showerror("Error", "Could not find defender unit data")
                return
            
            # Create defender model
            defender_model_data = defender_unit_data.get('models', {}).get(defender_model, {})
            defender = Model(
                name=defender_model,
                toughness=defender_model_data.get('T', 4),
                save=defender_model_data.get('SV', 4),
                wounds=defender_model_data.get('W', 1),
                current_wounds=defender_model_data.get('W', 1),  # Initialize current_wounds to full wounds
                total_models=defender_unit_data.get('total_models', 1),
                invulnerable_save=defender_model_data.get('Inv'),
                feel_no_pain=defender_model_data.get('Fnp'),
                keywords=defender_unit_data.get('keywords', []),
                special_rules=defender_unit_data.get('special_rules_defence', []) + selected_defender_special_rules  # Add selected defender special rules
            )
            
            # Create weapons
            weapons = []
            for unit_data in self.attacker_units:
                unit = unit_data['unit_combo'].get()
                if not unit:
                    continue
                    
                # Get unit data for this attacker
                attacker_unit_data = next((u for u in self.faction_data[attacker_faction] if u['name'] == unit), None)
                if not attacker_unit_data:
                    continue
                
                # Create weapons for this unit
                for i in range(0, len(unit_data['weapon_widgets']), 3):
                    if i + 1 < len(unit_data['weapon_widgets']):
                        quantity = int(unit_data['weapon_widgets'][i].get())
                        weapon_name = unit_data['weapon_widgets'][i + 1].get()
                        if weapon_name:
                            weapon_data = attacker_unit_data['weapons'][weapon_name]
                            try:
                                tmp_range = int(weapon_data['Range'])
                            except ValueError:
                                tmp_range = weapon_data['Range']
                            weapon = Weapon(
                                name=weapon_name,
                                weapon_type=weapon_data['type'],
                                range=tmp_range,
                                attacks=int(weapon_data['A']),
                                skill=int(weapon_data.get('WS', weapon_data.get('BS', 3))),
                                strength=int(weapon_data['S']),
                                ap=int(weapon_data['AP']),
                                damage=weapon_data['D'],
                                special_rules=weapon_data.get('Keywords', []) + selected_attacker_special_rules + attacker_unit_data['special_rules_attack'],
                                target_range=attacker_range
                            )
                            weapons.extend([weapon] * quantity)
            
            # Run simulation
            results = self.simulator.simulate_attacks(weapons, defender, attacker_range)
            
            # Create title for the plot
            attacker_units = [u['unit_combo'].get() for u in self.attacker_units if u['unit_combo'].get()]
            title = f"{' + '.join(attacker_units)} vs {defender_unit}"
            
            # Determine which plots to show based on user selections
            show_regular = histogram_type in ["Both", "Regular"]
            show_cumulative = histogram_type in ["Both", "Cumulative"]
            show_damage = data_type in ["Both", "Damage"]
            show_models = data_type in ["Both", "Models Destroyed"]
            
            # Plot results with selected options
            self.simulator.plot_results(
                results, 
                title,
                show_regular=show_regular,
                show_cumulative=show_cumulative,
                show_damage=show_damage,
                show_models=show_models
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            print(f"Error details: {str(e)}")
            import traceback
            traceback.print_exc()

    def create_output_section(self):
        """Create the output options interface"""
        # Output options label
        ttk.Label(self.main_frame, text="Output Options", font=('Arial', 12, 'bold')).grid(row=15, column=0, columnspan=2, pady=(15,5))
        
        # Histogram type selection
        ttk.Label(self.main_frame, text="Histogram Type:").grid(row=16, column=0, sticky=tk.W)
        self.histogram_type = ttk.Combobox(self.main_frame, values=["Both", "Regular", "Cumulative"], width=40)
        self.histogram_type.grid(row=16, column=1, sticky=(tk.W, tk.E), padx=5)
        self.histogram_type.set("Both")  # Set default value
        
        # Data type selection
        ttk.Label(self.main_frame, text="Data Type:").grid(row=17, column=0, sticky=tk.W)
        self.data_type = ttk.Combobox(self.main_frame, values=["Both", "Damage", "Models Destroyed"], width=40)
        self.data_type.grid(row=17, column=1, sticky=(tk.W, tk.E), padx=5)
        self.data_type.set("Both")  # Set default value
        
    def create_debug_section(self):
        """Create the debug options interface"""
        # Debug options label
        ttk.Label(self.main_frame, text="Debug Options", font=('Arial', 12, 'bold')).grid(row=19, column=0, columnspan=2, pady=(15,5))
        
        # Debug mode toggle
        self.debug_var = tk.BooleanVar(value=False)
        debug_check = ttk.Checkbutton(self.main_frame, text="Enable Debug Output", variable=self.debug_var,
                                    command=self.toggle_debug, style='White.TCheckbutton')
        debug_check.grid(row=20, column=0, columnspan=2, sticky=tk.W, pady=(0,10))
        
        # Configure white text color for the checkbox
        style = ttk.Style()
        style.configure('White.TCheckbutton', foreground='white')
        
    def toggle_debug(self):
        """Toggle debug mode in the simulator"""
        self.simulator = UnitCombatSimulator(num_simulations=10, debug=self.debug_var.get())

    def filter_attacker_faction(self, event=None):
        """Filter attacker faction combobox based on user input"""
        value = self.attacker_faction.get().lower()
        if value == '':
            self.attacker_faction['values'] = sorted(self.faction_data.keys())
        else:
            data = []
            for item in self.faction_data.keys():
                if value.lower() in item.lower():
                    data.append(item)
            self.attacker_faction['values'] = sorted(data)

    def filter_attacker_unit(self, event=None):
        """Filter attacker unit combobox based on user input"""
        value = self.attacker_unit.get().lower()
        faction = self.attacker_faction.get()
        if faction in self.faction_data:
            units = [unit['name'] for unit in self.faction_data[faction]]
            if value == '':
                self.attacker_unit['values'] = sorted(units)
            else:
                data = []
                for item in units:
                    if value.lower() in item.lower():
                        data.append(item)
                self.attacker_unit['values'] = sorted(data)

class FilteredCombobox(ttk.Frame):
    def __init__(self, parent, values, **kwargs):
        super().__init__(parent)
        
        self.values = sorted(values)
        self.filtered_values = self.values
        
        # Create the entry widget with increased width
        self.entry = ttk.Entry(self, width=40)  # Increased from default
        self.entry.pack(fill=tk.X, expand=True)
        
        # Create the listbox for filtered results with increased width
        self.listbox = tk.Listbox(self, height=5, width=40)  # Increased from default
        self.listbox.pack(fill=tk.X, expand=True)
        
        # Initially hide the listbox
        self.listbox.pack_forget()
        
        # Bind events
        self.entry.bind('<KeyRelease>', self.filter)
        self.entry.bind('<FocusOut>', self.hide_listbox)
        self.entry.bind('<FocusIn>', self.show_listbox)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        
        # Populate initial values
        self.update_listbox()


def main():
    root = tk.Tk()
    app = CombatSimulatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 