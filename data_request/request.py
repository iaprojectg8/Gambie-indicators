from utils.imports import *
from utils.variables import *


cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# This open the available coordinates of open meteo that we will take

def build_api_params(lat, lon):
    """
    Constructs the API parameters for the request based on latitude, longitude, and variables.
    
    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
    
    Returns:
        dict: Parameters for the API request.
    """
    return {
        "latitude": lat,
        "longitude": lon,
        "start_date": "1950-01-01",
        "end_date": "2050-12-31",
        "models": "MRI_AGCM3_2_S",
        "daily": VARIABLES_LIST,
        "timezone": "auto",
        "wind_speed_unit": "ms"
    }

def get_lat_lon(row):
    """
    Extracts latitude and longitude from a DataFrame row.
    
    Args:
        row (pd.Series): A row from the DataFrame containing 'lat' and 'lon' fields.
    
    Returns:
        tuple: A tuple containing the latitude and longitude.
    """
    lat = row["lat"]
    lon = row["lon"]

    return lat, lon


def get_data_from_open_meteo(url, params):
    """
    Fetches weather data from the Open Meteo API using specified URL and parameters.
    
    Args:
        url (str): The API endpoint URL for fetching weather data.
        params (dict): Parameters for the API request.
    
    Returns:
        dict: The API response containing weather data.
    """
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    return response


def fill_daily_dict(daily, lat, lon):
    """
    Fills a dictionary with daily weather data including date, latitude, and longitude.
    
    Args:
        daily (object): Object containing daily weather data from the API response.
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        
    Returns:
        dict: A dictionary with the date, latitude, longitude, and weather variables.
    """
    daily_data = {
        "date": pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left"
        ),
        "lat": lat,
        "lon": lon
    }
    # Loop through the variable list and extract data using their respective indices
    for var_idx, var_name in enumerate(VARIABLES_LIST):
        daily_data[var_name] = daily.Variables(var_idx).ValuesAsNumpy()

    return daily_data


def save_daily_dataset(daily_data, dataset_folder, filename_base, index, lat, lon):
    """
    Saves the daily weather data to a CSV file.
    
    Args:
        daily_data (dict): Dictionary containing daily weather data.
        dataset_folder (str): Path to the folder where the file will be saved.
        filename_base (str): Base name for the output CSV file.
        index (int): Index for distinguishing multiple output files.
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
    """
    daily_dataframe = pd.DataFrame(data = daily_data)
    os.path.join(dataset_folder, filename_base)
    daily_dataframe.to_csv(f'{dataset_folder}/{filename_base}_{index}.csv')
    print(f"Request number {index} done for Lat:{lat}, and Lon:{lon}")




# --- Main function to get openmeteo data from Gambia ---
def request_all_data_gambie(coordinates_csv, dataset_folder):
    """
    Orchestrates the process of requesting and saving daily weather data for multiple coordinates.
    
    Args:
        coordinates_csv (str): Path to the CSV file containing coordinates.
        dataset_folder (str): Path to the folder where the results will be saved.
    """
    filename_base = "cmip6_era5_data_daily"
    url ="https://climate-api.open-meteo.com/v1/climate"
    df = pd.read_csv(coordinates_csv)
    
    for index, row in df.iterrows():

        lat, lon = get_lat_lon(row)
        params = build_api_params(lat, lon)

        try:
            
            response = get_data_from_open_meteo(url, params)
            if response:
                
                daily = response.Daily()
                daily_data = fill_daily_dict(daily, lat, lon)
                save_daily_dataset(daily_data, dataset_folder, filename_base, index, lat, lon)

            else:
                print(f"No data for point: Latitude {lat}, Longitude {lon}")
            
        except Exception as e:
            print(f"Error for point: Latitude {lat}, Longitude {lon} - {str(e)}")
        # Time sleep here to not causing trouble reaching the request limit
        time.sleep(2)

request_all_data_gambie(COORDINATES_FILE, DATASET_FOLDER)