<div style="text-align: center;">
    <h1>Gambia indicators</h1>
</div>


This repo allows you to request data on 

## Features

- Request Data on openmeteo
- Calculate scores for each variable
- Organize the score by periods
- Make raster from the score 

## Install
If you don't have any miniconda environnment yet you should follow the following instruction. Else you don't need to create any environnment, you only have to activate it, so start from the 2nd point of the Environnment part.
You should install miniconda to not have any problem with the installation as it will contain everything you need and well separate from anything else that could interfer. Interence between packages is the most annoying problem when making installation.

## Environment

If you don't have miniconda install it, and set it up correctly.

1. Create your conda environment with the YAML configuration provided
```
conda env create -n new_env_name --file environment.yml
```
2. Acivate it
```
conda activate new_env_name
```

If you are struggling to launch the code maybe you should try to reopen VSCode. It can solve numerous troubles


## Make all the requests
```
python .\data_request\request.py
```

## Create all the graph and score

```
python .\main.py
```

## Make a raster viz
```
python .\rasterization\raster_from_point.py    
```
Then you will have to give the name of the parameter you want to see and an integer 0 or 1 for the mask.
