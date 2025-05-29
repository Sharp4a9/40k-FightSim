import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from pathlib import Path
from typing import Dict, List
from combat_engine import CombatEngine, Model, Weapon
from unit_combat_simulator import UnitCombatSimulator

class StandardSimulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Standard Target Array Simulator")
        
        # Configure dark theme
        self.configure_dark_theme()
        
        # Initialize combat engine and simulator
        self.combat_engine = CombatEngine()
        self.simulator = UnitCombatSimulator(num_simulations=1000, debug=False)
        
        # Load faction data
        self.faction_data = self.load_faction_data()
        
        # Load standard target array
        self.standard_targets = self.load_standard_targets()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Initialize widget lists
        self.attacker_units = []  # List to store attacker unit widgets
        self.weapon_widgets = []
        self.special_rule_widgets = []
        
        # Create run button first
        self.run_button = ttk.Button(self.main_frame, text="Run Simulation", command=self.run_simulation)
        
        # Create all sections
        self.create_attacker_designation()
        self.create_attacker_section()
        self.create_output_section()
        self.create_debug_section()
        
        # Position the run button
        self.run_button.grid(row=11, column=0, columnspan=10, pady=20)
    
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
            if filename.endswith(".json") and not filename.startswith("zz_"):
                faction_name = filename[:-5]  # Remove .json extension
                with open(os.path.join(data_dir, filename), 'r') as f:
                    faction_data[faction_name] = json.load(f)
        return faction_data
    
    def load_standard_targets(self) -> List[Dict]:
        """Load the standard target array from JSON file"""
        try:
            with open("data/json/zz_standard_target_array.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            messagebox.showerror("Error", "Standard target array file not found!")
            return []
    
    def create_attacker_designation(self):
        """Create the attacker designation input field"""
        ttk.Label(self.main_frame, text="Attacker Designation:", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=10, pady=5, sticky=tk.W)
        self.attacker_designation = ttk.Entry(self.main_frame, width=40)
        self.attacker_designation.grid(row=1, column=0, columnspan=10, sticky=(tk.W, tk.E), padx=5, pady=5)
    
    def create_attacker_section(self):
        """Create the attacker selection interface"""
        # Attacker label
        ttk.Label(self.main_frame, text="Attacker", font=('Arial', 12, 'bold')).grid(row=2, column=0, columnspan=10, pady=5, sticky=tk.W)

        # Faction selection
        ttk.Label(self.main_frame, text="Faction:").grid(row=3, column=0, sticky=tk.W)
        self.attacker_faction = ttk.Combobox(self.main_frame, values=sorted(self.faction_data.keys()), width=40)
        self.attacker_faction.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5)
        self.attacker_faction.bind('<<ComboboxSelected>>', self.update_attacker_units)
        self.attacker_faction.bind('<KeyRelease>', self.filter_attacker_faction)

        # Add Unit button
        self.add_unit_button = ttk.Button(self.main_frame, text="Add Unit", command=self.add_attacker_unit)
        self.add_unit_button.grid(row=3, column=2, padx=5, sticky=tk.W)

        # Frame to hold all unit frames in a row (must be before add_attacker_unit)
        self.units_row_frame = ttk.Frame(self.main_frame)
        self.units_row_frame.grid(row=4, column=0, columnspan=10, sticky=(tk.W, tk.E), pady=2)

        # Add initial unit
        self.add_attacker_unit()

        # Place the initial unit frame in the units_row_frame
        self.update_unit_frames_in_row()

        # Distance to Defender (always below all units)
        ttk.Label(self.main_frame, text="Distance to Defender:").grid(row=5, column=0, sticky=tk.W)
        self.attacker_range = ttk.Entry(self.main_frame, width=5)
        self.attacker_range.grid(row=5, column=1, sticky=tk.W, padx=5)
        self.attacker_range.insert(0, "0")  # Default range

        # Special rules section
        ttk.Label(self.main_frame, text="Attacker Special Rules:", font=('Arial', 10)).grid(row=6, column=0, columnspan=10, sticky=tk.W, pady=(10,5))

        # Special rules frame
        self.special_rules_frame = ttk.Frame(self.main_frame)
        self.special_rules_frame.grid(row=7, column=0, columnspan=10, sticky=(tk.W, tk.E), pady=(0,10))

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

        # Update the layout
        self.update_unit_frames_in_row()
    
    def remove_attacker_unit(self, unit_index):
        """Remove an attacker unit"""
        if len(self.attacker_units) > 1:
            self.attacker_units[unit_index]['frame'].destroy()
            self.attacker_units.pop(unit_index)
            self.update_unit_frames_in_row()
    
    def update_unit_frames_in_row(self):
        """Update the layout of unit frames in the row"""
        for i, unit in enumerate(self.attacker_units):
            # Grid the unit frame
            unit['frame'].grid(row=0, column=i, padx=5, sticky=(tk.W, tk.E))
            # Grid the remove button
            unit['remove_button'].grid(row=0, column=1, sticky=tk.E)
            # Configure the column to expand
            self.units_row_frame.grid_columnconfigure(i, weight=1)
    
    def update_attacker_units(self, event=None):
        """Update available units when faction is selected"""
        faction = self.attacker_faction.get()
        if faction in self.faction_data:
            units = [unit["name"] for unit in self.faction_data[faction]]
            for unit in self.attacker_units:
                unit['unit_combo']['values'] = sorted(units)
    
    def update_attacker_weapons(self, event=None, unit_index=None):
        """Update available weapons when unit is selected"""
        if unit_index is None:
            return

        faction = self.attacker_faction.get()
        unit_name = self.attacker_units[unit_index]['unit_combo'].get()
        
        if faction in self.faction_data:
            for unit in self.faction_data[faction]:
                if unit["name"] == unit_name:
                    # Clear existing weapon widgets
                    for widget in self.attacker_units[unit_index]['weapon_widgets']:
                        widget.destroy()
                    self.attacker_units[unit_index]['weapon_widgets'] = []
                    
                    # Add new weapon rows
                    self.add_weapon_row(unit["weapons"], unit_index)
                    break
    
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
    
    def add_attacker_special_rule_row(self):
        """Add a new special rule row for attacker"""
        row = len(self.special_rule_widgets) // 2
        
        # Rule name
        rule_combo = ttk.Combobox(self.special_rules_frame, values=[
            "Lethal Hits", "Sustained Hits", "Devastating Wounds", "Twin-Linked",
            "Anti-Infantry", "Anti-Vehicle", "Anti-Monster", "Anti-Psyker",
            "Torrent", "Blast", "Indirect Fire", "Lance", "Melta", "Rapid Fire",
            "Assault", "Heavy", "Pistol", "Grenades", "Extra Attacks"
        ], width=30)
        rule_combo.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # Rule value
        rule_value = ttk.Entry(self.special_rules_frame, width=5)
        rule_value.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Add button for first row only
        if row == 0:
            add_button = ttk.Button(self.special_rules_frame, text="+", width=3,
                                  command=self.add_attacker_special_rule_row)
            add_button.grid(row=row, column=2, sticky=tk.W, pady=2)
        else:
            remove_button = ttk.Button(self.special_rules_frame, text="-", width=3,
                                     command=lambda r=row: self.remove_special_rule_row(r))
            remove_button.grid(row=row, column=2, sticky=tk.W, pady=2)
        
        # Add to special rule widgets list
        self.special_rule_widgets.extend([rule_combo, rule_value])
        
        # Update button position
        self.update_button_position()
    
    def remove_special_rule_row(self, row):
        """Remove a special rule row"""
        # Remove widgets
        for i in range(2):
            self.special_rule_widgets[row * 2 + i].destroy()
        self.special_rule_widgets.pop(row * 2 + 1)
        self.special_rule_widgets.pop(row * 2)
    
    def update_button_position(self):
        """Update the position of the run button"""
        # Position the run button at a fixed row after all other sections
        self.run_button.grid(row=11, column=0, columnspan=10, pady=20)
    
    def run_simulation(self):
        """Run the simulation against all standard targets"""
        # Get attacker designation
        designation = self.attacker_designation.get().strip()
        if not designation:
            messagebox.showerror("Error", "Please enter an attacker designation!")
            return
        
        # Get attacker configuration
        attacker_config = self.get_attacker_configuration()
        if not attacker_config:
            return
        
        # Create results directory if it doesn't exist
        results_dir = Path("data/results")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing results if any
        results_file = results_dir / "simulation_data.json"
        if results_file.exists():
            with open(results_file, 'r') as f:
                results = json.load(f)
        else:
            results = {}
        
        # Get faction name
        faction = self.clean_string(self.attacker_faction.get())
        
        # Initialize faction dictionary if it doesn't exist
        if faction not in results:
            results[faction] = {}
        
        # Run simulation for each target
        for target in self.standard_targets:
            # Create defender model
            model_name = next(iter(target["models"]))  # Get the first model name
            defender_model = Model(
                name=target["name"],
                toughness=target["models"][model_name]["T"],
                save=target["models"][model_name]["SV"],
                wounds=target["models"][model_name]["W"],
                current_wounds=target["models"][model_name]["W"],
                invulnerable_save=target["models"][model_name]["Inv"],
                feel_no_pain=target["models"][model_name]["Fnp"]
            )
            
            # Combine weapons from all units
            all_weapons = []
            for unit in attacker_config["units"]:
                all_weapons.extend(unit["weapons"])
            
            # Determine phase based on weapon types
            weapon_types = set(weapon.weapon_type for weapon in all_weapons)
            if len(weapon_types) == 1:
                phase = next(iter(weapon_types))  # Get the single type
            else:
                phase = "Mixed"
            
            # Initialize phase dictionary if it doesn't exist
            if phase not in results[faction]:
                results[faction][phase] = {}
            
            # Initialize designation dictionary if it doesn't exist
            if designation not in results[faction][phase]:
                results[faction][phase][designation] = {}
            
            # Run simulation
            damage_results = self.simulator.simulate_attacks(
                attacking_weapons=all_weapons,
                defending_unit=defender_model,
                target_range=attacker_config["range"]
            )
            
            # Calculate statistics
            mean_damage = sum(damage_results["damage"]) / len(damage_results["damage"])
            std_damage = (sum((x - mean_damage) ** 2 for x in damage_results["damage"]) / len(damage_results["damage"])) ** 0.5
            
            # Calculate models killed
            mean_models_killed = sum(damage_results["models_destroyed"]) / len(damage_results["models_destroyed"])
            std_models_killed = (sum((x - mean_models_killed) ** 2 for x in damage_results["models_destroyed"]) / len(damage_results["models_destroyed"])) ** 0.5
            
            # Store results under the defender model name
            results[faction][phase][designation][target["name"]] = {
                "mean_damage": mean_damage,
                "std_damage": std_damage,
                "mean_models_killed": mean_models_killed,
                "std_models_killed": std_models_killed
            }
        
        # Save results
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        messagebox.showinfo("Success", f"Simulation completed and results saved to {results_file}")
    
    def get_attacker_configuration(self):
        """Get the attacker configuration from the GUI"""
        # Get faction and units
        faction = self.attacker_faction.get()
        if not faction:
            messagebox.showerror("Error", "Please select a faction!")
            return None
        
        # Get range
        try:
            range_value = int(self.attacker_range.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid range value!")
            return None
        
        # Get units and their weapons
        units = []
        for unit_widgets in self.attacker_units:
            unit_name = unit_widgets['unit_combo'].get()
            if not unit_name:
                continue
            
            # Find unit data
            unit_data = None
            for unit in self.faction_data[faction]:
                if unit["name"] == unit_name:
                    unit_data = unit
                    break
            
            if not unit_data:
                continue
            
            # Get weapons
            weapons = []
            weapon_widgets = unit_widgets['weapon_widgets']
            for i in range(0, len(weapon_widgets), 3):  # Each weapon has 3 widgets: quantity, weapon combo, button
                quantity = weapon_widgets[i].get()
                weapon_name = weapon_widgets[i + 1].get()
                if not weapon_name:
                    continue
                
                try:
                    num_weapons = int(quantity)
                except ValueError:
                    continue
                
                if weapon_name in unit_data["weapons"]:
                    weapon_data = unit_data["weapons"][weapon_name]
                    for _ in range(num_weapons):
                        weapons.append(Weapon(
                            name=weapon_name,
                            weapon_type=weapon_data["type"],
                            range=weapon_data["Range"],
                            attacks=weapon_data["A"],
                            skill=weapon_data.get("WS", weapon_data.get("BS")),
                            strength=weapon_data["S"],
                            ap=weapon_data["AP"],
                            damage=weapon_data["D"],
                            special_rules=weapon_data.get("Keywords", [])
                        ))
            
            if weapons:
                # Find the first model in the unit's models dictionary
                model_name = next(iter(unit_data["models"]))
                units.append({
                    "name": unit_name,
                    "weapons": weapons,
                    "models": unit_data["models"][model_name]
                })
        
        if not units:
            messagebox.showerror("Error", "No valid units configured!")
            return None
        
        # Get special rules
        special_rules = {}
        for i in range(0, len(self.special_rule_widgets), 2):
            rule_name = self.special_rule_widgets[i].get()
            if not rule_name:
                continue
            
            try:
                rule_value = int(self.special_rule_widgets[i + 1].get())
            except ValueError:
                continue
            
            special_rules[rule_name] = rule_value
        
        return {
            "faction": faction,
            "units": units,
            "range": range_value,
            "special_rules": special_rules
        }
    
    def create_output_section(self):
        """Create the output options section"""
        ttk.Label(self.main_frame, text="Output Options", font=('Arial', 12, 'bold')).grid(row=8, column=0, columnspan=10, pady=5, sticky=tk.W)
        
        # Number of simulations
        ttk.Label(self.main_frame, text="Number of Simulations:").grid(row=9, column=0, sticky=tk.W)
        self.num_simulations = ttk.Entry(self.main_frame, width=10)
        self.num_simulations.grid(row=9, column=1, sticky=tk.W, padx=5)
        self.num_simulations.insert(0, "1000")  # Default value
    
    def create_debug_section(self):
        """Create the debug toggle section"""
        self.debug_var = tk.BooleanVar(value=False)
        debug_check = ttk.Checkbutton(self.main_frame, text="Debug Mode", variable=self.debug_var,
                                    command=self.toggle_debug)
        debug_check.grid(row=10, column=0, sticky=tk.W, pady=5)
    
    def toggle_debug(self):
        """Toggle debug mode"""
        self.simulator.debug = self.debug_var.get()
    
    def filter_attacker_faction(self, event=None):
        """Filter attacker faction combobox"""
        value = self.attacker_faction.get().lower()
        self.attacker_faction['values'] = [f for f in sorted(self.faction_data.keys())
                                         if value in f.lower()]
    
    def filter_attacker_unit(self, event=None, unit_index=None):
        """Filter attacker unit combobox"""
        if unit_index is None:
            return
        
        faction = self.attacker_faction.get()
        if faction not in self.faction_data:
            return
        
        value = self.attacker_units[unit_index]['unit_combo'].get().lower()
        self.attacker_units[unit_index]['unit_combo']['values'] = [
            u["name"] for u in self.faction_data[faction]
            if value in u["name"].lower()
        ]

    def clean_string(self, text):
        """Remove all numbers and periods from a string"""
        return ''.join(c for c in text if not c.isdigit() and c != '.')

def main():
    root = tk.Tk()
    app = StandardSimulatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 