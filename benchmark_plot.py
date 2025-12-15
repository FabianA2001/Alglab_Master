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
                    'value': 'solve_time',
                    'solve_time': solution.solve_time,
                    'objective_value': solution.objective_value
                })
            file_pattern = data_dir.glob(f"*_{key}_first_good_{try_num}.json")
            for file in file_pattern:
                solution = Solution.from_json_file(file.stem)  # Load using the base filename
                instance_name = file.stem.split('_')[0]
                sol_times.append({
                    'instance': instance_name,
                    'key': key,
                    'type': 'optimal',
                    'value': 'solve_time',
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
                    'value': 'solve_time',
                    'solve_time': solution.solve_time,
                    'objective_value': solution.objective_value
                })

            file_pattern = data_dir.glob(f"*_{key}_immediate_{try_num}.json")
            
            
            for file in file_pattern:
                solution = Solution.from_json_file(file.stem)  # Load using the base filename
                instance_name = file.stem.split('_')[0]
                sol_times.append({
                    'instance': instance_name,
                    'key': key,
                    'type': 'immediate_first',
                    'value': 'solve_time',
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
                    'value': 'solve_time',
                    'solve_time': solution.solve_time,
                    'objective_value': solution.objective_value
                })

    for key in dict_constraint.values():
        for try_num in range(0, 5):
            file_pattern = data_dir.glob(f"*_{key}_time_out_30_{try_num}.json")
            
            
            for file in file_pattern:
                solution = Solution.from_json_file(file.stem)  # Load using the base filename
                if solution.solve_time >= 1800 or True:
                    instance_name = file.stem.split('_')[0]
                    sol_times.append({
                        'instance': instance_name,
                        'key': key,
                        'type': 'timed_out',
                        'value': 'objective_value',
                        'solve_time': solution.objective_value,
                        'objective_value': solution.objective_value
                    })

    return pd.DataFrame(sol_times)


def plot_sol_times_lines(df, solution_type, value_type):
    measures = ['min', 'max', 'mean', 'median', 'count']
    
    for measure in measures:
        # Create a new figure for each measure
        plt.figure(figsize=(15, 8))
        
        # Compute aggregation based on the current measure
        if measure == 'min':
            plot_data = df.groupby(['instance', 'key'])[value_type].min().reset_index(name='value')
        elif measure == 'max':
            plot_data = df.groupby(['instance', 'key'])[value_type].max().reset_index(name='value')
        elif measure == 'mean':
            plot_data = df.groupby(['instance', 'key'])[value_type].mean().reset_index(name='value')
        elif measure == 'median':
            plot_data = df.groupby(['instance', 'key'])[value_type].median().reset_index(name='value')
        elif measure == 'count':
            plot_data = df.groupby(['instance', 'key'])[value_type].count().reset_index(name='value')
        
        for key in plot_data['key'].unique():
            subset = plot_data[plot_data['key'] == key]
            x = subset['instance']
            y = subset['value']

            # Plotting with different colors for different keys
            plt.plot(x, y, marker='o', linestyle='', markersize=10, label=f'{measure.capitalize()} {key}')

        plt.title(f'Solve {measure.capitalize()} for {solution_type.capitalize()} {value_type.capitalize()} Solutions')
        plt.xlabel('Instance Name')
        plt.ylabel('Solve Time (seconds)')
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        
        # Show each plot
        #plt.show()
        filename = f'solve_{solution_type}_{value_type}_{measure}_points.png'  # Change extension for different formats
        plt.savefig(filename)

def plot_sol_times_barchart(df, solution_type, value_type):
    measures = ['min', 'max', 'mean', 'median', 'count']
    bar_width = 0.05  # Width of each bar
    indices = np.arange(len(df['instance'].unique()))  # Bar positions

    for measure in measures:
        fig, ax = plt.subplots(figsize=(15, 8))

        # Compute aggregation
        if measure == 'min':
            plot_data = df.groupby(['instance', 'key'])[value_type].min().reset_index(name='value')
        elif measure == 'max':
            plot_data = df.groupby(['instance', 'key'])[value_type].max().reset_index(name='value')
        elif measure == 'mean':
            plot_data = df.groupby(['instance', 'key'])[value_type].mean().reset_index(name='value')
        elif measure == 'median':
            plot_data = df.groupby(['instance', 'key'])[value_type].median().reset_index(name='value')
        elif measure == 'count':
            plot_data = df.groupby(['instance', 'key'])[value_type].count().reset_index(name='value')

        # Get unique instances and keys
        instances = plot_data['instance'].unique()
        keys = plot_data['key'].unique()

        # Set bar width and indices
        bar_width = 0.15
        indices = np.arange(len(instances))

        # Iterate through keys to create grouped bars
        for i, key in enumerate(keys):
            subset = plot_data[plot_data['key'] == key]
            y = subset['value'].values
            
            # Offset for each bar based on its order
            bar_positions = indices + (i * bar_width)

            # Ensure y and bar_positions have the same length
            if len(y) != len(bar_positions):
                continue  # Skip this iteration if lengths do not match
            
            rects = ax.bar(bar_positions, y, bar_width, label=key, alpha=0.7)

            # Bar labels
            ax.bar_label(rects, padding=3)

        # Adding details
        ax.set_ylabel('Solve Time (seconds)')
        ax.set_title(f'Solve {measure.capitalize()} for {solution_type.capitalize()} {value_type.capitalize()} Solutions')

        # Set x-axis ticks and labels
        ax.set_xticks(indices + bar_width * (len(keys) - 1) / 2)  # Center bars
        ax.set_xticklabels(instances, rotation=45)  # Rotate labels for better visibility

        ax.legend(title="Keys", loc='upper left')
        plt.tight_layout()

        # Save the figure
        filename = f'solve_{solution_type}_{value_type}_{measure}_bar.png'
        plt.savefig(filename)

