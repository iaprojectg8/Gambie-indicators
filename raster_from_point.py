from utils.imports import *


# --- Matplotlib functions control ---

global pan_start
pan_start = None

def pan_start_handler(event):
    """Record the starting point for panning."""
    global pan_start, xlim_start, ylim_start
    if event.button == 1:  # Left mouse button starts the pan
        pan_start = (event.xdata, event.ydata)
        ax = plt.gca()
        xlim_start = ax.get_xlim()
        ylim_start = ax.get_ylim()
    else: 
        pan_start = None

def pan_move_handler(event):
    """Handle mouse movement while panning."""
    global pan_start, xlim_start, ylim_start
    if pan_start is None or event.xdata is None or event.ydata is None:
        return  # Ignore if no starting point or mouse is out of bounds

    # Calculate the offset from the starting point
    dx = pan_start[0] - event.xdata
    dy = pan_start[1] - event.ydata

    # Update limits based on the movement
    ax = plt.gca()
    ax.set_xlim([xlim_start[0] + dx, xlim_start[1] + dx])
    ax.set_ylim([ylim_start[0] + dy, ylim_start[1] + dy])

    

def pan_end_handler(event):
    """End the panning action."""
    global pan_start
    if event.button == 1:  # Left mouse button
        pan_start = None  # Reset the pan start to stop panning
    plt.draw()  # Redraw the plot

def zoom(event):
    # Get the current x and y limits
    ax = plt.gca()
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    # Define the zoom factor
    zoom_factor = 1.2

    # Zoom in
    if event.button == 'up':
        scale_factor = 1 / zoom_factor
    # Zoom out
    elif event.button == 'down':
        scale_factor = zoom_factor
    else:
        return

    # Compute the new limits based on the zoom factor
    ax.set_xlim([event.xdata - (event.xdata - xlim[0]) * scale_factor,
                 event.xdata + (xlim[1] - event.xdata) * scale_factor])
    ax.set_ylim([event.ydata - (event.ydata - ylim[0]) * scale_factor,
                 event.ydata + (ylim[1] - event.ydata) * scale_factor])

    # Redraw the plot with new limits
    plt.draw()



# --- Others functions that have been tested ---


def create_sparse_raster(gdf, score_column, resolution, output_tif='sparse_raster.tif'):
    # Get the boundaries of the points
    min_lon, min_lat, max_lon, max_lat = gdf.total_bounds
    print(gdf.total_bounds)

    # Calculate the width and height of the raster based on resolution
    lat = np.unique(gdf["LAT"].values)
    empty_lat = np.arange(min_lat, max_lat,0.01)
    print(type(lat), type(empty_lat))
    lat = np.sort(np.concatenate((lat, empty_lat)))
    print(lat)
    lon = np.unique(gdf["LON"].values)
    # points = np.array([list((row["LON"], row["LAT"])) for index, row in gdf.iterrows()])

    score_dict=dict()
    for index, row in gdf.iterrows():
        score_dict[f"{row["LAT"]},{row["LON"]}"] = row[score_column]
    
    print(score_dict)

    lat_resolution = np.mean(pd.DataFrame(lat).diff())
    lon_resolution = np.mean(pd.DataFrame(lon).diff())
   

    grid = np.empty((lat.shape[0], lon.shape[0]))
    for idx_lat, la in enumerate(lat):
        for idx_lon, lo in enumerate(lon):
            key = f"{la},{lo}"
            if key in score_dict:
                grid[idx_lat][idx_lon]=score_dict[key]
            else:
                grid[idx_lat][idx_lon]=np.nan

    grid_score = grid[::-1]
    pd.DataFrame(grid_score).to_csv("test1.csv")
    
    print(grid_score.shape)


    transform = from_origin(min_lon, max_lat, lon_resolution, lat_resolution)


    with rasterio.open(
        output_tif,
        'w',
        driver='GTiff',
        height=grid_score.shape[0],
        width=grid_score.shape[1],
        count=1,
        dtype=grid_score.dtype,
        crs='EPSG:4326',
        transform=transform,
    ) as dst:
        dst.write(grid_score, 1)

    print(f"Sparse raster saved as {output_tif}")


def plot_data(gdf, score_column):
    scatter = plt.scatter(gdf["LON"], gdf["LAT"], c=gdf[score_column], cmap="RdYlGn_r")
    plt.gca().set_aspect('equal', adjustable='box')
    plt.colorbar(scatter, label='score_column')
    plt.show()

#########################################################################################################################################
# --- Main function that are used in the main script ---

def apply_mask(masked, grid_score, shape_gdf, min_lon, max_lat, resolution):
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

    df = pd.read_csv(filename_path)
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["LON"], df["LAT"]))
    gdf.set_crs(epsg=4326, inplace=True)

    return gdf

def get_gdf_values(gdf, score_column):
    lat = gdf["LAT"].values
    lon = gdf["LON"].values
    score = gdf[score_column].values  # Replace with the actual column name

    return lat, lon, score


