import json
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Optional
from combat_engine import CombatEngine, Weapon, Model
import os

class UnitCombatSimulator:
    def __init__(self, num_simulations: int = 100, debug: bool = False):
        self.num_simulations = num_simulations
        self.combat_engine = CombatEngine(debug=debug)
        self.units_data = self._load_units_data()
    
    def _load_units_data(self) -> Dict:
        """Load units data from JSON files"""
        faction_data = {}
        data_dir = "data/json"
        for filename in os.listdir(data_dir):
            if filename.endswith(".json"):
                faction_name = filename[:-5]  # Remove .json extension
                with open(os.path.join(data_dir, filename), 'r') as f:
                    faction_data[faction_name] = json.load(f)
        return faction_data
    
    def get_unit_names(self) -> List[str]:
        """Get list of all unit names in the data"""
        unit_names = []
        for faction_data in self.units_data.values():
            for unit in faction_data:
                unit_names.append(unit['name'])
        return sorted(unit_names)
    
    def get_unit_weapons(self, unit_name: str) -> List[str]:
        """Get list of all weapons for a given unit"""
        for faction_data in self.units_data.values():
            for unit in faction_data:
                if unit['name'] == unit_name:
                    return list(unit['weapons'].keys())
        return []
    
    def create_weapon(self, unit_name: str, weapon_name: str) -> Optional[Weapon]:
        """Create a Weapon object from the unit data"""
        for faction_data in self.units_data.values():
            for unit in faction_data:
                if unit['name'] == unit_name:
                    print(f"Looking for weapon '{weapon_name}' in unit '{unit_name}'")
                    print(f"Available weapons: {list(unit['weapons'].keys())}")
                    if weapon_name in unit['weapons']:
                        weapon_data = unit['weapons'][weapon_name]
                        print(f"Found weapon data: {weapon_data}")
                        
                        # Combine weapon keywords and unit special rules
                        weapon_special_rules = weapon_data.get('Keywords', [])
                        unit_special_rules = unit.get('special_rules', [])
                        combined_special_rules = list(set(weapon_special_rules + unit_special_rules))  # Remove duplicates
                        
                        return Weapon(
                            name=weapon_name,
                            weapon_type=weapon_data['type'],
                            range=int(weapon_data['Range']),
                            attacks=int(weapon_data['A']),
                            skill=int(weapon_data['BS'] if 'BS' in weapon_data else weapon_data['WS']),
                            strength=int(weapon_data['S']),
                            ap=int(weapon_data['AP']),
                            damage=weapon_data['D'],
                            special_rules=combined_special_rules
                        )
                    else:
                        print(f"Weapon '{weapon_name}' not found in unit '{unit_name}'")
        return None
    
    def create_target_model(self, unit_name: str) -> Optional[Model]:
        """Create a Model object from the unit data"""
        for faction_data in self.units_data.values():
            for unit in faction_data:
                if unit['name'] == unit_name:
                    characteristics = unit['models'][list(unit['models'].keys())[0]]  # Get first model's characteristics
                    return Model(
                        name=unit_name,
                        toughness=int(characteristics['T']),
                        save=int(characteristics['SV']),
                        wounds=int(characteristics['W']),
                        current_wounds=int(characteristics['W']),
                        total_models=unit.get('total_models'),
                        invulnerable_save=int(characteristics['INV']) if 'INV' in characteristics else None,
                        feel_no_pain=int(characteristics['FNP']) if 'FNP' in characteristics else None,
                        keywords=unit.get('keywords', []),
                        special_rules=unit.get('special_rules', [])
                    )
        return None
    
    def simulate_attacks(self, 
                        attacking_weapons: List[Weapon], 
                        defending_unit: Model) -> Dict[str, np.ndarray]:
        """
        Simulate multiple attacks from a unit against a defending unit.
        
        Args:
            attacking_weapons: List of weapons in the attacking unit
            defending_unit: The defending unit model
            
        Returns:
            Dictionary containing arrays of damage and models destroyed for each simulation
        """
        damage_results = []
        models_destroyed_results = []
        
        for _ in range(self.num_simulations):
            # Reset defending unit's wounds for each simulation
            defending_unit.current_wounds = defending_unit.wounds
            
            # Track if we've used the Reroll 1 Hit Roll and Reroll 1 Wound Roll
            hit_reroll_used = False
            wound_reroll_used = False
            
            # Calculate total damage and models destroyed
            total_damage = 0
            for weapon in attacking_weapons:
                # Check if any weapon has the Reroll 1 Hit Roll or Reroll 1 Wound Roll special rule
                has_reroll_1_hit = any("Reroll 1 Hit Roll" in w.special_rules for w in attacking_weapons)
                has_reroll_1_wound = any("Reroll 1 Wound Roll" in w.special_rules for w in attacking_weapons)
                
                # Pass the reroll tracking to the combat engine
                results = self.combat_engine.resolve_attacks(weapon, defending_unit, 
                                                          can_reroll_1_hit=has_reroll_1_hit and not hit_reroll_used,
                                                          can_reroll_1_wound=has_reroll_1_wound and not wound_reroll_used)
                
                # Update reroll tracking
                if has_reroll_1_hit and not hit_reroll_used and results.get("used_reroll_1_hit", False):
                    hit_reroll_used = True
                if has_reroll_1_wound and not wound_reroll_used and results.get("used_reroll_1_wound", False):
                    wound_reroll_used = True
                
                total_damage += results["damage_dealt"]
            
            # Calculate models destroyed based on total damage
            models_destroyed = total_damage // defending_unit.wounds  # Integer division to round down
            
            damage_results.append(total_damage)
            models_destroyed_results.append(models_destroyed)

        return {
            "damage": np.array(damage_results),
            "models_destroyed": np.array(models_destroyed_results)
        }
    
    def plot_results(self, results: Dict[str, np.ndarray], title: str = "Combat Simulation Results",
                    show_regular: bool = True, show_cumulative: bool = True,
                    show_damage: bool = True, show_models: bool = True):
        """
        Create histograms and cumulative histograms for damage and models destroyed.
        
        Args:
            results: Dictionary containing arrays of damage and models destroyed
            title: Title for the plot
            show_regular: Whether to show regular histograms
            show_cumulative: Whether to show cumulative histograms
            show_damage: Whether to show damage plots
            show_models: Whether to show models destroyed plots
        """
        # Calculate number of rows and columns needed
        n_rows = sum([show_regular, show_cumulative])
        n_cols = sum([show_damage, show_models])
        
        if n_rows == 0 or n_cols == 0:
            return
            
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(7.5 * n_cols, 5 * n_rows))
        if n_rows == 1 and n_cols == 1:
            axes = np.array([[axes]])
        elif n_rows == 1:
            axes = axes.reshape(1, -1)
        elif n_cols == 1:
            axes = axes.reshape(-1, 1)
            
        # Calculate appropriate bin ranges
        damage_bins = np.arange(min(results["damage"]), max(results["damage"]) + 2) - 0.5
        models_bins = np.arange(min(results["models_destroyed"]), max(results["models_destroyed"]) + 2) - 0.5
        
        row = 0
        col = 0
        
        # Regular histograms
        if show_regular:
            if show_damage:
                axes[row, col].hist(results["damage"], bins=damage_bins, alpha=0.7, color='blue')
                axes[row, col].set_title("Damage Distribution")
                axes[row, col].set_xlabel("Damage")
                axes[row, col].set_ylabel("Frequency")
                axes[row, col].set_xticks(range(min(results["damage"]), max(results["damage"]) + 1))
                col += 1
                
            if show_models:
                axes[row, col].hist(results["models_destroyed"], bins=models_bins, alpha=0.7, color='red')
                axes[row, col].set_title("Models Destroyed Distribution")
                axes[row, col].set_xlabel("Models Destroyed")
                axes[row, col].set_ylabel("Frequency")
                axes[row, col].set_xticks(range(min(results["models_destroyed"]), max(results["models_destroyed"]) + 1))
            row += 1
            col = 0
        
        # Cumulative histograms
        if show_cumulative:
            if show_damage:
                # Calculate survival probability (1 - cumulative probability)
                damage_hist, damage_bins = np.histogram(results["damage"], bins=damage_bins, density=True)
                damage_cumsum = np.cumsum(damage_hist) * np.diff(damage_bins)[0]
                damage_survival = 1 - damage_cumsum
                
                # Center bars on tick marks
                bar_width = 0.8  # Width of bars relative to bin width
                bin_centers = damage_bins[:-1] + 0.5  # Center of each bin
                axes[row, col].bar(bin_centers, damage_survival, width=bar_width, alpha=0.7, color='blue')
                axes[row, col].set_title("Probability of at least N damage")
                axes[row, col].set_xlabel("Damage")
                axes[row, col].set_ylabel("Probability")
                axes[row, col].set_xticks(range(min(results["damage"]), max(results["damage"]) + 1))
                col += 1
                
            if show_models:
                # Calculate survival probability (1 - cumulative probability)
                models_hist, models_bins = np.histogram(results["models_destroyed"], bins=models_bins, density=True)
                total_runs = len(results["models_destroyed"])  # Use actual number of simulations
                
                # Calculate cumulative probabilities
                cumulative_counts = np.cumsum(models_hist[::-1])[::-1]
                cumulative_probabilities = cumulative_counts #/ total_runs
                
                # Center bars on tick marks
                bar_width = 0.8  # Width of bars relative to bin width
                bin_centers = models_bins[:-1] + 0.5  # Center of each bin
                
                # Ensure bin_centers and probabilities have the same length
                if len(bin_centers) != len(cumulative_probabilities):
                    # If they don't match, use the shorter length
                    min_length = min(len(bin_centers), len(cumulative_probabilities))
                    bin_centers = bin_centers[:min_length]
                    cumulative_probabilities = cumulative_probabilities[:min_length]
                
                axes[row, col].bar(bin_centers, cumulative_probabilities, width=bar_width, alpha=0.7, color='red')
                axes[row, col].set_title("Probability of at least N models destroyed")
                axes[row, col].set_xlabel("Models Destroyed")
                axes[row, col].set_ylabel("Probability")
                axes[row, col].set_xticks(range(min(results["models_destroyed"]), max(results["models_destroyed"]) + 1))
        
        plt.suptitle(title)
        plt.tight_layout()
        plt.show()

