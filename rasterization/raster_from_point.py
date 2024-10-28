from utils.imports import *
from utils.variables import *


# --- Main function that are used in the main script ---

def apply_mask(masked, grid_score, shape_gdf, min_lon, max_lat, resolution):
    """
    Applies a mask to the grid score data based on the specified shape geometry.
    
    Args:
    - masked (bool): Flag indicating whether to apply the mask.
    - grid_score (ndarray): Array of interpolated scores.
    - shape_gdf (GeoDataFrame): GeoDataFrame containing the shape geometry.
    - min_lon (float): Minimum longitude of the grid.
    - max_lat (float): Maximum latitude of the grid.
    - resolution (float): Grid cell resolution.
    
    Returns:
    - ndarray: Masked grid score array with NaNs outside the shape geometry.
    """
    grid_score = grid_score[::-1]
    if masked:
        # Create the mask
        mask = geometry_mask([mapping(shape_gdf.geometry.unary_union)], 
                            transform=from_origin(min_lon, max_lat, resolution, resolution), 
                            out_shape=grid_score.shape)
        
        # Apply the mask to the interpolated scores
        grid_score[mask] = np.nan

    return grid_score


def get_geodataframe(filename_path):
    """
    Loads data from a CSV file and creates a GeoDataFrame with point geometries.
    
    Args:
    - filename_path (str): Path to the CSV file containing longitude and latitude columns.
    
    Returns:
    - GeoDataFrame: A GeoDataFrame with points generated from longitude and latitude data.
    """
    df = pd.read_csv(filename_path)
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["LON"], df["LAT"]))
    gdf.set_crs(epsg=4326, inplace=True)

    return gdf

def get_gdf_values(gdf, score_column):
    """
    Extracts latitude, longitude, and score values from a GeoDataFrame.
    
    Args:
    - gdf (GeoDataFrame): The GeoDataFrame containing latitude, longitude, and score data.
    - score_column (str): The column name for score data.
    
    Returns:
    - tuple: Arrays of latitude, longitude, and score values.
    """
    lat = gdf["LAT"].values
    lon = gdf["LON"].values
    score = gdf[score_column].values  # Replace with the actual column name

    return lat, lon, score


def create_grid(min_lon, min_lat, max_lon, max_lat, resolution):
    """
    Creates a grid of longitude and latitude values for raster data.
    
    Args:
    - min_lon (float): Minimum longitude of the grid.
    - min_lat (float): Minimum latitude of the grid.
    - max_lon (float): Maximum longitude of the grid.
    - max_lat (float): Maximum latitude of the grid.
    - resolution (float): Resolution of each grid cell.
    
    Returns:
    - tuple: Meshgrid arrays of longitude and latitude values.
    """
    # Create a grid for the raster
    grid_lon = np.arange(min_lon, max_lon, resolution)
    grid_lat = np.arange(min_lat, max_lat, resolution)
    grid_lon, grid_lat = np.meshgrid(grid_lon, grid_lat)
    return grid_lon, grid_lat


def create_raster_from_df(gdf, score_column, shapefile_path,masked, resolution):
    """
    Generates a raster from a GeoDataFrame and applies an optional mask.
    
    Args:
    - gdf (GeoDataFrame): The input data containing latitude, longitude, and score columns.
    - score_column (str): The column name of the score data.
    - shapefile_path (str): Path to the shapefile for masking the raster.
    - masked (bool): Flag indicating whether to apply the mask.
    - resolution (float): Grid cell resolution.
    
    Returns:
    - tuple: Masked raster grid score and affine transform for spatial alignment.
    """
    # Read the shapefile
    shape_gdf = gpd.read_file(shapefile_path)
    
    # Get Latitude, Longitude and Scores
    min_lon, min_lat, max_lon, max_lat = gdf.total_bounds
    lat, lon, score = get_gdf_values(gdf,score_column)
    grid_lon, grid_lat = create_grid(min_lon, min_lat, max_lon, max_lat, resolution)

    # Interpolate the irregular data to the regular grid
    grid_score = griddata((lon, lat), score, (grid_lon, grid_lat), method='linear')
    grid_score = apply_mask(masked, grid_score, shape_gdf, min_lon, max_lat, resolution)


    # Define the affine transform for the raster from top-left
    transform = from_origin(min_lon, max_lat, resolution, resolution)

    return grid_score, transform


