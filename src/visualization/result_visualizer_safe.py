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
        
    def create_control_panel(self):
        """Create the control panel with selection options"""
        control_frame = ttk.LabelFrame(self.main_frame, text="Controls", padding="5")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Configure control frame to not expand
        self.main_frame.grid_columnconfigure(0, weight=0)
        
        # Faction selection
        ttk.Label(control_frame, text="Faction:").grid(row=0, column=0, sticky=tk.W)
        self.faction_var = tk.StringVar(value="All Factions")
        self.faction_combo = ttk.Combobox(control_frame, textvariable=self.faction_var, width=30)
        self.faction_combo['values'] = ["All Factions"] + sorted(list(self.simulation_data.keys()))
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
        
        # Sorting controls
        ttk.Label(control_frame, text="Sort By:").grid(row=3, column=0, sticky=tk.W)
        self.sort_column_var = tk.StringVar(value="Unit Name")
        self.sort_column_combo = ttk.Combobox(control_frame, textvariable=self.sort_column_var, width=30)
        self.sort_column_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Label(control_frame, text="Sort Direction:").grid(row=4, column=0, sticky=tk.W)
        self.sort_direction_var = tk.StringVar(value="Low to High")
        sort_direction_frame = ttk.Frame(control_frame)
        sort_direction_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        ttk.Radiobutton(sort_direction_frame, text="High to Low", variable=self.sort_direction_var, 
                       value="High to Low").pack(side=tk.LEFT)
        ttk.Radiobutton(sort_direction_frame, text="Low to High", variable=self.sort_direction_var, 
                       value="Low to High").pack(side=tk.LEFT)
        
        # Update button
        update_button = ttk.Button(control_frame, text="Update Visualization", 
                                 command=self.update_visualization)
        update_button.grid(row=5, column=0, columnspan=2, pady=10)
        
    def create_visualization_area(self):
        """Create the area for the visualization"""
        self.viz_frame = ttk.Frame(self.main_frame)
        self.viz_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights to allow expansion
        self.main_frame.grid_columnconfigure(1, weight=1)  # Make visualization column expand
        self.main_frame.grid_rowconfigure(0, weight=1)     # Make rows expand
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Create a frame to hold the canvas and scrollbar
        self.canvas_frame = ttk.Frame(self.viz_frame)
        self.canvas_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure the canvas frame to expand
        self.viz_frame.grid_columnconfigure(0, weight=1)
        self.viz_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        
        # Create inner frame for the canvas
        self.inner_frame = ttk.Frame(self.canvas_frame)
        self.inner_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create and configure the scrollbar
        self.scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical")
        self.scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Create figure with initial size
        self.fig = plt.Figure(figsize=(15, 3))  # Initial size
        
    def get_filtered_data(self) -> Tuple[List[str], List[str], np.ndarray, np.ndarray]:
        """Get filtered data based on current selections"""
        # Get selected faction
        selected_faction = self.faction_var.get()
        
        # Define small and large units
        small_units = [
            "Hormagaunts", "Boyz", "Necron Warriors", "Battle Sisters Squad",
            "Nobz", "Intercessor Squad", "Einhyr Hearthguard", "Aggressor Squad",
            "Terminator Squad", "Custodian Guard"
        ]
        
        large_units = [
            "Trukk", "Falcon", "Hive Tyrant", "Armiger Warglaive",
            "Vindicator", "Transcendant C'tan", "Knight Paladin"
        ]
        
        # Filter units based on faction and combat type
        filtered_units = []
        for faction, units in self.simulation_data.items():
            if selected_faction != "All Factions" and faction != selected_faction:
                continue
                
            for unit, targets in units.items():
                # Get combat type from first target (all targets for a unit have same phase)
                combat_type = next(iter(targets.values()))["phase"]
                if self.combat_type_var.get() != "Both" and combat_type != self.combat_type_var.get():
                    continue
                    
                filtered_units.append(f"{faction} - {unit}")
            
        if not filtered_units:
            return [], [], np.array([]), np.array([])
            
        # Get all target units in their original order
        target_units = []
        seen_targets = set()
        # Use the first unit's targets to establish the order
        first_unit = next(iter(self.simulation_data.values()))
        first_targets = next(iter(first_unit.values()))
        for target in first_targets.keys():
            if target not in seen_targets:
                target_units.append(target)
                seen_targets.add(target)
        
        # Create matrices for means and standard deviations
        means = np.zeros((len(filtered_units), len(target_units) + 3))  # +3 for the new columns
        stds = np.zeros((len(filtered_units), len(target_units) + 3))   # +3 for the new columns
        
        # Fill matrices
        for i, full_unit_name in enumerate(filtered_units):
            faction, unit = full_unit_name.split(" - ", 1)
            
            # Calculate averages against small and large units
            small_unit_values = []
            large_unit_values = []
            all_values = []  # For overall average
            
            for target in small_units:
                if target in self.simulation_data[faction][unit]:
                    data = self.simulation_data[faction][unit][target]
                    if self.metric_var.get() == "Damage":
                        small_unit_values.append(data["mean_damage"])
                    elif self.metric_var.get() == "Models Killed":
                        small_unit_values.append(data["mean_models_killed"])
                    else:  # Points Killed per Point
                        small_unit_values.append(data["pnts_killed_per_point"])
                        
            for target in large_units:
                if target in self.simulation_data[faction][unit]:
                    data = self.simulation_data[faction][unit][target]
                    if self.metric_var.get() == "Damage":
                        large_unit_values.append(data["mean_damage"])
                    elif self.metric_var.get() == "Models Killed":
                        large_unit_values.append(data["mean_models_killed"])
                    else:  # Points Killed per Point
                        large_unit_values.append(data["pnts_killed_per_point"])
            
            # Fill the main data
            for j, target in enumerate(target_units):
                if target in self.simulation_data[faction][unit]:
                    data = self.simulation_data[faction][unit][target]
                    if self.metric_var.get() == "Damage":
                        means[i, j] = data["mean_damage"]
                        stds[i, j] = data["std_damage"]
                        all_values.append(data["mean_damage"])
                    elif self.metric_var.get() == "Models Killed":
                        means[i, j] = data["mean_models_killed"]
                        stds[i, j] = data["std_models_killed"]
                        all_values.append(data["mean_models_killed"])
                    else:  # Points Killed per Point
                        means[i, j] = data["pnts_killed_per_point"]
                        stds[i, j] = data["std_dev_pnts_killed_per_point"]
                        all_values.append(data["pnts_killed_per_point"])
            
            # Add averages to last three columns
            means[i, -3] = np.mean(small_unit_values) if small_unit_values else 0
            means[i, -2] = np.mean(large_unit_values) if large_unit_values else 0
            means[i, -1] = np.mean(all_values) if all_values else 0
                        
        # Add average columns to the end of target_units
        target_units = target_units + ["Avg. vs. Small", "Avg. vs. Large", "Overall Avg"]
        
        # Update sort column options
        self.sort_column_combo['values'] = ["Unit Name"] + target_units
        
        # Sort the data based on selected column and direction
        sort_column = self.sort_column_var.get()
        if sort_column == "Unit Name":
            # Sort by unit name (after the faction)
            sort_order = 1 if self.sort_direction_var.get() == "Low to High" else -1
            # Create a list of (index, unit_name) pairs for sorting
            indexed_units = list(enumerate(filtered_units))
            # Sort based on the unit part of the name (after the faction)
            # indexed_units.sort(key=lambda x: x[1].split(" - ")[1].lower(), reverse=(sort_order == -1))
            indexed_units.sort(key=lambda x: x[1].lower(), reverse=(sort_order == -1))
            # Extract the sorted indices
            sort_indices = [i for i, _ in indexed_units]
        elif sort_column in target_units:
            # Sort by column value
            sort_idx = target_units.index(sort_column)
            sort_order = -1 if self.sort_direction_var.get() == "High to Low" else 1
            sort_indices = np.argsort(means[:, sort_idx] * sort_order)
        else:
            sort_indices = np.arange(len(filtered_units))
            
        means = means[sort_indices]
        stds = stds[sort_indices]
        filtered_units = [filtered_units[i] for i in sort_indices]
                        
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
            
        # Compute fixed height
        num_rows = len(filtered_units)
        row_height = 0.5  # inches
        height_inches = num_rows * row_height
        self.fig.set_size_inches(15, height_inches)  # Keep width fixed
            
        # Create heatmap
        ax = self.fig.add_subplot(111)
        sns.heatmap(means, annot=True, fmt='.2f', cmap='RdYlGn', ax=ax,
                   xticklabels=target_units, yticklabels=filtered_units,
                   square=False,  # Allow non-square cells
                   cbar_kws={'label': self.metric_var.get()})  # Add colorbar label
        
        # Add horizontal error bars
        for i in range(len(filtered_units)):
            for j in range(len(target_units)):
                if means[i, j] != 0:  # Only add error bars for non-zero values
                    # Calculate error bar width relative to row max
                    row_max = np.max(means[i, :])
                    error_width = stds[i, j] / row_max
                    ax.plot([j + 0.5 - error_width/2, j + 0.5 + error_width/2], 
                           [i + 0.7, i + 0.7],  # Move error bar below the number
                           'k-', linewidth=2)
        
        # Move x-axis labels to top
        ax.xaxis.set_label_position('top')
        ax.xaxis.tick_top()
        
        # Rotate x-axis labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha='left')
        
        # Set title
        ax.set_title(f"{self.metric_var.get()} by Unit\n{self.faction_var.get()} - {self.combat_type_var.get()}")
        
        # Adjust layout with more space for labels
        self.fig.tight_layout(pad=2.0)
        
        # Now embed figure into the scrollable canvas
        # Clear old canvas if necessary
        for child in self.inner_frame.winfo_children():
            child.destroy()
            
        # Create new canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.inner_frame)
        canvas_widget = self.canvas.get_tk_widget()
        
        # Compute canvas pixel size
        dpi = self.fig.get_dpi()
        canvas_widget.config(
            width=int(self.fig.get_figwidth() * dpi),
            height=int(self.fig.get_figheight() * dpi)
        )
        
        # Configure scrollbar
        self.scrollbar.config(command=canvas_widget.yview)
        canvas_widget.config(yscrollcommand=self.scrollbar.set)
        
        # Pack the canvas
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        
        # Draw the canvas
        self.canvas.draw()
        
        # Update the scroll region
        canvas_widget.configure(scrollregion=canvas_widget.bbox("all"))

def main():
    root = tk.Tk()
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    app = ResultVisualizer(root)
    root.mainloop()

if __name__ == "__main__":
    main() 