from utils.imports import *
from utils.variables import *
from data_processing.classify import classify_risk_frequency, classify_risk_score
 

# --- Daily calculation ---

def filter_growing_season(data):
    """
    Filters the data for the growing season (May to October).
    
    Args:
        data (DataFrame): Daily weather data.

    Returns:
        DataFrame: Filtered DataFrame for the growing season.
    """
    return data[(data.index.month >= SEASON_THRESHOLDS['start']) & (data.index.month <= SEASON_THRESHOLDS['end'])].copy()

def add_indicators(data):
    """
    Adds various indicators to the growing season data thanks to daily thresholds.
    
    Args:
        data (DataFrame): Filtered data for the growing season.

    Returns:
        DataFrame: DataFrame with added indicators.
    """
    data.loc[:, 'gdd'] = np.maximum(
        (data['temperature_2m_max'] + data['temperature_2m_min']) / 2 - DAILY_THRESHOLDS['gdd_base_temp'], 0)

    data = data.assign(
        is_extreme_precipitation=data['precipitation_sum'] > DAILY_THRESHOLDS['daily_ext_prec_threshold'],
        consecutive_dry_days=(data['precipitation_sum'] < DAILY_THRESHOLDS['daily_dry_day_threshold']).astype(int)
                              .groupby((data['precipitation_sum'] >= DAILY_THRESHOLDS['daily_dry_day_threshold']).cumsum()).cumsum(),
        is_heat_stress=data['temperature_2m_mean'] > DAILY_THRESHOLDS['daily_heat_stress_threshold'],
        is_wind_above_threshold=data['wind_speed_10m_max'] > DAILY_THRESHOLDS['daily_wind_stress_threshold'],
        is_humidity_above_threshold=data['relative_humidity_2m_mean'] > DAILY_THRESHOLDS['daily_humidity_risk'],
        soil_moisture_deficit = np.maximum(0, DAILY_THRESHOLDS['daily_soil_moisture_threshold'] - data['soil_moisture_0_to_10cm_mean']),
        solar_radiation_mj=data['shortwave_radiation_sum']
    )

    return data

# --- Monthly calculation ---

def aggregate_monthly(data_daily : pd.DataFrame):
    """
    Aggregates daily data into monthly data for the growing season.
    
    Args:
        data (DataFrame): Data for the growing season.

    Returns:
        DataFrame: Monthly aggregated data.
    """
    return data_daily.resample('ME').agg(MONTHLY_AGG_FUNCTIONS)


def calculate_coefficient_of_variation(data_monthly):
    """
    Calculate the coefficient of variation (CV) for a given series.
    
    Arg:
        series (Series): A pandas Series to calculate CV for.
    
    Returns:
        float: Coefficient of variation (in %). Returns NaN if the count of non-NaN values is less than or equal to 1.
    """
    return data_monthly.std() / data_monthly.mean() * 100 if data_monthly.count() > 1 else np.nan


def calculate_monthly_aggregations(data_monthly):
    """
    Aggregates daily data into monthly data and calculates coefficient of variation for temperature and precipitation.
    
    Arg:
        data_monthly (DataFrame): Monthly weather data.

    Returns:
        DataFrame: Monthly data with CV columns added.
    """
    # Coefficient of variation for temperature and precipitation
    data_monthly['cv_temperature'] = data_monthly['temperature_2m_mean'].groupby(
        data_monthly.index.year).transform(calculate_coefficient_of_variation)
    
    data_monthly['cv_precipitation'] = data_monthly['precipitation_sum'].groupby(
        data_monthly.index.year).transform(calculate_coefficient_of_variation)
    
    return data_monthly

