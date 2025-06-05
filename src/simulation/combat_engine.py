"""
A note on abilities that deal mortal wounds:
Some units have abilities that deal mortal wounds. I have coded these abilies as weapons with the Mortal special rule.
This special rule, combined with Overkill, allows the weapon to deal mortal wounds across multiple models.

Attacker Special Rules Implemented:

- Sustained Hits X
- Sustained Hits D3
- Lethal Hits
- Lethal Hits [Keyword]
- Torrent
- Reroll Hits
- Reroll Wounds
- Reroll Damage
- Reroll Hits 1
- Reroll Wounds 1
- Reroll Damage 1
- Reroll Hits [Keyword]
- Reroll Wounds [Keyword]
- Reroll Damage [Keyword]
- Reroll 1 [Keyword] (implementing)
- Devastating Wounds
- Twin-Linked
- Anti-[Keyword] X+
- Critical Hits X+
- Critical Wounds X+
- Mortal
- Overkill
- Ignores Cover
- Blast (assumes minimum legal unit size; might be updated to allow for user to specify unit size)
- Ignore Hit Modifiers
- Ignore Wound Modifiers
- Ignore Modifiers
- +1 to Hit 
- +1 to Wound 
- +1 AP
- +1 to Hit [Keyword]
- +1 to Wound [Keyword]
- Melta X
- Rapid Fire X (works for integer and random values)


Defender Special Rules Implemented:
- -1 Damage
- Half Damage
- -1 to be Hit
- -1 to be Hit in Melee
- Stealth
- -1 to be Wounded
- -1 to be Wounded in Melee
- Cover (Only if attacker weapon is ranged)
- [Keyword] FNP X+
- -1 AP (Armor of Contempt)
- -1 AP in Melee
- Invulnerable Save Ranged X+
- Invulnerable Save Melee X+
- -1 to be Wounded by High Strength 
- Invulnerable Save X+
"""

import random
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass, field
import re
import math as m

@dataclass
class Model:
    name: str
    toughness: int
    save: int
    wounds: int
    current_wounds: int
    total_models: int = 1  # Default to 1 for single models
    invulnerable_save: Optional[int] = None
    feel_no_pain: Optional[int] = None
    keywords: List[str] = field(default_factory=list)
    special_rules: List[str] = field(default_factory=list)

@dataclass
class Weapon:
    name: str
    range: int
    attacks: Union[int, str]  # Can be an integer or a string like "D6+3"
    skill: int  # BS or WS
    strength: int
    ap: int
    damage: Union[int, str]  # Can be an integer or a string like "D6+3"
    weapon_type: str  # "melee" or "ranged"
    special_rules: List[str]
    one_use_rules: Dict[str, bool] = field(default_factory=dict)
    target_range: int = 0  # Distance to target in inches

