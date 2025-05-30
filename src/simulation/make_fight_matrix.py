"""
Currently working; need to fix the way phase is determined, need to clean faction names (steal from standard_simulation_gui.py);
need to check results by hand for errors.

Need to implement distance as a variable.
"""

import json
from pathlib import Path
import numpy as np
from typing import Dict, List, Tuple
import statistics
from unit_combat_simulator import UnitCombatSimulator

def load_attackers() -> Dict:
    """Load attacker configurations from attacker_array.json"""
    with open("data/configs/attacker_array.json", 'r') as f:
        return json.load(f)

def load_targets() -> List[Dict]:
    """Load target configurations from zz_standard_target_array_cover.json"""
    with open("data/configs/zz_standard_target_array_cover.json", 'r') as f:
        return json.load(f)

def determine_phase(weapons_data: List[Dict]) -> str:
    """Determine if the attack is Ranged, Melee, or Mixed based on weapon types"""
    weapon_types = set()
    for weapon in weapons_data:
        weapon_type = weapon['data'].get('Type', 'Unknown')
        weapon_types.add(weapon_type)
    
    if len(weapon_types) == 1:
        return list(weapon_types)[0]
    return "Mixed"

def run_simulation(simulator: UnitCombatSimulator, attacker_config: Dict, target_data: Dict) -> Tuple[float, float, float, float]:
    """Run a single simulation and return mean damage, std damage, mean models killed, std models killed"""
    # Create weapons for the attacker
    attacking_weapons = []
    for unit in attacker_config['units']:
        for weapon_data in unit['weapons']:
            weapon = simulator.create_weapon(unit['name'], weapon_data['name'])
            if weapon:
                # Set quantity
                weapon.attacks *= weapon_data['quantity']
                attacking_weapons.append(weapon)
    
    # Create target model
    target_model = simulator.create_target_model(target_data['name'])
    if not target_model:
        raise ValueError(f"Could not create target model for {target_data['name']}")
    
    # Run simulation
    results = simulator.simulate_attacks(attacking_weapons, target_model)
    
    # Calculate statistics
    mean_damage = float(np.mean(results["damage"]))
    std_damage = float(np.std(results["damage"]))
    mean_models = float(np.mean(results["models_destroyed"]))
    std_models = float(np.std(results["models_destroyed"]))
    
    return mean_damage, std_damage, mean_models, std_models

def main():
    # Create simulator
    simulator = UnitCombatSimulator(num_simulations=1000)
    
    # Load configurations
    attackers = load_attackers()
    targets = load_targets()
    
    # Initialize results dictionary
    results = {}
    
    # Create output directory if it doesn't exist
    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run simulations for each attacker against each target
    for designation, attacker_config in attackers.items():
        faction = attacker_config['faction']
        
        # Initialize faction in results if not exists
        if faction not in results:
            results[faction] = {}
        
        # Initialize designation in results
        results[faction][designation] = {}
        
        # Determine phase for this attacker
        phase = determine_phase(attacker_config['units'][0]['weapons'])
        
        # Run simulations against each target
        for target_data in targets:
            target_name = target_data['name']
            print(f"Simulating {faction} - {designation} vs {target_name}")
            
            try:
                # Run simulation
                mean_damage, std_damage, mean_models, std_models = run_simulation(
                    simulator, attacker_config, target_data
                )
                
                # Store results
                results[faction][designation][target_name] = {
                    'phase': phase,
                    'mean_damage': mean_damage,
                    'std_damage': std_damage,
                    'mean_models_killed': mean_models,
                    'std_models_killed': std_models
                }
            except Exception as e:
                print(f"Error simulating {faction} - {designation} vs {target_name}: {str(e)}")
                continue
    
    # Save results
    output_file = output_dir / "simulation_data.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Simulation complete. Results saved to {output_file}")

if __name__ == "__main__":
    main() 