def write_multiband_tif(output_path, grid_score_list, transform_list):
    """
    Writes multiple bands of raster data to a GeoTIFF file.
    
    Args:
    - output_path (str): The path where the output GeoTIFF will be saved.
    - grid_score_list (list): A list of 2D arrays representing the raster data for each band.
    - transform_list (list): A list of affine transformations for each raster band.
    """
    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=grid_score_list[0].shape[0],
        width=grid_score_list[0].shape[1],
        count=len(grid_score_list),
        dtype=grid_score_list[0].dtype,
        crs='EPSG:4326',
        transform=transform_list[0],
    ) as dst:
        for i in range(len(grid_score_list)):
            dst.write(grid_score_list[i], i+1)

def plot_tif_multiband(output_path, gdf, shapefile_path, score_type, score_columns):
    # Load the rasters
    rasters = []
    global_min, global_max = np.inf, -np.inf  # Initialize extreme values
    with rasterio.open(output_path) as src:
        for i in range(len(score_columns)):
            data = src.read(i + 1)
            rasters.append(data)
            global_min = min(global_min, np.nanmin(data))  # Update global min
            global_max = max(global_max, np.nanmax(data))  # Update global max
    
    # Variable init
    min_lon, min_lat, max_lon, max_lat = gdf.total_bounds
    shape_gdf = gpd.read_file(shapefile_path)

    # Create figure and axis
    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.25)  # Adjust the bottom for the slider

    # Initial display
    current_frame = 0
    # ctx.add_basemap(plt.gca(), crs="EPSG:4326", source=ctx.providers.OpenStreetMap.Mapnik)
    img = ax.imshow(rasters[current_frame], extent=(min_lon, max_lon, min_lat, max_lat), cmap='RdYlGn_r', vmin=global_min, vmax=global_max)
    
    date = score_columns[current_frame].split("_")[-2:]
    start = date[0]
    end = date[1]
    ax.set_title(f"{score_type.capitalize()} {start}-{end}")
    # ax.set_title(f"Image Epoch {current_frame + 1}")
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    shape_gdf.boundary.plot(ax=ax, color='black', linewidth=1)  # Overlay the shape

    # Color bar
    cbar = fig.colorbar(img, ax=ax, orientation="vertical")
    cbar.set_label("Score Value")
    

    # Slider configuration
    ax_slider = plt.axes([0.1, 0.01, 0.8, 0.03])  # [left, bottom, width, height]
    slider = Slider(ax_slider, 'Epoch', 0, len(rasters) - 1, valinit=current_frame, valstep=1)
    

    # Update function
    def update(val):
        frame = int(slider.val)
        
        # Update the image
        img.set_array(rasters[frame])  
        
        date = score_columns[frame].split("_")[-2:]
        start = date[0]
        end = date[1]
        # Update the title
        ax.set_title(f"{score_type.capitalize()} {start}-{end}")
        fig.canvas.draw_idle()  # Refresh the figure

    # Connect the slider to the update function
    slider.on_changed(update)

    plt.show()

def main_epoch_loop():
    """
    Main loop to execute the processing of the geospatial data and visualize the results.
    
    This function:
    - Prompts the user for input to select the score type and masking options.
    - Reads the geospatial data and creates rasters for each score column.
    - Writes the raster data to a multi-band TIFF file and plots the result.
    """
    filename_path = FINAL_CSV_PATH
    gdf = get_geodataframe(filename_path)
    shapefile_path = SHAPE_FILE_PATH
    score_type = input("Enter the name of the score type you want to see: ")
    masked = int(input("Enter 1 to see the raster delimited by the country shape and 0 else: "))
    output_path = f"{score_type}_all_periods.tif"
    score_columns = []
    grid_score_list = list()
    tranform_list = list()
    for column in gdf.columns:
        if score_type in column:
            grid_score, tranform = create_raster_from_df(gdf=gdf,score_column=column ,shapefile_path=shapefile_path,
                                        masked=masked, resolution=0.001)
            grid_score_list.append(grid_score)
            tranform_list.append(tranform)
            score_columns.append(column)

    write_multiband_tif(output_path=output_path, grid_score_list=grid_score_list, transform_list=tranform_list)
    plot_tif_multiband(output_path, gdf, shapefile_path, score_type, score_columns)

if "__main__":
    main_epoch_loop()

    