def create_grid(min_lon, min_lat, max_lon, max_lat, resolution):
    
    # Create a grid for the raster
    grid_lon = np.arange(min_lon, max_lon, resolution)
    grid_lat = np.arange(min_lat, max_lat, resolution)
    grid_lon, grid_lat = np.meshgrid(grid_lon, grid_lat)
    return grid_lon, grid_lat


def create_raster_from_df(gdf, score_column, shapefile_path,masked, resolution):

    # Read the shapefile
    shape_gdf = gpd.read_file(shapefile_path)
    
    # Get Latitude, Longitude and Score
    min_lon, min_lat, max_lon, max_lat = gdf.total_bounds
    lat, lon, score = get_gdf_values(gdf,score_column)
    grid_lon, grid_lat = create_grid(min_lon, min_lat, max_lon, max_lat, resolution)

    # Interpolate the irregular data to the regular grid
    grid_score = griddata((lon, lat), score, (grid_lon, grid_lat), method='linear')
    grid_score = apply_mask(masked, grid_score, shape_gdf, min_lon, max_lat, resolution)


    # Define the affine transform for the raster from top-left
    transform = from_origin(min_lon, max_lat, resolution, resolution)

    return grid_score, transform


def write_tif(output_path, grid_score, transform):
    # Create the raster file
    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=grid_score.shape[0],
        width=grid_score.shape[1],
        count=1,
        dtype=grid_score.dtype,
        crs='EPSG:4326',
        transform=transform,
    ) as dst:
        dst.write(grid_score, 1)



def plot_tif_score(grid_score, gdf, shapefile_path):
    
    # Variable init
    min_lon, min_lat, max_lon, max_lat = gdf.total_bounds
    shape_gdf = gpd.read_file(shapefile_path)

    # Create figure and interaction on it
    fig, _ = plt.subplots()
    fig.canvas.mpl_connect('scroll_event', zoom)
    fig.canvas.mpl_connect('button_press_event', pan_start_handler) 
    fig.canvas.mpl_connect('motion_notify_event', pan_move_handler)  
    fig.canvas.mpl_connect('button_release_event', pan_end_handler)  

    # Plot the shape with a black border, add open street map basemap and the tif 
    shape_gdf.boundary.plot(ax=plt.gca(), color='black', linewidth=1)
    ctx.add_basemap(plt.gca(), crs="EPSG:4326", source=ctx.providers.OpenStreetMap.Mapnik)
    plt.imshow(grid_score, extent=(min_lon, max_lon, min_lat, max_lat), cmap='RdYlGn_r')

    # Add titles
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Raster with Shape Overlay')

    plt.show()


def plot_tif(output_path, gdf, shapefile_path):
    
    with rasterio.open(output_path) as src:
        grid_score = src.read(1)
    # Variable init
    min_lon, min_lat, max_lon, max_lat = gdf.total_bounds
    shape_gdf = gpd.read_file(shapefile_path)

    # Create figure and interaction on it
    fig, _ = plt.subplots()
    fig.canvas.mpl_connect('scroll_event', zoom)
    fig.canvas.mpl_connect('button_press_event', pan_start_handler) 
    fig.canvas.mpl_connect('motion_notify_event', pan_move_handler)  
    fig.canvas.mpl_connect('button_release_event', pan_end_handler)  

    # Plot the shape with a black border, add open street map basemap and the tif 
    shape_gdf.boundary.plot(ax=plt.gca(), color='black', linewidth=1)
    ctx.add_basemap(plt.gca(), crs="EPSG:4326", source=ctx.providers.OpenStreetMap.Mapnik)
    plt.imshow(grid_score, extent=(min_lon, max_lon, min_lat, max_lat), cmap='RdYlGn_r')

    # Add titles
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Raster with Shape Overlay')

    plt.show()



def main():

    filename_path = "extended_final.csv"
    gdf = get_geodataframe(filename_path)
    shapefile_path = "AOI_Gambia 1/AOI_Gambia.shp"
    score_column = "temperature_score_2030_2050"
    output_path = "score_raster.tif"
    grid_score, transform = create_raster_from_df(gdf=gdf,score_column=score_column ,shapefile_path=shapefile_path,
                                        masked=1, output_path=output_path, resolution=0.001)
    write_tif(output_path, grid_score, transform)
    plot_tif_score(grid_score=grid_score, gdf=gdf, shapefile_path=shapefile_path)


def write_multiband_tif(output_path, grid_score_list, transform_list):
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
        frame = int(slider.val)  # Get the frame number from the slider
        
        img.set_array(rasters[frame])  # Update the image
        
        date = score_columns[frame].split("_")[-2:]
        start = date[0]
        end = date[1]
        ax.set_title(f"{score_type.capitalize()} {start}-{end}")
        fig.canvas.draw_idle()  # Refresh the figure

    # Connect the slider to the update function
    slider.on_changed(update)

    plt.show()


