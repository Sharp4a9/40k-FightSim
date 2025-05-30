"""
I think it's working now; lots of time debugging the target profile.
"""

import json
from pathlib import Path
import numpy as np
from typing import Dict, List, Tuple
import statistics
from unit_combat_simulator import UnitCombatSimulator
from unit_combat_simulator import Model, Weapon

def clean_string(s: str) -> str:
    """Remove all non-alphabetical characters from a string."""
    return ''.join(c for c in s if c.isalpha())

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
        weapon_type = weapon['data'].get('type', 'Unknown')
        weapon_types.add(weapon_type)
    
    if len(weapon_types) == 1:
        return list(weapon_types)[0]
    return "Mixed"

def create_weapon(unit: dict, weapon_all: dict):
    """Create a Weapon object from the unit data"""
    # Combine weapon keywords and unit special rules
    weapon_name = weapon_all['name']
    weapon_data = weapon_all['data']
    weapon_special_rules = weapon_data.get('Keywords', [])
    unit_special_rules = unit.get('special_rules', [])
    combined_special_rules = list(set(weapon_special_rules + unit_special_rules))  # Remove duplicates
    try:
        tmp_range = int(weapon_data['Range'])
    except ValueError:
        tmp_range = weapon_data['Range']
    
    return Weapon(
        name=weapon_name,
        weapon_type=weapon_data['type'],
        range=tmp_range,
        attacks=int(weapon_data['A']),
        skill=int(weapon_data['BS'] if 'BS' in weapon_data else weapon_data['WS']),
        strength=int(weapon_data['S']),
        ap=int(weapon_data['AP']),
        damage=weapon_data['D'],
        special_rules=combined_special_rules,
        target_range=0  # Will be set when simulating attacks
    )

def run_simulation(simulator: UnitCombatSimulator, attacker_config: Dict, target_data: Dict) -> Tuple[float, float, float, float]:
    """Run a single simulation and return mean damage, std damage, mean models killed, std models killed"""
    # Create weapons for the attacker
    attacking_weapons = []
    for unit in attacker_config['units']:
        for weapon_all in unit['weapons']:
            weapon = create_weapon(unit, weapon_all)
            if weapon:
                for _ in range(weapon_all['quantity']):
                    attacking_weapons.append(weapon)
    
    # Create target model directly from target data
    model_name = list(target_data['models'].keys())[0]
    characteristics = target_data['models'][model_name]
    if characteristics['INV'] is not None:
        temp_inv = int(characteristics['INV'])
    else:
        temp_inv = None
    if characteristics['FNP'] is not None:
        temp_fnp = int(characteristics['FNP'])
    else:
        temp_fnp = None
    target_model = Model(
        name=target_data['name'],
        toughness=int(characteristics['T']),
        save=int(characteristics['SV']),
        wounds=int(characteristics['W']),
        current_wounds=int(characteristics['W']),
        total_models=target_data.get('total_models'),
        invulnerable_save=temp_inv,
        feel_no_pain=temp_fnp,
        keywords=target_data.get('keywords', []),
        special_rules=target_data.get('special_rules_defence', [])
    )
    
    # Run simulation
    results = simulator.simulate_attacks(attacking_weapons, target_model, target_range=attacker_config['target_range'])
    
    # Calculate statistics
    mean_damage = float(np.mean(results["damage"]))
    std_damage = float(np.std(results["damage"]))
    mean_models = float(np.mean(results["models_destroyed"]))
    std_models = float(np.std(results["models_destroyed"]))
    
    return mean_damage, std_damage, mean_models, std_models

def main():
    # Create simulator
    simulator = UnitCombatSimulator(num_simulations=2000)
    
    # Load configurations
    attackers = load_attackers()
    targets = load_targets()
    
    # Initialize results dictionary
    results = {}
    
    # Create output directory if it doesn't exist
    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load existing results if file exists
    output_file = output_dir / "simulation_data.json"
    if output_file.exists():
        with open(output_file, 'r') as f:
            results = json.load(f)
    
    # Run simulations for each attacker against each target
    for designation, attacker_config in attackers.items():
        faction = clean_string(attacker_config['faction'])
        
        # Initialize faction in results if not exists
        if faction not in results:
            results[faction] = {}
        
        # Skip if this designation already exists in the results
        if designation in results[faction]:
            print(f"Skipping {faction} - {designation} (already simulated)")
            continue
        
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
                print(f"Debug: Attacker config: {json.dumps(attacker_config, indent=2)}")
                print(f"Debug: Target data: {json.dumps(target_data, indent=2)}")
                import traceback
                traceback.print_exc()
                continue
    
    # Save results (appending to existing data)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Simulation complete. Results saved to {output_file}")

if __name__ == "__main__":
    main() 