def aggregate_scores(df, value_type, solution_type):
    # Creating a dictionary to store scores
    method_scores = {}

    # Get unique instances
    instances = df['instance'].unique()

    for instance in instances:
        # Filter the data for the current instance
        subset = df[df['instance'] == instance]
        
        # Calculate min, max, mean, median
        min_values = subset.groupby('key')[value_type].min()
        max_values = subset.groupby('key')[value_type].max()
        mean_values = subset.groupby('key')[value_type].mean()
        median_values = subset.groupby('key')[value_type].median()
        # Combine metrics into a single DataFrame
        metrics_df = pd.DataFrame({
            'min': min_values,
            'max': max_values,
            'mean': mean_values,
            'median': median_values
        }).reset_index()

        # Sort by each metric and assign scores
        for metric in ['min', 'max', 'mean', 'median']:
            sorted_metric = metrics_df.sort_values(by=metric)
            sorted_metric['score'] = sorted_metric[metric].rank(method='dense').astype(int)
            # Accumulate scores for each method
            for row in sorted_metric.itertuples():
                method = row.key
                score = row.score
                if method not in method_scores:
                    method_scores[method] = 0
                method_scores[method] += score  # Summing scores across instances
    
    return method_scores

def get_top_methods(method_scores, n=3):
    # Sort methods by their total scores
    sorted_methods = sorted(method_scores.items(), key=lambda x: x[1])
    
    # Get the top n methods
    top_methods = sorted_methods[:n]
    
    return top_methods


def aggregate_scores_(df, value_type, solution_type):
    # Create a dictionary to store scores
    method_scores = {}

    # Get unique instances
    instances = df['instance'].unique()

    for instance in instances:
        # Filter the data for the current instance
        subset = df[df['instance'] == instance]
        
        # Calculate metrics for each method
        min_values = subset.groupby('key')[value_type].min()
        max_values = subset.groupby('key')[value_type].max()
        mean_values = subset.groupby('key')[value_type].mean()
        median_values = subset.groupby('key')[value_type].median()
        # Combine metrics into a single DataFrame
        metrics_df = pd.DataFrame({
            'key': min_values.index,
            'min': min_values.values,
            'max': max_values.values,
            'mean': mean_values.values,
            'median': median_values.values
        })

        # Sort and assign scores for each metric
        for metric in ['min', 'max', 'mean', 'median']:
            sorted_metric = metrics_df.sort_values(by=metric)
            sorted_metric['score'] = sorted_metric[metric].rank(method='dense').astype(int)
            # Accumulate scores for each method
            for row in sorted_metric.itertuples():
                method = row.key
                score = row.score
                if method not in method_scores:
                    method_scores[method] = {metric: 0 for metric in ['min', 'max', 'mean', 'median']}
                method_scores[method][metric] += score  # Summing scores across instances
    return method_scores

def print_top_methods(method_scores, n=3):
    overall_scores = {}
    
    for metric in ['min', 'max', 'mean', 'median']:
        # Sort methods by their score for the current metric
        sorted_methods = sorted(method_scores.items(), key=lambda x: x[1][metric])
        
        print(f"\nTop {n} methods for {metric}:")
        for method, scores in sorted_methods[:n]:
            print(f"Method: {method}, Score: {scores[metric]}")
            # Calculate overall scores
            if method not in overall_scores:
                overall_scores[method] = 0
            overall_scores[method] += scores[metric]
    
    # Print overall scores
    sorted_overall = sorted(overall_scores.items(), key=lambda x: x[1])
    print(f"\nTop {n} methods overall:")
    for method, score in sorted_overall[:n]:
        print(f"Method: {method}, Overall Score: {score}")

def main():
    DATA_DIR = Path(__file__).resolve().parent / "data" / "solutions"
    df_sol_times = gather_sol_times(DATA_DIR)
    
    # Filter the data for different solution types
    for solution_type in ['optimal', 'immediate_first', 'first_good', 'timed_out']:
        if len(df_sol_times) > 0:
            filtered_df = df_sol_times[df_sol_times['type'] == solution_type]
            if len(filtered_df) > 0:
                print(solution_type, df_sol_times.iloc[0]['value'])
                print(get_top_methods(aggregate_scores(filtered_df, df_sol_times.iloc[0]['value'], solution_type), n=10))
                print_top_methods(aggregate_scores_(filtered_df, df_sol_times.iloc[0]['value'], solution_type), n=10)
                #plot_sol_times_lines(filtered_df, solution_type= solution_type, value_type=df_sol_times.iloc[0]['value'])
                #plot_sol_times_barchart(filtered_df, solution_type= solution_type, value_type=df_sol_times.iloc[0]['value'])

if __name__ == "__main__":
    main()