def main():
    # Create simulator
    simulator = UnitCombatSimulator(num_simulations=100)
    
    # Print available units
    print("Available units:")
    for unit_name in simulator.get_unit_names():
        print(f"- {unit_name}")
    
    # Get user input for attacking unit and weapons
    attacking_unit = input("\nEnter attacking unit name: ")
    print(f"\nAvailable weapons for {attacking_unit}:")
    for weapon_name in simulator.get_unit_weapons(attacking_unit):
        print(f"- {weapon_name}")
    
    # Get user input for weapons to use
    selected_weapons = []
    while True:
        weapon_name = input("\nEnter weapon name to add (or 'done' to finish): ")
        if weapon_name.lower() == 'done':
            break
        weapon = simulator.create_weapon(attacking_unit, weapon_name)
        if weapon:
            selected_weapons.append(weapon)
        else:
            print("Invalid weapon name")
    
    # Get user input for target unit
    target_unit = input("\nEnter target unit name: ")
    target = simulator.create_target_model(target_unit)
    
    if not target:
        print("Invalid target unit name")
        return
    
    # Run simulation
    results = simulator.simulate_attacks(selected_weapons, target)
    simulator.plot_results(results, f"{attacking_unit} vs {target_unit}")

if __name__ == "__main__":
    main() 