
from utils.imports import *
from utils.variables import PERIODS
from data_processing.classify import classify_score_exposure

def plot_results_from_dataframe(df : pd.DataFrame, columns, graph_path):
    """
    Function to create bar plots for each score variable across periods.

    Args:
        df (pd.DataFrame): Dataframe containing scores.
        columns (list): List of score column names to plot.
        graph_path (str): File path to save the plot image.

    Returns:
        Saves the bar plot graph to the specified path.
    """
    # Initialize basic variables to make each graph
    num_rows, num_cols, num_vars  = 4, 3, len(columns)
    periods = [f"{start}-{end}" for (start, end) in PERIODS]

    # Create the figure
    fig, axes = initialize_figure_and_axes(num_rows, num_cols)
    make_each_graph(columns, axes, df, periods)
    fig = remove_unused_axes(axes, num_vars, fig)
    
    # Set the overall title and save the graph
    plt.suptitle('Evolution of Scores Across Variables and Periods', fontsize=16)
    plt.savefig(f'{graph_path}_score.png')
    plt.close()


def initialize_figure_and_axes(num_rows, num_cols):
    """
    Helper function to initialize a figure and subplots for multiple score variables.

    Args:
        num_rows (int): Number of subplot rows.
        num_cols (int): Number of subplot columns.

    Returns:
        fig (Figure): The figure object.
        axes (ndarray): Array of axes objects.
    """
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(15, num_rows * 4), layout="constrained") 
    axes = axes.flatten()
    return fig, axes

def make_each_graph(columns, axes, df, periods):
    """
    Function to generate each individual graph.

    Args:
        columns (list): List of score column names to plot.
        axes (ndarray): Array of axes for plotting.
        df (pd.DataFrame): Dataframe containing scores.
        periods (list): List of periods to plot along the x-axis.

    Returns:
        Generates the graphs on the given axes.
    """
    for score_column, ax in zip(columns, axes):
       
        # Filter scores in function of their names and assign colors to the score
        df_score = df.filter(like=score_column).iloc[0].tolist()
        score_levels_colors = [classify_score_exposure(score) for score in df_score]
        score_levels = [level for level, _ in score_levels_colors]
        colors = [color for _, color in score_levels_colors]

        # Create a bar plot for this score column
        bars = ax.bar(periods, df_score, color=colors)

        # Put the class label at the center of each bar
        center_class_labels(bars, ax, score_levels)

        if score_column == "Final_Score":
            format_final_score_plot(bars, ax, score_column)
        else : 
            format_standard_score(ax, score_column)

def remove_unused_axes(axes, num_vars, fig):
    """
    Helper function to remove unused subplot axes.

    Args:
        axes (ndarray): Array of axes objects.
        num_vars (int): Number of variables (plots) to keep.
        fig (Figure): The figure object.

    Returns:
        The modified figure with unused axes removed.
    """
    for ax in axes[num_vars:]:
        fig.delaxes(ax)
    return fig


def center_class_labels(bars, ax, score_levels):
    """
    Function to center class labels inside each bar of the bar plot.

    Args:
        bars (BarContainer): Bar container from the bar plot.
        ax (Axes): Current axis object.
        score_levels (list): List of score level labels to place inside bars.

    Returns:
        Centers the labels inside each bar on the plot.
    """
    for bar, level in zip(bars, score_levels):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() / 2, level,
                ha='center', va='center', fontsize=5,
                fontweight='bold', color='black',
                bbox=dict(facecolor='white', alpha=1.0, edgecolor='none', boxstyle='round,pad=0.3'))

def format_final_score_plot(bars, ax, score_column):
    """
    Helper function to format the plot for the final score.

    Args:
        bars (BarContainer): Bar container from the bar plot.
        ax (Axes): Current axis object.
        score_column (str): Name of the score column.

    Returns:
        Formats the final score plot with special styling.
    """
    
    # Put black edge to the bar to make contrast in comparison to the other graphs
    for bar in bars:
        bar.set_edgecolor('black')
        bar.set_linewidth(2)

    # Set the title and subtitle in bold
    ax.set_title(f'{" ".join(score_column.split("_")).title()}', fontsize=12, fontweight="bold",  color="black")
    ax.set_xlabel('Period', fontsize=10, weight="bold")
    ax.set_ylabel('Final Score', fontsize=10, weight="bold")
    ax.set_ylim(0, 1)

    # Set the legends and tick bold
    for tick in ax.get_xticklabels():
        tick.set_fontsize(8)
        tick.set_fontweight('bold')
    for tick in ax.get_yticklabels():
        tick.set_fontweight('bold')
        tick.set_fontsize(8)

    # Make a constrated frame around the final score
    for spine in ax.spines.values():
        spine.set_edgecolor('black')  
        spine.set_linewidth(2)  


def format_standard_score(ax, score_column):
    """
    Helper function to format standard score plots.

    Args:
        ax (Axes): Current axis object.
        score_column (str): Name of the score column.

    Returns:
        Formats the standard score plot with default styling.
    """
    ax.set_title(f'{" ".join(score_column.split("_")).title()}', fontsize=12)
    ax.set_xlabel('Period', fontsize=10)
    ax.set_ylabel('Final Score', fontsize=10)
    ax.set_ylim(0, 1)

    # Set the font size a bit smaller compared to final score graph
    for tick in ax.get_xticklabels():
        tick.set_fontsize(8)
    for tick in ax.get_yticklabels():
        tick.set_fontsize(8)