def plot_tif_multiband_plotly(output_path, gdf, shapefile_path, score_type, score_columns):
    # Load the rasters and determine min/max values across bands
    rasters = []
    global_min, global_max = np.inf, -np.inf
    with rasterio.open(output_path) as src:
        for i in range(len(score_columns)):
            data = src.read(i + 1)
            rasters.append(data)
            global_min = min(global_min, np.nanmin(data))
            global_max = max(global_max, np.nanmax(data))

    # Initialize coordinates from bounding box
    min_lon, min_lat, max_lon, max_lat = gdf.total_bounds

    # Read shapefile and dissolve all geometries into one
    shape_gdf = gpd.read_file(shapefile_path).dissolve()

    # Extract boundary coordinates for the dissolved geometry
    boundaries = []
    geometry = shape_gdf.geometry.iloc[0]
    if geometry.geom_type == "Polygon":
        lon, lat = geometry.exterior.xy
        boundaries.append((list(lon), list(lat)))  # Convert to list
    elif geometry.geom_type == "MultiPolygon":
        for polygon in geometry.geoms:  # Correctly iterate over each polygon
            lon, lat = polygon.exterior.xy
            boundaries.append((list(lon), list(lat)))  # Convert to list

    # Create frames for each raster epoch
    frames = []
    for i, raster in enumerate(rasters):
        date = score_columns[i].split("_")[-2:]
        start, end = date[0], date[1]
        title = f"{score_type.capitalize()} {start}-{end}"

        # Initialize data for the frame
        frame_data = [
            go.Heatmap(
                z=raster,
                x=np.linspace(min_lon, max_lon, raster.shape[1]),
                y=np.linspace(min_lat, max_lat, raster.shape[0]),
                zmin=global_min, zmax=global_max,
                colorscale="RdYlGn_r",
                colorbar=dict(title="Score Value")
            )
        ]

        frames.append(go.Frame(data=frame_data, name=title))

    # Set up the initial heatmap layout
    fig = go.Figure(
        data=frames[0].data,
        layout=go.Layout(
            title=frames[0].name,
            xaxis=dict(title="Longitude"),
            yaxis=dict(title="Latitude"),
            updatemenus=[
                dict(
                    buttons=[
                        dict(
                            label=frame.name,
                            method="animate",
                            args=[[frame.name], dict(mode="immediate", frame=dict(duration=0), transition=dict(duration=0))]
                        ) for frame in frames
                    ],
                    direction="down",
                    pad={"r": 10, "t": 10},
                    showactive=True,
                )
            ],
            sliders=[{
                'active': 0,
                'yanchor': 'top',
                'xanchor': 'left',
                'currentvalue': {
                    'prefix': 'Epoch:',
                    'visible': True,
                    'xanchor': 'right',
                },
                'transition': {'duration': 300},
                'pad': {'b': 10},
                'len': 0.9,
                'x': 0.1,
                'y': -0.1,
                'steps': []  # Ensure steps is initialized as a list
            }]
        ),
        frames=frames
    )

    # Debug: Check the initial structure of the fig object
    # print("Initial fig layout:", fig.layout)

    # Create steps for the slider
    for idx, frame in enumerate(frames):
        step = {
            'label': frame.name,
            'method': 'animate',
            'args': [
                [frame.name],
                {
                    'mode': 'immediate',
                    'frame': {'duration': 300, 'redraw': True},
                    'transition': {'duration': 300},
                }
            ]
        }
        # Append each step to the slider's steps
        print(fig.layout.sliders)
        print(fig.layout.sliders[0])
        print(fig.layout.sliders[0]["steps"])
        if idx ==0 : 
            print(fig.layout.sliders[0]['steps']    )
            fig.layout.sliders[0]['steps'] = list()
            print(type(fig.layout.sliders[0]['steps']))
            fig.layout.sliders[0]['steps'].append(step)
        else :
            fig.layout.sliders[0]['steps'].append(step)

    # Debug: Check the structure after adding steps
    print("Final fig layout:", fig.layout)

    fig.show()


def main_epoch_loop():
    filename_path = "extended_final.csv"
    gdf = get_geodataframe(filename_path)
    shapefile_path = "AOI_Gambia 1/AOI_Gambia.shp"
    score_type = "temperature"
    output_path = "score_multiband.tif"
    score_columns = []
    grid_score_list = list()
    tranform_list = list()
    for column in gdf.columns:
        if score_type in column:
            grid_score, tranform = create_raster_from_df(gdf=gdf,score_column=column ,shapefile_path=shapefile_path,
                                        masked=0, resolution=0.001)
            grid_score_list.append(grid_score)
            tranform_list.append(tranform)
            score_columns.append(column)

    write_multiband_tif(output_path=output_path, grid_score_list=grid_score_list, transform_list=tranform_list)
    plot_tif_multiband(output_path, gdf, shapefile_path, score_type, score_columns)



    output_path = "score_raster_loop.tif"

if "__main__":
    main_epoch_loop()
    # filename_path = "extended_final.csv"
    # gdf = get_geodataframe(filename_path=filename_path)
    # plot_data(gdf, "Final_Score_2010_2029")


# Pour la suite il va falloir commenter tout ce qui a été fait ici
    