import tkinter as tk
from tkinter import ttk
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from typing import Dict, List, Tuple
import seaborn as sns

class ResultVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Warhammer Simulation Results Visualizer")
        
        # Load simulation data
        with open("data/results/simulation_data.json", 'r') as f:
            self.simulation_data = json.load(f)
            
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create control panel
        self.create_control_panel()
        
        # Create visualization area
        self.create_visualization_area()
        
        # Initial plot
        self.update_visualization()
        
    def create_control_panel(self):
        """Create the control panel with selection options"""
        control_frame = ttk.LabelFrame(self.main_frame, text="Controls", padding="5")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Faction selection
        ttk.Label(control_frame, text="Faction:").grid(row=0, column=0, sticky=tk.W)
        self.faction_var = tk.StringVar(value="All Factions")
        self.faction_combo = ttk.Combobox(control_frame, textvariable=self.faction_var, width=30)
        self.faction_combo['values'] = ["All Factions"] + sorted(list(set(
            unit.split(" - ")[0] for unit in self.simulation_data.keys()
        )))
        self.faction_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Combat type selection
        ttk.Label(control_frame, text="Combat Type:").grid(row=1, column=0, sticky=tk.W)
        self.combat_type_var = tk.StringVar(value="Both")
        combat_type_frame = ttk.Frame(control_frame)
        combat_type_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        ttk.Radiobutton(combat_type_frame, text="Ranged", variable=self.combat_type_var, 
                       value="Ranged").pack(side=tk.LEFT)
        ttk.Radiobutton(combat_type_frame, text="Melee", variable=self.combat_type_var, 
                       value="Melee").pack(side=tk.LEFT)
        ttk.Radiobutton(combat_type_frame, text="Both", variable=self.combat_type_var, 
                       value="Both").pack(side=tk.LEFT)
        
        # Metric selection
        ttk.Label(control_frame, text="Metric:").grid(row=2, column=0, sticky=tk.W)
        self.metric_var = tk.StringVar(value="Points Killed per Point")
        metric_combo = ttk.Combobox(control_frame, textvariable=self.metric_var, width=30)
        metric_combo['values'] = ["Damage", "Models Killed", "Points Killed per Point"]
        metric_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Update button
        update_button = ttk.Button(control_frame, text="Update Visualization", 
                                 command=self.update_visualization)
        update_button.grid(row=3, column=0, columnspan=2, pady=10)
        
    def create_visualization_area(self):
        """Create the area for the visualization"""
        self.viz_frame = ttk.Frame(self.main_frame)
        self.viz_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create figure and canvas
        self.fig = plt.Figure(figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def get_filtered_data(self) -> Tuple[List[str], List[str], np.ndarray, np.ndarray]:
        """Get filtered data based on current selections"""
        # Get selected faction
        selected_faction = self.faction_var.get()
        
        # Filter units based on faction and combat type
        filtered_units = []
        for unit in self.simulation_data.keys():
            faction = unit.split(" - ")[0] # TODO: This is not correct, we need to get the faction above the unit name
            if selected_faction != "All Factions" and faction != selected_faction:
                continue
                
            combat_type = "Ranged" if "Ranged" in unit else "Melee"
            if self.combat_type_var.get() != "Both" and combat_type != self.combat_type_var.get():
                continue
                
            filtered_units.append(unit)
            
        if not filtered_units:
            return [], [], np.array([]), np.array([])
            
        # Get all target units
        target_units = set()
        for unit in filtered_units:
            for target in self.simulation_data[unit].keys():
                target_units.add(target)
        target_units = sorted(list(target_units))
        
        # Create matrices for means and standard deviations
        means = np.zeros((len(filtered_units), len(target_units)))
        stds = np.zeros((len(filtered_units), len(target_units)))
        
        # Fill matrices
        for i, unit in enumerate(filtered_units):
            for j, target in enumerate(target_units):
                if target in self.simulation_data[unit]:
                    data = self.simulation_data[unit][target]
                    if self.metric_var.get() == "Damage":
                        means[i, j] = data["mean_damage"]
                        stds[i, j] = data["std_damage"]
                    elif self.metric_var.get() == "Models Killed":
                        means[i, j] = data["mean_models_killed"]
                        stds[i, j] = data["std_models_killed"]
                    else:  # Points Killed per Point
                        means[i, j] = data["pnts_killed_per_point"]
                        stds[i, j] = data["std_dev_pnts_killed_per_point"]
                        
        return filtered_units, target_units, means, stds
        
    def update_visualization(self):
        """Update the visualization based on current selections"""
        # Clear the figure
        self.fig.clear()
        
        # Get filtered data
        filtered_units, target_units, means, stds = self.get_filtered_data()
        
        if len(filtered_units) == 0 or len(target_units) == 0:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "No data available for selected filters",
                   ha='center', va='center')
            self.canvas.draw()
            return
            
        # Create subplot
        ax = self.fig.add_subplot(111)
        
        # Create heatmap
        sns.heatmap(means, annot=True, fmt='.2f', cmap='YlOrRd', ax=ax,
                   xticklabels=target_units, yticklabels=filtered_units)
        
        # Add error bars
        for i in range(len(filtered_units)):
            for j in range(len(target_units)):
                if means[i, j] != 0:  # Only add error bars for non-zero values
                    # Calculate error bar height relative to column max
                    col_max = np.max(means[:, j])
                    error_height = stds[i, j] / col_max
                    ax.plot([j + 0.5, j + 0.5], 
                           [i + 0.5 - error_height/2, i + 0.5 + error_height/2],
                           'k-', linewidth=2)
        
        # Rotate x-axis labels
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Set title
        ax.set_title(f"{self.metric_var.get()} by Unit\n{self.faction_var.get()} - {self.combat_type_var.get()}")
        
        # Adjust layout
        self.fig.tight_layout()
        
        # Update canvas
        self.canvas.draw()

def main():
    root = tk.Tk()
    app = ResultVisualizer(root)
    root.mainloop()

if __name__ == "__main__":
    main() 