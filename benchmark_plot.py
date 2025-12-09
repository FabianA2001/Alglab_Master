import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import json
from src.solution import Solution

def gather_sol_times(data_dir):
    sol_times = []
    all_files = list(data_dir.glob("*.json"))
    dict_constraint = {
        0:"original"
        ,1:"new"
        ,2:"Alternative"
        ,3:"Alternative_enforce"
        ,4:"Alternative_exact"
        ,5:"Alternative_exact_Enforce"
        ,7:"Alternative_exact_original"
        }
    # Gathering files for optimal solutions
    for key in dict_constraint.values():  # Modify keys as per your dictionary
        for try_num in range(0, 5):  # Assuming tries are 1 and 2
            # Search for optimal solution files
            file_pattern = data_dir.glob(f"*_{key}_opt_{try_num}.json")
            
            
            for file in file_pattern:
                solution = Solution.from_json_file(file.stem)  # Load using the base filename
                instance_name = file.stem.split('_')[0]  # Get instance name from filename
                sol_times.append({
                    'instance': instance_name,
                    'key': key,
                    'type': 'optimal',
                    'value': 'time',
                    'solve_time': solution.solve_time,
                    'objective_value': solution.objective_value
                })
    
    # Repeat for immediate first solutions
    for key in dict_constraint.values():
        for try_num in range(0, 5):
            file_pattern = data_dir.glob(f"*_{key}_immediate_first_{try_num}.json")
            
            
            for file in file_pattern:
                solution = Solution.from_json_file(file.stem)  # Load using the base filename
                instance_name = file.stem.split('_')[0]
                sol_times.append({
                    'instance': instance_name,
                    'key': key,
                    'type': 'immediate_first',
                    'value': 'time',
                    'solve_time': solution.solve_time,
                    'objective_value': solution.objective_value
                })
    
    # Repeat for first good solutions
    for key in dict_constraint.values():
        for try_num in range(0, 5):
            file_pattern = data_dir.glob(f"*_{key}_first_good_{try_num}.json")
            
            
            for file in file_pattern:
                solution = Solution.from_json_file(file.stem)  # Load using the base filename
                instance_name = file.stem.split('_')[0]
                sol_times.append({
                    'instance': instance_name,
                    'key': key,
                    'type': 'first_good',
                    'value': 'time',
                    'solve_time': solution.solve_time,
                    'objective_value': solution.objective_value
                })

    for key in dict_constraint.values():
        for try_num in range(0, 5):
            file_pattern = data_dir.glob(f"*_{key}_first_good_{try_num}.json")
            
            
            for file in file_pattern:
                solution = Solution.from_json_file(file.stem)  # Load using the base filename
                if solution.solve_time >= 1800:
                    instance_name = file.stem.split('_')[0]
                    sol_times.append({
                        'instance': instance_name,
                        'key': key,
                        'type': 'timed_out',
                        'value': 'objective_function',
                        'solve_time': solution.objective_value,
                        'objective_value': solution.objective_value
                    })

    return pd.DataFrame(sol_times)


def plot_sol_times_lines(df, solution_type):
    measures = ['min', 'max', 'mean']
    
    for measure in measures:
        # Create a new figure for each measure
        plt.figure(figsize=(15, 8))
        
        # Compute aggregation based on the current measure
        if measure == 'min':
            plot_data = df.groupby(['instance', 'key'])['solve_time'].min().reset_index(name='value')
        elif measure == 'max':
            plot_data = df.groupby(['instance', 'key'])['solve_time'].max().reset_index(name='value')
        elif measure == 'mean':
            plot_data = df.groupby(['instance', 'key'])['solve_time'].mean().reset_index(name='value')
        
        for key in plot_data['key'].unique():
            subset = plot_data[plot_data['key'] == key]
            x = subset['instance']
            y = subset['value']

            # Plotting with different colors for different keys
            plt.plot(x, y, marker='o', linestyle='', label=f'{measure.capitalize()} {key}')

        plt.title(f'Solve {measure.capitalize()} for {solution_type.capitalize()} Solutions')
        plt.xlabel('Instance Name')
        plt.ylabel('Solve Time (seconds)')
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        
        # Show each plot
        plt.show()

def plot_sol_times_barchart(df, solution_type):
    measures = ['min', 'max', 'mean']
    bar_width = 0.05  # Width of each bar
    indices = np.arange(len(df['instance'].unique()))  # Bar positions

    for measure in measures:
        # Create a new figure for each measure
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Compute aggregation based on the current measure
        if measure == 'min':
            plot_data = df.groupby(['instance', 'key'])['solve_time'].min().reset_index(name='value')
        elif measure == 'max':
            plot_data = df.groupby(['instance', 'key'])['solve_time'].max().reset_index(name='value')
        elif measure == 'mean':
            plot_data = df.groupby(['instance', 'key'])['solve_time'].mean().reset_index(name='value')

        # Get unique instances and keys
        instances = plot_data['instance'].unique()
        keys = plot_data['key'].unique()

        # Iterate through keys to create grouped bars
        for i, key in enumerate(keys):
            subset = plot_data[plot_data['key'] == key]
            y = subset['value'].values
            
            # Offset for each bar based on its order
            bar_positions = indices + (i * bar_width)
            rects = ax.bar(bar_positions, y, bar_width, label=key, alpha=0.7)

            # Adding bar labels
            ax.bar_label(rects, padding=3)

        # Adding details
        ax.set_ylabel('Solve Time (seconds)')
        ax.set_title(f'Solve Time {measure.capitalize()} for {solution_type.capitalize()} Solutions')
        ax.legend(title="Keys", loc='upper left', ncols=len(keys))

        plt.tight_layout()
        plt.show()
        filename = f'solve_time_{solution_type}_{measure}.png'  # Change extension for different formats
        plt.savefig(filename) 


def main():
    DATA_DIR = Path(__file__).resolve().parent / "data" / "solutions"
    df_sol_times = gather_sol_times(DATA_DIR)
    
    # Filter the data for different solution types
    for solution_type in ['optimal', 'immediate_first', 'first_good', 'timed_out']:
        if len(df_sol_times) > 0:
            filtered_df = df_sol_times[df_sol_times['type'] == solution_type]
            if len(filtered_df) > 0:
                plot_sol_times_lines(filtered_df, df_sol_times.iloc[0]['value'])

if __name__ == "__main__":
    main()