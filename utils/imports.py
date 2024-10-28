
import time
import os
import pandas as pd 
from datetime import datetime, date
import json
from shapely.geometry import Polygon, mapping
import shapely
import requests
import geopandas as gpd
import tempfile
import numpy as np
from pyproj import CRS
import base64
import matplotlib.pyplot as plt
from matplotlib import rcParams
import openmeteo_requests 
import time
import requests_cache
from retry_requests import retry
from tqdm import tqdm


