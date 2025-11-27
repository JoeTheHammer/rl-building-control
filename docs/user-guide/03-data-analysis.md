# Data Analysis

To access the frontend, start the application via Docker (refer to the README in the project root) and navigate to `http://localhost:5173/`. Select `Data Analysis` from the top navigation bar or click `Show Results` in the `Experiments` dashboard ([more information](02-running-experiments.md)).

## Data Analysis in GUI

Experiment data can be loaded by clicking `Load Data`. An overview of the results for each experiment in the suite will be displayed:

![alt text](images/data-analysis-1.png)

At the top of the card, experiment details are provided, such as the configuration `.yaml` files used and the total reward collected during evaluation.

Four options are available for each experiment:

- **Show Experiment Config**: Displays the experiment configuration.
- **Show Environment Config**: Displays the environment configuration.
- **Show Controller Config**: Displays the controller configuration.
- **Reproduce**: Creates a new experiment in the `Experiments` section with the exact same configuration and environment data (building model, weather data), facilitating experiment reproduction.

For each episode, general information including the creation timestamp, completion timestamp, and total reward is displayed. Below this, a data visualization interface is provided. Users can select which variable to visualize from three categories:
- **Reward**: Displays the reward for each timestep in the episode.
- **Actions**: Displays the action taken by each actuator at each timestep.
- **States**: Displays the measured value for each variable in the state space at each timestep.

Chart smoothing can be adjusted by modifying the averaging frequency. Options include every 5, 10, 20, 50, 100, 200, or 500 timesteps. Additionally, data can be presented as a line chart, bar chart, or table view.

The following screenshot demonstrates the same data presented as a bar chart with averaging every 200 timesteps.

![alt text](images/data-analysis-2.png)

The y-axis and x-axis ranges can be adjusted to investigate specific data sections in greater detail. The example below focuses on cooling setpoints between 25.3 and 25.94 degrees for timesteps between 7150 and 7250:
![alt text](images/data-analysis-3.png)

This data analysis tool is also available for data collected during the training process, provided this feature was enabled in the configuration file.

## CSV Export

Data can be exported to a `.csv` file by clicking `Export CSV` at the top of the screen. A dialog will appear allowing users to select which variables to include in the dataset:

![alt text](images/data-analysis-5.png)

## Download .h5

The underlying `.h5` file ([HDF5-based file](https://www.hdfgroup.org/solutions/hdf5/)) containing comprehensive experiment information can be exported. This file includes:

- **Context data**
    - All `.yaml` configuration files
    - The building model (`.epJSON`)
    - The weather data (`.ddy` and `.epw`) files
- **Evaluation data**
    - Actions taken by all actuators at each timestep
    - Reward for each timestep
    - Values for all variables configured in the environment state
- **Training data**
    - Actions taken by all actuators at each timestep
    - Reward for each timestep
    - Values for all variables configured in the environment state

By including context information, the `.h5` file serves as a "self-contained experiment data" package, containing both the results and the information necessary to reproduce them.
