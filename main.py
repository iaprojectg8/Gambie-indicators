from data_processing.main_functions import *
from data_processing.plot import plot_results_from_dataframe
from utils.variables import DATASET_FOLDER, GRAPH_FOLDER, FINAL_CSV_PATH, DAILY_AGG_FOLDER, YEARLY_AGG_FOLDER

def process_data(filename, save_csv:bool):
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
    saving_filename = filename.split("\\")[1]
 
    # Making on different time scale
    data_daily_growing_season, data_yearly_mean_temp = daily_work(data)
    save_agg_csv(save_csv, DAILY_AGG_FOLDER, saving_filename, data_daily_growing_season)
    data_monthly_growing_season = monthly_work(data_daily_growing_season)
    data_yearly_growing_season, df_aggregate_yearly = yearly_work(data_daily_growing_season, data_monthly_growing_season, data_yearly_mean_temp)
    save_agg_csv(save_csv, YEARLY_AGG_FOLDER, saving_filename, df_aggregate_yearly)

    # Looping on periods to calculate risks on them
    risk_df_data = loop_to_process_data_on_periods(data_yearly_growing_season, SCORE_COLUMNS)
    risk_df, final_score_columns = convert_into_dataframe(risk_df_data)
    data_yearly_growing_season['temperature_2m_mean'] = data_yearly_mean_temp
    # Making a clean table of the different final score
    final_score_df = create_final_score_dataframe(lat,lon, PERIODS, final_score_columns, risk_df)
    final_score_df.to_csv("final_score.csv",index=False)

    return final_score_df, final_score_columns


def save_agg_csv(save_csv, folder, filename, df):
    if save_csv:
        path = os.path.join(folder, filename)
        df.to_csv(path)

def calculate_score_for_one_point():
    """
    Function to calculate and plot scores for one specific data point (single location).
    """
    path = "Gambie_dataset/cmip6_era5_data_daily_0.csv"
    graph_path = "final_graph"
    plot_args = process_data(path)
    plot_results_from_dataframe(*plot_args, graph_path=graph_path)


def get_point_for_score():
    df_all_coords= pd.read_csv("unique_coords_to_request.csv")
    df_score_coords = pd.read_csv("point_to_ask_score_for.csv")
    df_score_coords.columns = df_score_coords.columns.str.strip()
    tree = KDTree(df_all_coords[['lat', 'lon']].values)
    coords_to_ask = []
    for _,row in df_score_coords.iterrows():
        lon, lat = row["lon"], row["lat"]
        _, index = tree.query([lat, lon], k=1)  # Get index of the nearest point
        closest_point = df_all_coords.iloc[index]  # Retrieve data for the nearest point

        coords_to_ask.append((closest_point["lat"], closest_point["lon"]))

    return coords_to_ask




def calculate_score_for_all_points():
    """
    Function to calculate and plot scores for all points in a dataset (multiple locations).
    """
    df = pd.DataFrame()
    if not os.path.exists(GRAPH_FOLDER):
        os.makedirs(GRAPH_FOLDER)
    if not os.path.exists(YEARLY_AGG_FOLDER):
        os.makedirs(YEARLY_AGG_FOLDER)
    if not os.path.exists(DAILY_AGG_FOLDER):
        os.makedirs(DAILY_AGG_FOLDER)

    files_list = os.listdir(DATASET_FOLDER)

    index_to_make_csv_with = ['cmip6_era5_data_daily_89.csv', 
                              'cmip6_era5_data_daily_53.csv',
                              'cmip6_era5_data_daily_194.csv',
                              'cmip6_era5_data_daily_101.csv'
                            ]
    
    coords_to_get_score = get_point_for_score()
    df_final_score = pd.DataFrame()

    for index, filename in enumerate(tqdm(files_list, desc="Creating graphs for each point and filling the dataframe"), start=1):
        
        save_csv = filename in index_to_make_csv_with
        filename_graph = filename.split(".")[0]

        graph_path = os.path.join(GRAPH_FOLDER, filename_graph)
        data_path= os.path.join(DATASET_FOLDER, filename)
        plot_args = process_data(filename=data_path, save_csv=save_csv)
        # plot_results_from_dataframe(*plot_args, graph_path=graph_path)
        new_final_row = pd.DataFrame(plot_args[0])
        for  lat, lon in coords_to_get_score:
            if abs(new_final_row["LAT"].values[0]- lat)<10e-8 and abs(new_final_row["LON"].values[0]- lon)<10e-8:
                print("in the condition for final score")
                df_final_score = pd.concat([df_final_score, new_final_row])
        new_final_row["filename"] = filename_graph
        new_final_row.set_index('filename', inplace=True)

        if df is None : 
            df = new_final_row
        else:
            df = pd.concat([df, new_final_row])
    df.to_csv(FINAL_CSV_PATH)
    df_final_score.to_csv("final_score_wanted.csv")


# calculate_score_for_one_point()
calculate_score_for_all_points()