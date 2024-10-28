from data_processing.main_functions import *
from data_processing.plot import plot_results_from_dataframe
from utils.variables import DATASET_FOLDER, GRAPH_FOLDER, FINAL_CSV_PATH


def process_data(filename):
    """
    Main function to process climate data for a specific location.

    Args:
        filename (str): Path to the input data file.

    Returns:
        final_score_df (pd.DataFrame): DataFrame with final scores.
        final_score_columns (list): List of final score column names.
    """
    # Loading the data
    data, lat, lon = loads_data(filename)
 
    # Making on different time scale
    data_daily_growing_season = daily_work(data)
    data_monthly_growing_season = monthly_work(data_daily_growing_season)
    data_yearly_growing_season = yearly_work(data_daily_growing_season, data_monthly_growing_season)

    # Looping on periods to calculate risks on them
    risk_df_data = loop_to_process_data_on_periods(data_yearly_growing_season, SCORE_COLUMNS)
    risk_df, final_score_columns = convert_into_dataframe(risk_df_data)

    # Making a clean table of the different final score
    final_score_df = create_final_score_dataframe(lat,lon, PERIODS, final_score_columns, risk_df)
    final_score_df.to_csv("final_score.csv",index=False)

    return final_score_df, final_score_columns


def calculate_score_for_one_point():
    """
    Function to calculate and plot scores for one specific data point (single location).
    """
    path = "Gambie_dataset/cmip6_era5_data_daily_0.csv"
    graph_path = "final_graph"
    plot_args = process_data(path)
    plot_results_from_dataframe(*plot_args, graph_path=graph_path)


def calculate_score_for_all_points():
    """
    Function to calculate and plot scores for all points in a dataset (multiple locations).
    """
    df = pd.DataFrame()
    if os.path.isdir(GRAPH_FOLDER):
        print("The graph folder already exists")
    else :
        os.makedirs(GRAPH_FOLDER)

    for filename in tqdm(os.listdir(DATASET_FOLDER), desc="Creating graphs for each point and filling the dataframe"):
        
        filename_graph = filename.split(".")[0]
        graph_path = os.path.join(GRAPH_FOLDER, filename_graph)
        data_path= os.path.join(DATASET_FOLDER, filename)
        plot_args = process_data(filename=data_path)
        plot_results_from_dataframe(*plot_args, graph_path=graph_path)
        new_final_row = pd.DataFrame(plot_args[0])

        if df is None : 
            df = new_final_row
        else:
            df = pd.concat([df, new_final_row])
    df.to_csv(FINAL_CSV_PATH, index=False)


# calculate_score_for_one_point()
calculate_score_for_all_points()