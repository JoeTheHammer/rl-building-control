# Overview


Experiment configuration relies on `.yaml` files. To define an experiment, the following components are required:

-   **Controller config** (`.yaml`)
-   **Environment config** (`.yaml`)
-   **Experiment config** (`.yaml`)
-   **Building model** (`.epJSON`)
-   **Weather data** (`.epw` and `.ddy` files)

The building model and weather data must be provided by the user as external assets. The configuration files, however, can be either authored manually or generated automatically using the Frontend interface.

# Configuration with Frontend

To access the frontend, start the application via Docker (see README in project root) and access `http://localhost:5173/`. To create 

## Environment Configuration

In the menubar at the top, navigate to `Configurators` / `Environment` and you will see this screen:

![alt text](images/enviornment_configurator.png)

On the top, you have a bar with different options:

- Switch to Dev Mode: Opens the plain yaml file that you are updating under the hood. You can switch between Dev Mode and GUI mode without loosing your current progress, are changes are reflected in both views
- Open Configuration: Opens a dialog that allows you to previous created environment configuration
- Import Configuration: Allows you to import a configuration from any location of you system into the project.
- Save Configuration: Allows you to store the configuration in the system. 

### General

In the general tab, you can configure general environment properties:

- Building Model: Click on the button `Select Building Model` to select a building model. You select building models (`.epJSON` files) that have previously been placed in the folder `data/environment/buildings`. 
- Weather Data: Click on the button `Select Weather Data` to select weather data. You can select wather data that have previously been placed in the folder `data/environment/weather` in it's own folder. Every weather data folder must contain a `.ddy` and `epw` file.
- Start Date Episode: Selects the date on which each experiment episodes will start.
- End Date Episode: Selects the date on which each experiment episode will end.
- Timesteps per hour: Select how many timesteps per hour are simulated.

### State Space

In the state space tab, you can configure your state space. On the top, you can choose if you want to add time information and specify which information you want. Furthermore, you can choose if the time information should be cyclic. For information on cyclic time data can be found [here](https://towardsdatascience.com/how-to-handle-cyclical-data-in-machine-learning-3e0336f7f97c/).

In the `Variables` section, you can define the variables that are present in your state  space. They are mapped to a sinergym state space and have to be present as output variables in the `epJSON` energy plus building model file. More information can be found [here](https://ugr-sail.github.io/sinergym/compilation/main/pages/environments)

 You can specify
- Variable Name: The internal name used in the platform for this variable
- The type: `Variable` or `Meter`. If you choose `Meter`, the only thing that is needed in addition is the meter name. If you choose `Variable` you must also give the EnergyPlus Name and the Zone 
- EnergyPlus Name: The variable name in EnergyPlus. This variable has to be present to make the framework work.
- Zone: EnergyPlus Zone (or object) in which the variable is. This must map to the value `key_value` in output variables in the `epJSON` building model.
- Exclude from state space: It this is ticket, the value of this variable will not be forwarded to the agent as part of the state space. However, the value is measured and is present in the resulting dataset.

You can add and remove state space variable by clicking on the corresponding buttons:

![alt text](images/environment_configurator_1.png)

### Action space

For the action space, you can define actuators. They are mapped to a sinergym action space and have to be present as in the `epJSON` energy plus building model file. More information can be found [here](https://ugr-sail.github.io/sinergym/compilation/main/pages/environments)

You must specify:

- Actuator Name: The internal name used in the platform for this actuator
- Component: Energy plus component name
- Control Type: The Energy Plus control type
- Actuator Key: The Energy Plus key for this actuator
- Type: Here you can either choose `Continuous` or `Discrete`
    - For `Continuous`, you can choose Min and Max value. A value out of the continuous range [min, max] will then be applied at each timestep by the agent for this actuator. Values outside will be clipped to this range.
    - For `Discrete`, you can choose for the mode `Values` or `Ranges`. If you choose values, you can give a list of values from which the agent might choose it's action. If you choose `Range`, you can give a `Min` and `Max` values and a step size. So for example the values min = 20, max = 21, range = 0.2 will result in [20, 20.2, 20.4, 20.6, 20.8, 21]

Here is an example of an action space configuration:

![alt text](images/environment_configurator_2.png)

### Reward

In general, you have two different options how to configure a reward: Expression or code base. You can choose the type you want to use in the `Type` combobox

#### Expression reward

In the `Variables` section, you can give a list of state space variable names. These variables are then available in the `Expression` section and their value will be used by the reward function at each timestep.

In the `Parameter` section, you can define custom parameters. There value will be used by the reward function at each timestep.

Finally, you have to define a custom expression in the `Expression` section.

#### Expression reward

In the `Variables` section, you can list state space variable names. These variables are then available in the `Expression` section, and their values will be updated at each timestep for the reward calculation.

In the `Parameter` section, you can define custom parameters. Their values are constant and available to the reward function at each timestep.

Finally, you have to define a custom expression in the `Expression` section. This expression is a mathematical formula that calculates the reward using the variables and parameters you defined.

The expression uses **Python-like syntax** and is evaluated safely using the **[asteval](https://newville.github.io/asteval/)** library. You can use standard arithmetic operators (`+`, `-`, `*`, `/`, `**`) and parentheses.

Additionally, the following specific functions are available for use in your formula:

- **Standard Math**: `abs(x)`, `min(a, b)`, `max(a, b)`, `exp(x)`, `sqrt(x)`
- **Numpy Utilities**: `clip(value, min, max)`
- **Custom Logic**: `within(x, start, end)`
  - *Description*: Checks if `x` is between `start` and `end`.
  - *Wrap-around*: It handles wrap-around ranges automatically (e.g., `within(month, 11, 2)` returns True for Nov, Dec, Jan, Feb).

**Example:**
To penalize energy consumption while keeping temperature within comfortable bounds (20°C to 24°C):

```python
-1.0 * energy_consumption + (10.0 if within(zone_temp, 20, 24) else -10.0)
```

Example of an expression reward:

![alt text](images/environment_configurator_3.png)

#### Code-based reward

To overcome limitations of expression rewards, you can also use code based rewards. For this, you can give the python module name and the python class name of your reward class. More information about how to add such a customized reward can be found here [05-extending-the-system](05-extending-the-system.md)

## Controller configuration




## Experiment configuration
