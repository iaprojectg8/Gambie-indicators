VARIABLES_LIST = ["temperature_2m_mean", "temperature_2m_max", "temperature_2m_min", "wind_speed_10m_mean",
          "wind_speed_10m_max", "shortwave_radiation_sum", "relative_humidity_2m_mean", "relative_humidity_2m_max", 
          "relative_humidity_2m_min", "precipitation_sum", "soil_moisture_0_to_10cm_mean"]

SCORE_COLUMNS = ['temperature_score', 'gdd_score', 'precipitation_score', 'soil_moisture_score',
                    'wind_score', 'heat_stress_score', 'humidity_score', 'season_start_shift_score', 
                    'season_end_shift_score', 'season_length_score']



DATASET_FOLDER ="Extended_Gambie_dataset"    
GRAPH_FOLDER = "Extended_Gambie_graphs"
FINAL_CSV_PATH = "extended_final.csv"
COORDINATES_FILE = "unique_coords_2.csv"
SHAPE_FILE_PATH  = "shape_folder_Gambia/AOI_Gambia.shp"


PERIODS = [
    (1950, 1969), 
    (1970, 1989), 
    (1990, 2009), 
    (2010, 2029), 
    (2030, 2050)
    ]


YEARLY_THRESHOLDS = {
    'yearly_min_temp_suitability_threshold': 24,
    'yearly_max_temp_suitability_threshold': 30,
    'yearly_max_cv_temp_suitability': 10,
    'yearly_min_gdd_suitability_threshold': 1500,
    'yearly_max_gdd_suitability_threshold': 3500,
    'yearly_min_prec_suitability_threshold': 700,
    'yearly_max_prec_suitability_threshold': 2000,
    'yearly_max_cv_prec_suitability': 150,
    'yearly_min_soil_moisture_threshold': 0.2,
    'yearly_max_soil_moisture_threshold': 0.3,
    'yearly_min_solar_radiation_suitability_threshold': 20,
    'yearly_max_solar_radiation_suitability_threshold': 30,
    'yearly_max_season_start_shift': 20,
    'yearly_max_season_end_shift': 15,
    'yearly_min_season_length': 120
}

DAILY_THRESHOLDS = {
    'gdd_base_temp': 10,
    'daily_prec_threshold': 5,
    'daily_ext_prec_threshold': 50,
    'daily_dry_day_threshold': 1,
    'daily_heat_stress_threshold': 35,
    'daily_wind_stress_threshold': 10,
    'daily_humidity_risk': 90
}

MONTHLY_THRESHOLDS = {
    'monthly_wind_stress_threshold': 5,
    'monthly_heat_stress_threshold': 10,
    'monthly_humidity_stress_threshold': 10
}


MONTHLY_AGG_FUNCTIONS = {
    'temperature_2m_mean': 'mean',
    'precipitation_sum': 'sum',
    'soil_moisture_0_to_10cm_mean': 'mean',
    'solar_radiation_mj': 'mean',
    'gdd': 'sum',
    'is_precipitation_above_threshold': 'sum',
    'is_soil_moisture_above_threshold': 'sum',
    'is_extreme_precipitation': 'sum',
    'is_heat_stress': 'sum',
    'is_humidity_above_threshold': 'sum',
    'is_wind_above_threshold': 'sum',
    'consecutive_dry_days': 'max'
}


YEARLY_AGG_FUNCTIONS = {
    'temperature_2m_mean': 'mean',
    'precipitation_sum': 'sum',
    'soil_moisture_0_to_10cm_mean': 'mean',
    'solar_radiation_mj': 'mean',
    'gdd': 'sum',
    'cv_temperature': 'mean',
    'cv_precipitation': 'mean',
    'is_precipitation_above_threshold': 'sum',
    'is_extreme_precipitation': 'sum',
    'is_heat_days_above_threshold': 'sum',
    'is_humidity_days_above_threshold': 'sum',
    'is_wind_days_above_threshold': 'sum',
    'consecutive_dry_days': 'max'
}
  