class CombatEngine:
    def __init__(self, debug: bool = False):
        self.hit_modifiers = 0
        self.wound_modifiers = 0
        self.save_modifiers = 0
        self.debug = debug

    def debug_print(self, message: str):
        """Print message only if debug mode is enabled"""
        if self.debug:
            print(message)

    def roll_dice(self) -> int:
        """Roll a single D6"""
        return random.randint(1, 6)

    def find_rapid_fire_bonus(self, rapid_fire_value: str) -> int:
        """Find the Rapid Fire bonus from the Rapid Fire value"""
        # Handle D6+X format
        match = re.match(r'D6\+(\d+)', rapid_fire_value)
        if match:
            result = self.roll_dice() + int(match.group(1))
            self.debug_print(f"  D6+X attacks result: {result}")
            bonus = result
            
        # Handle D6 format
        if rapid_fire_value == 'D6':
            result = self.roll_dice()
            self.debug_print(f"  D6 attacks result: {result}")
            bonus = result
            
        # Handle D3+X format
        match = re.match(r'D3\+(\d+)', rapid_fire_value)
        if match:
            result = random.randint(1, 3) + int(match.group(1))
            self.debug_print(f"  D3+X attacks result: {result}")
            bonus = result
            
        # Handle D3 format
        if rapid_fire_value == 'D3':
            result = random.randint(1, 3)
            self.debug_print(f"  D3 attacks result: {result}")
            bonus = result
            
        # Handle 2D6 format
        match = re.match(r'(\d+)D6', rapid_fire_value)
        if match:
            num_dice = int(match.group(1))
            result = sum(self.roll_dice() for _ in range(num_dice))
            self.debug_print(f"  XD6 attacks result: {result}")
            bonus = result
            
        # If we can't parse it, return 1 as a fallback
        if bonus == 0:
            self.debug_print(f"  Using fallback attacks value: 1")
            bonus = 1

        return bonus
    
    def roll_attacks(self, attacks_value: Union[int, str], weapon: Weapon, target: Model) -> int:
        """Calculate number of attacks based on the weapon's attacks value"""
        self.debug_print(f"  Rolling attacks for value: {attacks_value}")
        base_attacks = 0
        
        if isinstance(attacks_value, int):
            self.debug_print(f"  Integer attacks value: {attacks_value}")
            base_attacks = attacks_value
            # Apply Blast rule if present
            if "Blast" in weapon.special_rules:
                blast_bonus = m.floor(target.total_models / 5)
                self.debug_print(f"  Weapon has Blast rule - adding {blast_bonus} attacks for {target.total_models} models")
                base_attacks += blast_bonus
            return base_attacks
            
        # Handle D6+X format
        match = re.match(r'D6\+(\d+)', attacks_value)
        if match:
            result = self.roll_dice() + int(match.group(1))
            self.debug_print(f"  D6+X attacks result: {result}")
            base_attacks = result
            
        # Handle D6 format
        if attacks_value == 'D6':
            result = self.roll_dice()
            self.debug_print(f"  D6 attacks result: {result}")
            base_attacks = result
            
        # Handle D3+X format
        match = re.match(r'D3\+(\d+)', attacks_value)
        if match:
            result = random.randint(1, 3) + int(match.group(1))
            self.debug_print(f"  D3+X attacks result: {result}")
            base_attacks = result
            
        # Handle D3 format
        if attacks_value == 'D3':
            result = random.randint(1, 3)
            self.debug_print(f"  D3 attacks result: {result}")
            base_attacks = result
            
        # Handle 2D6 format
        match = re.match(r'(\d+)D6', attacks_value)
        if match:
            num_dice = int(match.group(1))
            result = sum(self.roll_dice() for _ in range(num_dice))
            self.debug_print(f"  XD6 attacks result: {result}")
            base_attacks = result
            
        # If we can't parse it, return 1 as a fallback
        if base_attacks == 0:
            self.debug_print(f"  Using fallback attacks value: 1")
            base_attacks = 1
            
        # Apply Blast rule if present
        if "Blast" in weapon.special_rules:
            blast_bonus = m.floor(target.total_models / 5)
            self.debug_print(f"  Weapon has Blast rule - adding {blast_bonus} attacks for {target.total_models} models")
            base_attacks += blast_bonus
            
        return base_attacks

    def roll_damage(self, damage_value: Union[int, str], weapon: Weapon, target: Model, is_critical_hit: bool = False, one_use_rules: Dict[str, bool] = None) -> int:
        """Calculate damage based on the weapon's damage value"""
        self.debug_print(f"  Rolling damage for value: {damage_value}")
        if isinstance(damage_value, int):
            self.debug_print(f"  Integer damage value: {damage_value}")
            return damage_value
            
        # Handle D6+X format
        match = re.match(r'D6\+(\d+)', damage_value)
        if match:
            unmodified_roll = self.roll_dice()
            result = unmodified_roll + int(match.group(1))
            self.debug_print(f"  D6+X damage result: {result}")
            
            # Check if we need to reroll
            should_reroll = False
            if self.has_reroll_damage(weapon, target):
                # Reroll if the roll failed (for D6+X, we consider it failed if the expected value of the reroll is higher than the roll)
                should_reroll = unmodified_roll < 4
            elif self.has_reroll_damage_1(weapon) and unmodified_roll == 1:
                # Reroll if we rolled a 1
                should_reroll = True
            elif one_use_rules["has_reroll_1_hit_wound_or_damage"] and unmodified_roll < 4:
                should_reroll = True
                one_use_rules["has_reroll_1_hit_wound_or_damage"] = False
                self.debug_print("  Using Reroll 1 Hit or Wound or Damage special rule")

            if should_reroll:
                self.debug_print(f"  Initial damage roll {result} (unmodified {unmodified_roll}) failed or rolled a 1, attempting reroll")
                unmodified_reroll = self.roll_dice()
                result = unmodified_reroll + int(match.group(1))
                self.debug_print(f"  Reroll result: {result}")

            if one_use_rules["has_flip_a_6_damage"]:
                if should_reroll and unmodified_reroll < 4:
                    die_roll = 6
                    one_use_rules["has_flip_a_6_damage"] = False
                    self.debug_print("  Using Flip Damage Roll to 6 special rule")
                    result = die_roll + int(match.group(1))
                elif unmodified_roll < 4:
                    die_roll = 6
                    one_use_rules["has_flip_a_6_damage"] = False
                    self.debug_print("  Using Flip Damage Roll to 6 special rule")
                    result = die_roll + int(match.group(1))
            elif one_use_rules["has_flip_a_6"]:
                if should_reroll and unmodified_reroll < 4:
                    die_roll = 6
                    one_use_rules["has_flip_a_6"] = False
                    self.debug_print("  Using Flip Damage Roll to 6 special rule")
                    result = die_roll + int(match.group(1))
                elif unmodified_roll < 4:
                    die_roll = 6
                    one_use_rules["has_flip_a_6"] = False
                    self.debug_print("  Using Flip Damage Roll to 6 special rule")
                    result = die_roll + int(match.group(1))
            
            return result
            
        # Handle D6 format
        if damage_value == 'D6':
            unmodified_roll = self.roll_dice()
            result = unmodified_roll
            self.debug_print(f"  D6 damage result: {result}")
            
            # Check if we need to reroll
            should_reroll = False
            if self.has_reroll_damage(weapon, target):
                # Reroll if the roll failed (for D6+X, we consider it failed if the expected value of the reroll is higher than the roll)
                should_reroll = unmodified_roll < 4
            elif self.has_reroll_damage_1(weapon) and unmodified_roll == 1:
                # Reroll if we rolled a 1
                should_reroll = True
            elif one_use_rules["has_reroll_1_hit_wound_or_damage"] and unmodified_roll < 4:
                should_reroll = True
                one_use_rules["has_reroll_1_hit_wound_or_damage"] = False
                self.debug_print("  Using Reroll 1 Hit or Wound or Damage special rule")

            if should_reroll:
                self.debug_print(f"  Initial damage roll {result} (unmodified {unmodified_roll}) failed or rolled a 1, attempting reroll")
                unmodified_reroll = self.roll_dice()
                reroll = unmodified_reroll
                self.debug_print(f"  Reroll result: {reroll}")
                result = reroll

            if one_use_rules["has_flip_a_6_damage"]:
                if should_reroll and unmodified_reroll < 4:
                    die_roll = 6
                    one_use_rules["has_flip_a_6_damage"] = False
                    self.debug_print("  Using Flip Damage Roll to 6 special rule")
                    result = die_roll
                elif unmodified_roll < 4:
                    die_roll = 6
                    one_use_rules["has_flip_a_6_damage"] = False
                    self.debug_print("  Using Flip Damage Roll to 6 special rule")
                    result = die_roll
            elif one_use_rules["has_flip_a_6"]:
                if should_reroll and unmodified_reroll < 4:
                    die_roll = 6
                    one_use_rules["has_flip_a_6"] = False
                    self.debug_print("  Using Flip Damage Roll to 6 special rule")
                    result = die_roll
                elif unmodified_roll < 4:
                    die_roll = 6
                    one_use_rules["has_flip_a_6"] = False
                    self.debug_print("  Using Flip Damage Roll to 6 special rule")
                    result = die_roll

            return result
            
        # Handle D3+X format
        match = re.match(r'D3\+(\d+)', damage_value)
        if match:
            unmodified_roll = self.roll_dice()
            result = m.ceil(unmodified_roll/2) + int(match.group(1))
            self.debug_print(f"  D3+X damage result: {result}")
            
            # Check if we need to reroll
            should_reroll = False
            if self.has_reroll_damage(weapon, target):
                # Reroll if the roll failed (for D3+X, we consider it failed if the expected value of the reroll is higher than the roll)
                should_reroll = unmodified_roll < 3
            elif self.has_reroll_damage_1(weapon) and unmodified_roll == 1:
                # Reroll if we rolled a 1
                should_reroll = True
            elif one_use_rules["has_reroll_1_hit_wound_or_damage"] and unmodified_roll < 4:
                should_reroll = True
                one_use_rules["has_reroll_1_hit_wound_or_damage"] = False
                self.debug_print("  Using Reroll 1 Hit or Wound or Damage special rule")

            if should_reroll:
                self.debug_print(f"  Initial damage roll {result} (unmodified {unmodified_roll}) failed or rolled a 1, attempting reroll")
                unmodified_reroll = self.roll_dice()
                reroll = m.ceil(unmodified_reroll/2) + int(match.group(1))
                self.debug_print(f"  Reroll result: {reroll}")
                result = reroll
            
            return result
            
        # Handle D3 format
        if damage_value == 'D3':
            unmodified_roll = self.roll_dice()
            result = m.ceil(unmodified_roll/2)
            self.debug_print(f"  D3 damage result: {result}")
            
            # Check if we need to reroll
            should_reroll = False
            if self.has_reroll_damage(weapon, target):
                # Reroll if the roll failed (for D3, we consider it failed if the expected value of the reroll is higher than the roll)
                should_reroll = unmodified_roll < 3
            elif self.has_reroll_damage_1(weapon) and unmodified_roll == 1:
                # Reroll if we rolled a 1
                should_reroll = True
            elif one_use_rules["has_reroll_1_hit_wound_or_damage"] and unmodified_roll < 4:
                should_reroll = True
                one_use_rules["has_reroll_1_hit_wound_or_damage"] = False
                self.debug_print("  Using Reroll 1 Hit or Wound or Damage special rule")

            if should_reroll:
                self.debug_print(f"  Initial damage roll {result} (unmodified {unmodified_roll}) failed or rolled a 1, attempting reroll")
                unmodified_reroll = self.roll_dice()
                reroll = m.ceil(unmodified_reroll/2)
                self.debug_print(f"  Reroll result: {reroll}")
                result = reroll
            
            return result
            
        # Handle 2D6 format
        match = re.match(r'(\d+)D6', damage_value)
        if match:
            num_dice = int(match.group(1))
            unmodified_rolls = [self.roll_dice() for _ in range(num_dice)]
            result = sum(unmodified_rolls)
            self.debug_print(f"  XD6 damage result: {result}")
            
            # Check if we need to reroll
            should_reroll = False
            if self.has_reroll_damage(weapon, target):
                # Reroll if any die rolled a 1
                should_reroll = result < int(match.group(1)) * 3.5
            elif self.has_reroll_damage_1(weapon):
                # Reroll if any die rolled a 1
                should_reroll = 1 in unmodified_rolls
            elif one_use_rules["has_reroll_1_hit_wound_or_damage"] and unmodified_roll < 4:
                should_reroll = True
                one_use_rules["has_reroll_1_hit_wound_or_damage"] = False
                self.debug_print("  Using Reroll 1 Hit or Wound or Damage special rule")

            if should_reroll:
                self.debug_print(f"  Initial damage roll {result} (unmodified rolls {unmodified_rolls}) contains a 1, attempting reroll")
                unmodified_rerolls = [self.roll_dice() for _ in range(num_dice)]
                reroll = sum(unmodified_rerolls)
                self.debug_print(f"  Reroll result: {reroll}")
                # Use the better of the two rolls
                result = reroll
            
            return result
        
        # Handle 2D3 or 2D6 format
        if damage_value == '2D3 or 2D6':
            if is_critical_hit:
                unmodified_roll = self.roll_dice() + self.roll_dice()
            else:
                unmodified_roll = m.ceil(self.roll_dice()/2) + m.ceil(self.roll_dice()/2)
            result = unmodified_roll
            self.debug_print(f"  Damage result: {result}")
            return result
        
        # Handle D3 or 3 format
        if damage_value == 'D3 or 3':
            if is_critical_hit:
                unmodified_roll = 3
            else:
                unmodified_roll = m.ceil(self.roll_dice()/2)
            result = unmodified_roll
            self.debug_print(f"  Damage result: {result}")
            return result

        # If we can't parse it, return 1 as a fallback
        self.debug_print(f"  Using fallback damage value: 1")
        return 1

    def get_sustained_hits_value(self, weapon: Weapon) -> int:
        """Extract the number of sustained hits from weapon special rules"""
        for rule in weapon.special_rules:
            if "Sustained Hits" in rule:
                # Check for "Sustained Hits X+" pattern
                match = re.search(r'Sustained Hits (\d+)\+', rule)
                if match:
                    return int(match.group(1))
                
                # Check for "Sustained Hits D3" pattern
                if "Sustained Hits D3" in rule:
                    return random.randint(1, 3)
                
                # If no specific pattern matches, default to 1
                return 1
        return 0

    def get_critical_hit_threshold(self, weapon: Weapon) -> int:
        """Get the critical hit threshold from weapon special rules"""
        for rule in weapon.special_rules:
            if "Critical Hits" in rule:
                # Extract the number after "Critical Hits"
                match = re.search(r'Critical Hits (\d+)', rule)
                if match:
                    return int(match.group(1))
        # Default critical hit on 6
        return 6

    def get_critical_wound_threshold(self, weapon: Weapon, target: Model) -> int:
        """Get the critical wound threshold from weapon special rules"""
        # First check for Anti-[Keyword] X+ rules
        for rule in weapon.special_rules:
            if rule.startswith("Anti-"):
                # Extract the keyword and threshold
                # Format is "Anti-[Keyword] X+"
                match = re.match(r'Anti-([^ ]+) (\d+)\+', rule)
                if match:
                    keyword = match.group(1)
                    threshold = int(match.group(2))
                    # If target has the keyword, use this threshold
                    if keyword.lower() in [k.lower() for k in target.keywords]:
                        return threshold

        # If no Anti rule applies, check for Critical Wounds rule
        for rule in weapon.special_rules:
            if "Critical Wounds" in rule:
                # Extract the number after "Critical Wounds"
                match = re.search(r'Critical Wounds (\d+)', rule)
                if match:
                    return int(match.group(1))
        # Default critical wound on 6
        return 6

    def has_reroll_hits(self, weapon: Weapon, target: Model) -> bool:
        """Check if the weapon has any reroll hits special rule that applies to the target"""
        for rule in weapon.special_rules:
            if rule == "Reroll Hits":
                return True
            # Check for conditional rerolls like "Reroll Hits Vehicle"
            if rule.startswith("Reroll Hits "):
                keyword = rule.replace("Reroll Hits ", "")
                if keyword.lower() in [k.lower() for k in target.keywords]:
                    return True
        return False

    def has_reroll_hits_1(self, weapon: Weapon, target: Model) -> bool:
        """Check if the weapon has the Reroll Hits 1 special rule"""
        for rule in weapon.special_rules:
            if rule == "Reroll Hits 1":
                return True
            # Check for conditional rerolls like "Reroll Hits 1 Vehicle"
            elif rule.startswith("Reroll Hits 1 "):
                keyword = rule.replace("Reroll Hits 1 ", "")
                if keyword.lower() in [k.lower() for k in target.keywords]:
                    return True
            # Check for conditional rerolls like "Reroll Hit and Wound 1 Vehicle"
            elif rule.startswith("Reroll Hit and Wound 1 "):
                keyword = rule.replace("Reroll Hit and Wound 1 ", "")
                if keyword.lower() in [k.lower() for k in target.keywords] or keyword == "":
                    return True
        return False

    def has_reroll_1_hit_roll(self, weapon: Weapon) -> bool:
        """Check if the weapon has the Reroll 1 Hit Roll special rule"""
        return "Reroll 1 Hit Roll" in weapon.special_rules

    def has_reroll_wounds(self, weapon: Weapon, target: Model) -> bool:
        """Check if the weapon has any reroll wounds special rule that applies to the target"""
        for rule in weapon.special_rules:
            if rule == "Reroll Wounds" or rule == "Twin-Linked" or rule == "Twin Linked" or rule == "Twin-linked" or rule == "Twin linked":
                return True
            # Check for conditional rerolls like "Reroll Wounds Vehicles"
            if rule.startswith("Reroll Wounds "):
                keyword = rule.replace("Reroll Wounds ", "")
                if keyword.lower() in [k.lower() for k in target.keywords]:
                    return True
        return False

    def has_reroll_wounds_1(self, weapon: Weapon, target: Model) -> bool:
        """Check if the weapon has the Reroll Wounds 1 special rule"""
        for rule in weapon.special_rules:
            if rule == "Reroll Wounds 1":
                return True
            # Check for conditional rerolls like "Reroll Wounds 1 Vehicles"
            elif rule.startswith("Reroll Wounds 1 "):
                keyword = rule.replace("Reroll Wounds 1 ", "")
                if keyword.lower() in [k.lower() for k in target.keywords]:
                    return True
            # Check for conditional rerolls like "Reroll Hit and Wound 1 Vehicles"
            elif rule.startswith("Reroll Hit and Wound 1 "):
                keyword = rule.replace("Reroll Hit and Wound 1 ", "")
                if keyword.lower() in [k.lower() for k in target.keywords] or keyword == "":
                    return True
        return False

    def has_reroll_1_wound_roll(self, weapon: Weapon) -> bool:
        """Check if the weapon has the Reroll 1 Wound Roll special rule"""
        return "Reroll 1 Wound Roll" in weapon.special_rules

    def has_torrent(self, weapon: Weapon) -> bool:
        """Check if the weapon has the Torrent special rule"""
        return "Torrent" in weapon.special_rules

    def has_reroll_damage(self, weapon: Weapon, target: Model) -> bool:
        """Check if the weapon has any reroll damage special rule that applies to the target"""
        for rule in weapon.special_rules:
            if rule == "Reroll Damage":
                return True
            # Check for conditional rerolls like "Reroll Damage Vehicles"
            if rule.startswith("Reroll Damage "):
                keyword = rule.replace("Reroll Damage ", "")
                if keyword.lower() in [k.lower() for k in target.keywords]:
                    return True
        return False

    def has_reroll_damage_1(self, weapon: Weapon) -> bool:
        """Check if the weapon has the Reroll Damage 1 special rule"""
        return "Reroll Damage 1" in weapon.special_rules

    def has_lethal_hits(self, weapon: Weapon, target: Model) -> bool:
        """Check if the weapon has any lethal hits special rule that applies to the target"""
        for rule in weapon.special_rules:
            if rule == "Lethal Hits":
                return True
            # Check for conditional lethal hits like "Lethal Hits Vehicles"
            if rule.startswith("Lethal Hits "):
                keyword = rule.replace("Lethal Hits ", "")
                if keyword.lower() in [k.lower() for k in target.keywords]:
                    return True
        return False

    def make_hit_roll(self, weapon: Weapon, target: Model, one_use_rules: Dict[str, bool]) -> Dict[str, bool]:
        """Make a hit roll based on the weapon's skill"""
        # Check for Torrent special rule
        if self.has_torrent(weapon):
            self.debug_print("  Weapon has Torrent special rule - hit automatically succeeds")
            return {"hit": True, "critical": False}
            
        # Initial roll
        unmodified_roll = self.roll_dice()
        # Apply modifiers
        roll = unmodified_roll + self.hit_modifiers
        
        # Get critical hit threshold
        critical_threshold = self.get_critical_hit_threshold(weapon)
        
        # Check if we need to reroll
        should_reroll = False
        if self.has_reroll_hits(weapon, target):
            # Reroll if the roll failed
            should_reroll = roll < weapon.skill
        elif self.has_reroll_hits_1(weapon, target) and unmodified_roll == 1:
            # Reroll if we rolled a 1
            should_reroll = True
        elif one_use_rules["has_reroll_1_hit"] and roll < weapon.skill:
            # Reroll if we rolled a 1 and haven't used the reroll yet
            should_reroll = True
            one_use_rules["has_reroll_1_hit"] = False
            self.debug_print("  Using Reroll 1 Hit Roll special rule")
        elif one_use_rules["has_reroll_1_hit_or_wound"] and roll < weapon.skill:
            # Reroll if we rolled a 1 and haven't used the reroll yet
            should_reroll = True
            one_use_rules["has_reroll_1_hit_or_wound"] = False
            self.debug_print("  Using Reroll 1 Hit or Wound special rule")
        elif one_use_rules["has_reroll_1_hit_wound_or_damage"] and roll < weapon.skill:
            # Reroll if we rolled a 1 and haven't used the reroll yet
            should_reroll = True
            one_use_rules["has_reroll_1_hit_wound_or_damage"] = False
            self.debug_print("  Using Reroll 1 Hit or Wound or Damage special rule")
        
        if should_reroll:
            self.debug_print(f"  Initial hit roll {roll} failed or rolled a 1, attempting reroll")
            unmodified_reroll = self.roll_dice()
            reroll = unmodified_reroll + self.hit_modifiers
            self.debug_print(f"  Reroll result: {reroll}")
            unmodified_roll = unmodified_reroll
            roll = reroll
        
        # Apply a flipped 6, if any.
        if one_use_rules["has_flip_a_6_hit"] and roll < weapon.skill:
            unmodified_roll = 6
            one_use_rules["has_flip_a_6_hit"] = False
            self.debug_print("  Using Flip Hit Roll to 6 special rule")
        elif one_use_rules["has_flip_a_6_hit_wound"] and roll < weapon.skill:
            unmodified_roll = 6
            one_use_rules["has_flip_a_6_hit_wound"] = False
            self.debug_print("  Using Flip Hit or Wound Roll to 6 special rule")
        elif one_use_rules["has_flip_a_6"] and roll < weapon.skill:
            unmodified_roll = 6
            one_use_rules["has_flip_a_6"] = False
            self.debug_print("  Using Flip Hit Roll to 6 special rule")

        # Check for automatic failure on unmodified roll of 1
        if unmodified_roll == 1 and not self.has_torrent(weapon):
            self.debug_print("  Unmodified roll of 1 automatically fails (no Torrent)")
            return {"hit": False, "critical": False}
        
        # Critical hit based on threshold
        is_critical = unmodified_roll >= critical_threshold
        # Normal hit
        is_hit = is_critical or roll >= weapon.skill
        
        return {
            "hit": is_hit,
            "critical": is_critical
        }

    def make_wound_roll(self, weapon: Weapon, target: Model, is_critical_hit: bool = False, one_use_rules: Dict[str, bool] = None) -> Dict[str, bool]:
        """Make a wound roll based on strength vs toughness"""
        # Lethal Hits automatically wound on critical hits
        if is_critical_hit and self.has_lethal_hits(weapon, target):
            self.debug_print("  Critical hit with Lethal Hits, automatically wounding")
            return {"wound": True, "critical": False}
        
        # If the weapon has the Mortal special rule and it has hit, then it automatically gets a critical wound
        # Note that this is different from the Devastating Wounds special rule, which is handled later.
        if "Mortal" in weapon.special_rules:
            self.debug_print("  Weapon has Mortal special rule and has hit, automatically getting a critical wound")
            return {"wound": True, "critical": True}

        unmodified_roll = self.roll_dice()
        # Apply modifiers
        roll = unmodified_roll + self.wound_modifiers
        
        # Get critical wound threshold
        critical_threshold = self.get_critical_wound_threshold(weapon, target)
        
        # Determine required roll based on strength vs toughness
        if weapon.strength >= target.toughness * 2:
            required = 2
        elif weapon.strength > target.toughness:
            required = 3
        elif weapon.strength == target.toughness:
            required = 4
        elif weapon.strength * 2 <= target.toughness:
            required = 6
        else:
            required = 5
            
        # Check if we need to reroll
        should_reroll = False
        if self.has_reroll_wounds(weapon, target):
            # Reroll if the roll failed
            should_reroll = roll < required
        elif self.has_reroll_wounds_1(weapon, target) and unmodified_roll == 1:
            # Reroll if we rolled a 1
            should_reroll = True
        elif one_use_rules["has_reroll_1_wound"] and roll < required:
            # Use a 1-use reroll
            should_reroll = True
            one_use_rules["has_reroll_1_wound"] = False
            self.debug_print("  Using Reroll 1 Wound Roll special rule")
        elif one_use_rules["has_reroll_1_hit_or_wound"] and roll < required:
            # Use a 1-use reroll
            should_reroll = True
            one_use_rules["has_reroll_1_hit_or_wound"] = False
            self.debug_print("  Using Reroll 1 Hit or Wound special rule")
        elif one_use_rules["has_reroll_1_hit_wound_or_damage"] and roll < required:
            # Use a 1-use reroll
            should_reroll = True
            one_use_rules["has_reroll_1_hit_wound_or_damage"] = False
            self.debug_print("  Using Reroll 1 Hit or Wound or Damage special rule")

        if should_reroll:
            self.debug_print(f"  Initial wound roll {roll} failed or rolled a 1, attempting reroll")
            unmodified_reroll = self.roll_dice()
            reroll = unmodified_reroll + self.wound_modifiers
            self.debug_print(f"  Reroll result: {reroll}")
            unmodified_roll = unmodified_reroll
            roll = reroll

        # Apply a flipped 6, if any.
        if one_use_rules["has_flip_a_6_wound"] and roll < required:
            unmodified_roll = 6
            one_use_rules["has_flip_a_6_wound"] = False
            self.debug_print("  Using Flip Wound Roll to 6 special rule")
        elif one_use_rules["has_flip_a_6_hit_wound"] and roll < required:
            unmodified_roll = 6
            one_use_rules["has_flip_a_6_hit_wound"] = False
            self.debug_print("  Using Flip Hit or Wound Roll to 6 special rule")
        elif one_use_rules["has_flip_a_6"] and roll < required:
            unmodified_roll = 6
            one_use_rules["has_flip_a_6"] = False
            self.debug_print("  Using Flip Wound Roll to 6 special rule")

        # Check for automatic failure on unmodified roll of 1
        if unmodified_roll == 1:
            self.debug_print("  Unmodified roll of 1 automatically fails wound roll")
            return {"wound": False, "critical": False}
        
        # Critical wound based on threshold
        is_critical = unmodified_roll >= critical_threshold
        if is_critical:
            return {"wound": True, "critical": True}
            
        return {
            "wound": roll >= required,
            "critical": False
        }

    def make_save_roll(self, weapon: Weapon, target: Model, is_devastating_wound: bool = False) -> bool:
        """Make a save roll based on the target's save characteristic"""
        # Devastating Wounds automatically fail the save
        if is_devastating_wound:
            return False
        
        roll = self.roll_dice()

        # A roll of 1 automatically fails the save
        if roll == 1:
            return False

        # Apply modifiers
        roll += self.save_modifiers
        
        # Calculate final save value
        ap_value = weapon.ap
        
        # Apply -1 AP special rule if present
        if "-1 AP" in target.special_rules:
            self.debug_print("  Target has -1 AP rule")
            ap_value = max(0, ap_value - 1)
            self.debug_print(f"  AP value after -1 AP rule: {ap_value}")
        elif "-1 AP in Melee" in target.special_rules and weapon.weapon_type.lower() == "melee":
            self.debug_print("  Target has -1 AP in Melee rule and weapon is melee")
            ap_value = max(0, ap_value - 1)
            self.debug_print(f"  AP value after -1 AP in Melee rule: {ap_value}")
        
        save_value = target.save + ap_value
        
        # Apply Cover special rule if present and weapon is ranged
        if (("Cover" in target.special_rules or "Smoke" in target.special_rules) and 
            weapon.weapon_type.lower() == "ranged" and 
            "Ignores Cover" not in weapon.special_rules):
            self.debug_print("  Target has Cover rule (from Cover or Smoke) and weapon is ranged and doesn't ignore cover")
            # Only prevent save from going below 3 if base save is 3 or higher
            if target.save >= 3:
                save_value = max(3, save_value - 1)
            else:
                save_value = max(2, save_value - 1)
            self.debug_print(f"  Save value after Cover: {save_value}")

        # Debug print all special rules
        self.debug_print(f"  Target special rules: {target.special_rules}")

        # Check for Invulnerable Save Ranged special rule
        for rule in target.special_rules:
            if rule.startswith("Invulnerable Save Ranged "):
                # Extract the value from the rule
                match = re.match(r'Invulnerable Save Ranged (\d+)\+', rule)
                if match and weapon.weapon_type.lower() == "ranged":
                    inv_value = int(match.group(1))
                    self.debug_print(f"  Target has {rule} and weapon is ranged - using {inv_value}+ invulnerable save")
                    if roll >= inv_value:
                        return True
                    return False
            if rule.startswith("Invulnerable Save Melee "):
                # Extract the value from the rule
                match = re.match(r'Invulnerable Save Melee (\d+)\+', rule)
                if match and weapon.weapon_type.lower() == "melee":
                    inv_value = int(match.group(1))
                    self.debug_print(f"  Target has {rule} and weapon is melee - using {inv_value}+ invulnerable save")
                    if roll >= inv_value:
                        return True
                    return False

        # Check invulnerable save if available
        if target.invulnerable_save is not None:
            self.debug_print(f"  Using general invulnerable save: {target.invulnerable_save}+")
            if roll >= target.invulnerable_save:
                return True
                
        return roll >= save_value

    def resolve_attack(self, weapon: Weapon, target: Model, one_use_rules: Dict[str, bool]) -> Dict[str, bool]:
        """Resolve a single attack from a weapon against a target"""
        self.hit_modifiers = 0
        self.wound_modifiers = 0
        self.save_modifiers = 0
        self.debug_print(f"  Starting attack with {weapon.name}")
        self.debug_print(f"  Weapon damage value: {weapon.damage}")
        
        # Calculate hit and wound modifiers including target special rules
        for rule in target.special_rules:
            if "Ignore Modifiers" not in weapon.special_rules and "Ignore Hit Modifiers" not in weapon.special_rules:
                if rule == "-1 to be Hit":
                    self.debug_print("  Target has -1 to be Hit rule")
                    self.hit_modifiers -= 1
                    self.debug_print(f"  Hit modifiers reduced to {self.hit_modifiers}")
                elif rule == "-1 to be Hit in Melee" and weapon.weapon_type.lower() == "melee":
                    self.debug_print("  Target has -1 to be Hit in Melee rule and weapon is melee")
                    self.hit_modifiers -= 1
                    self.debug_print(f"  Hit modifiers reduced to {self.hit_modifiers}")
                elif rule == "Stealth" and weapon.weapon_type.lower() == "ranged":
                    self.debug_print("  Target has Stealth rule")
                    self.hit_modifiers -= 1
                    self.debug_print(f"  Hit modifiers reduced to {self.hit_modifiers}")
                elif rule == "Smoke":
                    self.debug_print("  Target has Smoke rule - applying Stealth")
                    self.hit_modifiers -= 1
                    self.debug_print(f"  Hit modifiers reduced to {self.hit_modifiers}")
            if "Ignore Modifiers" not in weapon.special_rules and "Ignore Wound Modifiers" not in weapon.special_rules:
                if rule == "-1 to be Wounded":
                    self.debug_print("  Target has -1 to be Wounded rule")
                    self.wound_modifiers -= 1
                    self.debug_print(f"  Wound modifiers reduced to {self.wound_modifiers}")
                elif rule == "-1 to be Wounded in Melee" and weapon.weapon_type.lower() == "melee":
                    self.debug_print("  Target has -1 to be Wounded in Melee rule and weapon is melee")
                    self.wound_modifiers -= 1
                    self.debug_print(f"  Wound modifiers reduced to {self.wound_modifiers}")
                elif rule == "-1 to be Wounded by High Strength" and weapon.strength > target.toughness:
                    self.debug_print("  Target has -1 to be Wounded by High Strength rule and weapon strength is greater than target toughness")
                    self.wound_modifiers -= 1
                    self.debug_print(f"  Wound modifiers reduced to {self.wound_modifiers}")
        
        # Max modifer is +/-1.
        self.hit_modifiers = max(-1, min(1, self.hit_modifiers))
        self.wound_modifiers = max(-1, min(1, self.wound_modifiers))
        self.save_modifiers = max(-1, min(1, self.save_modifiers))
        # Check for weapon special rules that modify rolls; maximum modifiers are +/-1.
        for rule in weapon.special_rules:
            if rule == "+1 to Hit":
                self.debug_print("  Weapon has +1 to Hit rule - adding +1 to hit roll")
                self.hit_modifiers += 1
                self.debug_print(f"  Hit modifiers increased to {self.hit_modifiers}")
            elif rule.startswith("+1 to Hit "):
                keyword = rule.replace("+1 to Hit ", "")
                if keyword.lower() in [k.lower() for k in target.keywords]:
                    self.debug_print(f"  Weapon has {rule} and target has {keyword} keyword - adding +1 to hit roll")
                    self.hit_modifiers += 1
                    self.debug_print(f"  Hit modifiers increased to {self.hit_modifiers}")
            if rule == "+1 to Wound":
                self.debug_print("  Weapon has +1 to Wound rule - adding +1 to wound roll")
                self.wound_modifiers += 1
                self.debug_print(f"  Wound modifiers increased to {self.wound_modifiers}")
            elif rule.startswith("+1 to Wound "):
                keyword = rule.replace("+1 to Wound ", "")
                if keyword.lower() in [k.lower() for k in target.keywords]:
                    self.debug_print(f"  Weapon has {rule} and target has {keyword} keyword - adding +1 to wound roll")
                    self.wound_modifiers += 1
                    self.debug_print(f"  Wound modifiers increased to {self.wound_modifiers}")
            if rule == "+1 AP":
                self.debug_print("  Weapon has +1 AP rule - adding +1 to AP")
                weapon.ap += 1
                self.debug_print(f"  AP increased to {weapon.ap}")

        # Step 1: Hit Roll
        hit_result = self.make_hit_roll(weapon, target, one_use_rules)
        self.debug_print(f"  Hit roll result: {hit_result}")
        if not hit_result["hit"]:
            return {"hit": False, "wound": False, "save": False, "damage_dealt": 0}
            
        # Check for Sustained Hits
        sustained_hits = 0
        if hit_result["critical"]:
            sustained_hits = self.get_sustained_hits_value(weapon)
            
        # Step 2: Wound Roll
        is_critical_hit = hit_result["critical"]
        wound_result = self.make_wound_roll(weapon, target, is_critical_hit, one_use_rules)
        self.debug_print(f"  Wound roll result: {wound_result}")
        if not wound_result["wound"]:
            return {"hit": True, "wound": False, "save": False, "damage_dealt": 0}
            
        # Step 3: Save Roll
        # Check for Devastating Wounds
        is_devastating_wound = False
        if wound_result["critical"]:
            # Check for conditional Devastating Wounds
            for rule in weapon.special_rules:
                if rule.startswith("Devastating Wounds "):
                    # Extract the keyword from the rule
                    keyword = rule.replace("Devastating Wounds ", "")
                    if keyword.lower() in [k.lower() for k in target.keywords]:
                        self.debug_print(f"  Critical wound with Devastating Wounds {keyword} - target has {keyword} keyword")
                        is_devastating_wound = True
                        break
                elif rule == "Devastating Wounds":
                    self.debug_print("  Critical wound with Devastating Wounds")
                    is_devastating_wound = True
                    break
                elif rule == "Mortal":
                    self.debug_print("  Critical wound with Mortal")
                    is_devastating_wound = True
                    break
        
        # Devastating Wounds count as mortal wounds; add "Mortal" to special rules here and remove it after the FNP is applied
        dev_to_mortals_dummy = False
        if is_devastating_wound:
            weapon.special_rules.append("Mortal Wounds")
            dev_to_mortals_dummy = True

        # Implement Smoke
        if "Smoke" in target.special_rules:
            self.debug_print("  Target has Smoke rule - applying Cover")
            target.special_rules.append("Cover")

        saved = self.make_save_roll(weapon, target, is_devastating_wound)
        self.debug_print(f"  Save roll result: {saved}")
        if saved:
            return {"hit": True, "wound": True, "save": True, "damage_dealt": 0}
            
        # Step 4: Inflict Damage
        self.debug_print("  About to roll damage")
        damage = self.roll_damage(weapon.damage, weapon, target, is_critical_hit, one_use_rules)
        self.debug_print(f"  Damage roll: {damage}")
        
        # Apply damage reduction rules
        for rule in target.special_rules:
            if rule == "-1 Damage" and ("Ignore Damage Modifiers" not in weapon.special_rules or "Ignore Modifiers" not in weapon.special_rules):
                self.debug_print("  Target has -1 Damage rule")
                damage = max(1, damage - 1)
                self.debug_print(f"  Damage reduced to {damage}")
            elif rule == "Half Damage" and ("Ignore Damage Modifiers" not in weapon.special_rules or "Ignore Modifiers" not in weapon.special_rules):
                self.debug_print("  Target has Half Damage rule")
                damage = m.ceil(damage / 2)
                self.debug_print(f"  Damage halved to {damage}")
        
        # Check for Melta rule; note that this is applied after damage reduction rules
        for rule in weapon.special_rules:
            if rule.startswith("Melta "):
                # Extract the bonus value from the rule
                match = re.match(r'Melta (\d+)', rule)
                if match:
                    melta_bonus = int(match.group(1))
                    # Check if target is within half range
                    if weapon.weapon_type.lower() == "ranged" and weapon.target_range <= weapon.range / 2:
                        self.debug_print(f"  Weapon has Melta {melta_bonus} and target is within half range - adding {melta_bonus} damage")
                        damage += melta_bonus
                        self.debug_print(f"  New damage value: {damage}")

        # Apply Feel No Pain if present
        fnp_value = None
        
        # First check for conditional FNP rules
        for rule in target.special_rules:
            if "Feel No Pain" in rule:
                # Extract the value of the unconditional Feel No Pain
                match = re.match(r'Feel No Pain (\d+)\+', rule)
                if match:
                    fnp_value = int(match.group(1))
                    self.debug_print(f"  Target has {rule}")
                    break
            elif "FNP" in rule:
                # Extract the condition and value from the rule
                # Format is "[condition] FNP X+"
                match = re.match(r'([^FNP]+) FNP (\d+)\+', rule)
                if match:
                    condition = match.group(1).strip()
                    value = int(match.group(2))
                    # Check if the weapon has the condition as a special rule
                    if condition in weapon.special_rules:
                        self.debug_print(f"  Weapon has {condition} and target has {condition} FNP {value}+")
                        fnp_value = value
                        break
                    if condition == "Mortal":
                        if "Mortal Wounds" in weapon.special_rules:
                            self.debug_print(f"  Weapon has Mortal Wounds and target has Mortal FNP {value}+")
                            fnp_value = value
                            break
        
        # If no conditional FNP applies, use the base FNP value
        if fnp_value is None and target.feel_no_pain is not None:
            fnp_value = target.feel_no_pain
        
        # Apply FNP if we have a value
        if fnp_value is not None:
            self.debug_print(f"  Target has Feel No Pain {fnp_value}+")
            fnp_saves = 0
            for _ in range(damage):
                fnp_roll = self.roll_dice()
                #self.debug_print(f"  Feel No Pain roll: {fnp_roll}")
                if fnp_roll >= fnp_value:
                    fnp_saves += 1
            damage -= fnp_saves
            self.debug_print(f"  Feel No Pain saved {fnp_saves} damage, reduced to {damage}")
        
        # Handle Overkill special rule
        if "Overkill" in weapon.special_rules:
            self.debug_print(f"  Weapon has Overkill rule - splitting {damage} damage into {damage} instances of 1 damage")
            # Each instance of damage is split into pieces of 1 damage so that overkill continues to kill models.
            overkill_instances = damage
            damage = 1
            for _ in range(overkill_instances):
                damage_dealt_temp = min(damage, target.current_wounds)
                target.current_wounds -= damage_dealt_temp
                self.debug_print(f"  Damage dealt: {damage_dealt_temp}")
                self.debug_print(f"  Target remaining wounds: {target.current_wounds}")
                # Reset wounds if model is destroyed
                if target.current_wounds <= 0:
                    target.current_wounds = target.wounds
            damage_dealt = overkill_instances
        else:
            damage_dealt = min(damage, target.current_wounds)
            target.current_wounds -= damage_dealt
            self.debug_print(f"  Damage dealt: {damage_dealt}")
            self.debug_print(f"  Target remaining wounds: {target.current_wounds}")
        
        # Reset wounds if model is destroyed
        if target.current_wounds <= 0:
            target.current_wounds = target.wounds
        
        # Remove "Mortal" from special rules if it was added from a devastating wound
        if dev_to_mortals_dummy:
            weapon.special_rules.remove("Mortal Wounds")

        return {
            "hit": True,
            "wound": True,
            "save": False,
            "damage_dealt": damage_dealt,
            "sustained_hits": sustained_hits
        }

    def resolve_attacks(self, weapon: Weapon, target: Model, one_use_rules: Dict[str, bool]) -> Dict[str, int]:
        """Resolve all attacks from a weapon against a target"""
        results = {
            "hits": 0,
            "wounds": 0,
            "failed_saves": 0,
            "damage_dealt": 0,
            "critical_hits": 0,
            "critical_wounds": 0,
            "sustained_hits": 0,
            "models_destroyed": 0
        }
                
        # Check if weapon is in range
        if weapon.weapon_type.lower() == "ranged" and weapon.range < weapon.target_range:
            self.debug_print(f"Weapon {weapon.name} is out of range ({weapon.range} < {weapon.target_range})")
            return results

        # Calculate number of attacks
        num_attacks = self.roll_attacks(weapon.attacks, weapon, target)
        self.debug_print(f"Resolving {num_attacks} attacks")

        # Apply Rapid Fire bonus
        for rule in weapon.special_rules:
            if rule.startswith("Rapid Fire ") and weapon.weapon_type.lower() == "ranged" and weapon.target_range <= weapon.range/2:
                # Extract the bonus value from the rule
                match = re.match(r'Rapid Fire (.+)', rule)
                if match and match.group(1).isdigit():
                    bonus = int(match.group(1))
                    self.debug_print(f"  Weapon has Rapid Fire {bonus} and target is within range - adding {bonus} attacks")
                    num_attacks += bonus
                else:
                    bonus = self.find_rapid_fire_bonus(match.group(1))
                    self.debug_print(f"  Weapon has Rapid Fire {bonus} and target is within range - adding {bonus} attacks")
                    num_attacks += bonus
        
        for _ in range(num_attacks):
            attack_result = self.resolve_attack(weapon, target, one_use_rules)
            if attack_result["hit"]:
                results["hits"] += 1
            if attack_result["wound"]:
                results["wounds"] += 1
            if not attack_result["save"]:
                results["failed_saves"] += 1
                results["damage_dealt"] += attack_result["damage_dealt"]
            
            # Handle sustained hits
            if "sustained_hits" in attack_result and attack_result["sustained_hits"] > 0:
                results["sustained_hits"] += attack_result["sustained_hits"]
                # Resolve each sustained hit
                for _ in range(attack_result["sustained_hits"]):
                    sustained_attack = self.resolve_attack(weapon, target, one_use_rules)
                    if sustained_attack["hit"]:
                        results["hits"] += 1
                    if sustained_attack["wound"]:
                        results["wounds"] += 1
                    if not sustained_attack["save"]:
                        results["failed_saves"] += 1
                        results["damage_dealt"] += sustained_attack["damage_dealt"]
        
        # Calculate models destroyed
        results["models_destroyed"] = results["damage_dealt"] // target.wounds
        
        return results 