def add_threshold_flags(data_monthly):
    """
    Adds flags for wind, heat, and humidity days above specified thresholds.
    
    Arg:
        data_monthly (DataFrame): Monthly weather data.

    Returns:
        DataFrame: Monthly data with added flags for days above thresholds.
    """
    data_monthly['is_wind_days_above_threshold'] = np.where(
        data_monthly['is_wind_above_threshold'] > MONTHLY_THRESHOLDS["monthly_wind_stress_threshold"], 1, 0)

    data_monthly['is_heat_days_above_threshold'] = np.where(
        data_monthly['is_heat_stress'] > MONTHLY_THRESHOLDS["monthly_heat_stress_threshold"], 1, 0)

    data_monthly['is_humidity_days_above_threshold'] = np.where(
        data_monthly['is_humidity_above_threshold'] > MONTHLY_THRESHOLDS["monthly_humidity_stress_threshold"], 1, 0)

    return data_monthly


# --- Yearly calculation ---
def aggregate_yearly(data_monthly: pd.DataFrame):
    """
    Aggregates monthly data into yearly data for the growing season.
    
    Args:
        data (DataFrame): Data for the growing season.

    Returns:
        DataFrame: Monthly aggregated data.
    """
    return data_monthly.resample('YE').agg(YEARLY_AGG_FUNCTIONS)

def season_indicator(data_daily, data_yearly):
    """
    Adds season start shift, and length to yearly data.
    
    Args:
        data_daily (DataFrame): Daily weather data.
        data_yearly (DataFrame): Yearly aggregated data.
    
    Returns:
        DataFrame: Updated yearly data with season indicators.
    """
    # Apply the calculate_season_start and calculate_season_end functions to each year's data
    season_start_shift = data_daily.groupby(data_daily.index.year).apply(lambda df: calculate_season_start(df)).values
    season_length = data_daily.groupby(data_daily.index.year).apply(lambda df: calculate_season_length(df)).values

    # Now, assign these shifts to the corresponding year in `data_yearly_growing_season`
    data_yearly['season_start_shift'] = season_start_shift
    data_yearly['season_length'] = season_length

    data_yearly = data_yearly.join(data_yearly.apply(indicator_scores, axis=1, result_type='expand'))

    return data_yearly


# --- Season calculation ---
# Define rainy season starting from May (for season start shift)
def calculate_season_start(df, threshold=5, consecutive_days=7):
    """
    Calculate the season start shift based on cumulative precipitation over consecutive days.
    
    Args:
        df (DataFrame): Daily weather data.
        threshold (int): Cumulative precipitation threshold.
        consecutive_days (int): Number of consecutive days for threshold.

    Returns:
        int: Number of days shifted from the reference start date (June 1).
    """
    rolling_sum = df['precipitation_sum'].rolling(window=consecutive_days).sum()
    season_start = df.index[rolling_sum >= threshold].min()

    return (season_start - pd.Timestamp(f'{season_start.year}-06-01', tz=season_start.tz)).days

def calculate_season_length(df, threshold_start=2, consecutive_days_start=7, threshold_end=2, consecutive_days_end=7):
    """
    Calculate the season length based on precipitation thresholds.
    
    Args:
        df (DataFrame): Daily weather data.
        threshold_start (int): Cumulative precipitation threshold for start.
        consecutive_days_start (int): Number of consecutive days for season start.
        threshold_end (int): Cumulative precipitation threshold for end.
        consecutive_days_end (int): Number of consecutive days for season end.

    Returns:
        int: The length of the season in days.
    """
    rolling_sum_start = df['precipitation_sum'].rolling(window=consecutive_days_start).sum()
    season_start = df.index[rolling_sum_start >= threshold_start].min()
    rolling_sum_end = df['precipitation_sum'].rolling(window=consecutive_days_end).sum()
    season_end = df.index[rolling_sum_end > threshold_end].max()
    return (season_end - season_start).days


