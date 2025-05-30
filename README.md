# 40k-FightSim
A simulator for Warhammer 40k attacks.

How to simulate an attack from one unit (with options) on another:

Clone the repository and run src/combat_gui.py. It should be self-explanatory. If it is not, please contact
Andrew White and let him know what part was confusing or non-intuitive.


FAQ:


1. Can I trust that all of the unit data is accurate?

Maybe? That's why the unit data is displayed when you select units. In principle, any faction file with a date in
its name has been checked, by hand, to work, but mistakes are possible. Faction files without dates in their
names have been pulled from the battlescribe project; the stats should be accurate, but errors are possible;
in addition, these files without dates include weapon and unit keywords but not weapon and unit special rules.

If you find errors, feel free to correct them; if you are not comfortable editing .json files and/or using Git,
simply contact Andrew White and he will get to it eventually.

2. Can I use this without installing Python?

No. A version that is independent of python is far down the line.

3. I cannot add the special rule that I need to simulate the combat I'm interested in. Where is it?

If you cannot find a special rule, it is currently not coded in. Please contact Andrew White and he will get 
to it eventually. If you feel up to it, you can also try to code it yourself while maintaining the style of
the existing code.

4. If I'm only supposed to run combat_gui.py, what are the other .py files?

Files with a "\_safe" suffix are there in case I accidentally break something beyond repair. Other files are either
called by combat_gui.py as it runs, or they are programs that have extra features that are currently under
development.

5. Can I simulate psychic abilities?

Sometimes. If you can simulate a psychic ability, it will appear as a weapon for the unit with the ability.


