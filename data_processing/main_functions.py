from utils.imports import *
from utils.variables import *
from data_processing.classify import classify_risk_frequency, classify_risk_score
from data_processing.calculation import *

# --- Main functions ---
def loads_data(filename):
    """
    Loads the CSV data with daily timestamps.
    
    Arg:
    filename (str): The path to the CSV file.
    
    Returns:
    tuple:
        - (pd.DataFrame): Loaded data with 'date' as the index.
        - (float): Latitude of the data point.
        - (float): Longitude of the data point.
    """
    # Load the CSV data with daily timestamps
    data = pd.read_csv(filename, parse_dates=['date'])
    
    # Extract the lat and lon and the point to identify it later to make the raster
    lat = data.loc[0, "lat"]
    lon = data.loc[0, "lon"]

    # Set the index to the date for the process to be easier
    data = data.set_index("date")
    return data, lat, lon


def daily_work(data):
    """
    Processes daily data to filter growing season and add indicators.
    
    Arg:
        data (DataFrame): Original daily data.

    Returns:
        DataFrame: Daily data with growing season and added indicators.
    """
    data_daily_growing_season = filter_growing_season(data)
    data_daily_growing_season = add_indicators(data_daily_growing_season)

    return data_daily_growing_season


def monthly_work(data_daily_growing_season):
    """
    Processes daily growing season data into monthly aggregations.
    
    Arg:
        data_daily_growing_season (DataFrame): Daily growing season data.

    Returns:
        DataFrame: Monthly aggregated data.
    """
    data_monthly_growing_season = aggregate_monthly(data_daily_growing_season)
    data_monthly_growing_season = calculate_monthly_aggregations(data_monthly_growing_season)
    data_monthly_growing_season = add_threshold_flags(data_monthly_growing_season)

    return data_monthly_growing_season

def yearly_work(data_daily_growing_season, data_monthly_growing_season):
    """
    Processes daily and monthly data into yearly aggregations and adds season indicators.
    
    Args:
        data_daily_growing_season (DataFrame): Daily growing season data.
        data_monthly_growing_season (DataFrame): Monthly aggregated data.

    Returns:
        DataFrame: Yearly aggregated data with season indicators.
    """
    data_yearly_growing_season = aggregate_yearly(data_monthly_growing_season)
    data_yearly_growing_season = season_indicator(data_daily=data_daily_growing_season, data_yearly=data_yearly_growing_season)

    return data_yearly_growing_season


def loop_to_process_data_on_periods(data_yearly_growing_season, score_columns):
    """
    Loops through defined periods and processes risk data for each period.
    
    Args:
        data_yearly_growing_season (DataFrame): Yearly aggregated data.
        score_columns (list): List of score columns.

    Returns:
        DataFrame: Risk data with frequencies, risks, and scores for each period.
    """
    period_zero_freq,period_risk_classification, risk_df_data, period_data = {}, {}, {}, {}

    # Main loop that iterates over periods and process each one
    for start, end in PERIODS:  
        # Filter the data for the current period
        period_label = f"{start}-{end}"
        period_data[period_label] = data_yearly_growing_season[
            (data_yearly_growing_season.index.year >= start) & 
            (data_yearly_growing_season.index.year <= end)
        ]
        
        # Calculate the frequency of 0 scores for this period
        period_zero_freq[period_label] = (period_data[period_label][score_columns] == 0).sum() / len(period_data[period_label]) * 100
        
        # Transform frequency into scores
        period_risk_classification[period_label] = period_zero_freq[period_label].apply(classify_risk_frequency)
        period_zero_freq, period_risk_classification = final_score_averaging(period_zero_freq,period_risk_classification, period_label )

        # Classify and give labels
        period_risk_classification[period_label] = period_risk_classification[period_label].apply(classify_risk_score)
        risk_df_data = filling_risk_dictionary(risk_df_data, period_label, period_zero_freq, period_risk_classification)

    return risk_df_data


def convert_into_dataframe(risk_df_data):
    """
    Converts risk data into a DataFrame and saves it to a CSV file.
    
    Arg:
    risk_df_data (dict): Dictionary containing risk data for all periods.

    Returns:
    tuple: A tuple containing:
        - DataFrame: Risk DataFrame.
        - list: List of score column names.
    """
    risk_df = pd.DataFrame(risk_df_data)
    score_columns = list(risk_df.index)

    return risk_df, score_columns


def create_final_score_dataframe(lat, lon, periods, score_columns, risk_df):
    """
    Creates a final score DataFrame with scores for each period and column.
    
    Args:
        lat (float): Latitude of the data point.
        lon (float): Longitude of the data point.
        periods (list): List of periods.
        score_columns (list): List of score columns.
        risk_df (DataFrame): DataFrame with risk scores.

    Returns:
        DataFrame: Final DataFrame containing scores for each period.
    """
    final_score_df = pd.DataFrame(columns=['LAT', 'LON'])
    final_score_df["LAT"] = [lat]
    final_score_df["LON"] = [lon]

    for start, end in periods:
        for score_column in score_columns:
            final_score_df[f"{score_column}_{start}_{end}"] = risk_df.loc[score_column, f'Score {start}-{end}']

    return final_score_df

    


    
    