# --- Indicator score calculation ---
def indicator_scores(row):
    """
    Calculates various indicator scores for a given row of data based on yearly thresholds.
    
    Arg:
        row (Series): A row of data from the yearly DataFrame.

    Returns:
        dict: Dictionary of calculated indicator scores.
    """
    # Initialize the indicator dictionary
    indicator_scores = {}

    # Create indicators using the YEARLY_THRESHOLDS dictionary
    indicator_scores['temperature_score'] = 1 if YEARLY_THRESHOLDS['yearly_min_temp_suitability_threshold'] <= row['temperature_2m_mean'] <= YEARLY_THRESHOLDS['yearly_max_temp_suitability_threshold'] and row['cv_temperature'] < YEARLY_THRESHOLDS['yearly_max_cv_temp_suitability'] else 0
    indicator_scores['gdd_score'] = 1 if YEARLY_THRESHOLDS['yearly_min_gdd_suitability_threshold'] <= row['gdd'] <= YEARLY_THRESHOLDS['yearly_max_gdd_suitability_threshold'] else 0
    indicator_scores['precipitations_score'] = 1 if YEARLY_THRESHOLDS['yearly_min_prec_suitability_threshold'] <= row['precipitation_sum'] <= YEARLY_THRESHOLDS['yearly_max_prec_suitability_threshold'] and row['cv_precipitation'] < YEARLY_THRESHOLDS['yearly_max_cv_prec_suitability'] else 0
    indicator_scores['ext_precipitation_score'] = 1 if row['is_extreme_precipitation'] <= YEARLY_THRESHOLDS['yearly_max_ext_prec_days_threshold'] else 0
    indicator_scores['soil_moisture_score'] = 1 if row['soil_moisture_deficit'] <= YEARLY_THRESHOLDS['yearly_max_soil_moisture_deficit_threshold'] else 0
    indicator_scores['wind_score'] = 1 if row['is_wind_days_above_threshold'] == 0 else 0
    indicator_scores['heat_stress_score'] = 1 if row['is_heat_days_above_threshold'] == 0 else 0
    indicator_scores['humidity_score'] = 1 if row['is_humidity_days_above_threshold'] == 0 else 0
    indicator_scores['solar_radiation_score'] = 1 if row['solar_radiation_mj'] >= YEARLY_THRESHOLDS['yearly_min_solar_radiation_suitability_threshold'] else 0

    # Calculate season score
    indicator_scores['season_start_shift_score'] = 1 if row['season_start_shift'] > YEARLY_THRESHOLDS['yearly_max_season_start_shift'] else 0
    indicator_scores['season_length_score'] = 1 if row['season_length'] > YEARLY_THRESHOLDS['yearly_min_season_length'] else 0
    
    return indicator_scores


# --- Final part included in the periods loop ---

def final_score_averaging(period_zero_freq,period_risk_classification, period_label):
    """
    Calculates the final score for both zero frequencies and risk classifications, which corresponds
    respectively to the mean of zero percentage and the mean of risk classification on all the score for each period 
    
    Args:
        period_zero_freq (dict): Dictionary of zero frequency percentages.
        period_risk_classification (dict): Dictionary of classified risk.
        period_label (str): The label for the current period.

    Returns:
        tuple: Updated dictionaries with final scores added.
    """
    period_zero_freq[period_label]["Final_Score"] = np.mean(period_zero_freq[period_label])
    period_risk_classification[period_label]["Final_Score"] = np.mean(period_risk_classification[period_label])

    return period_zero_freq, period_risk_classification

def filling_risk_dictionary(risk_df_data, period_label, period_zero_freq, period_risk_classification):
    """
    Fills the risk dictionary with frequency, risk, and score for the current period.
    
    Args:
        risk_df_data (DataFrame): Risk data for all periods.
        period_label (str): Label for the current period.
        period_zero_freq (dict): Zero frequency values.
        period_risk_classification (dict): Risk classification values.

    Returns:
        DataFrame: Updated risk data.
    """
    risk_df_data[f'Frequency {period_label} (%)'] = period_zero_freq[period_label]
    risk_df_data[f'Risk {period_label}'] = period_risk_classification[period_label].apply(lambda x: x[0])
    risk_df_data[f'Score {period_label}'] = period_risk_classification[period_label].apply(lambda x: x[1])
    return risk_df_data


def create_score_periods_columns(periods, score_columns):
    """
    Creates column names for each score for each period.
    
    Args:
        periods (list): List of periods in the format 'start-end'.
        score_columns (list): List of score column names.

    Returns:
        list: List of generated column names for each score and period.
    """
    return [f"{score_name}_{'_'.join(years.split('-'))}" for years in periods for score_name in score_columns]