# Experiment execution using GUI

To access the frontend, start the application via Docker (see README in project root) and access `http://localhost:5173/`. Navigate on the top bar to `Experiments`:

![alt text](images/execution_1.png)

On the page, there are three sections:
- New Experiment Suites: Shows experiment suites, that have been scheduled but are not executed yet.
- Running Experiment Suites: Shows experiment suites that are currently running.
- Completed Experiment Suites: Show experiments that have completed (finished or aborted).

## Scheduling an experiment suite

You can schedule a new experiment by clicking on `Schedule Experiment Suite`. A popup dialog opens that shows all stored experiment suites. Experiment suites can be created as described [here](01-experiment-configuration.md).

Once you have scheduled a experiment suite, you can see additional details (by clicking on `Show details`) of the individual experiments used in this experiment suite including their `.yaml` configuration files. When investigating `.yaml` files, you can use the corresponding buttons on the bottom to navigate to the corresponding configurator page and change them:

![alt text](images/execution_2.png)

You can start the experiment suite by clicking on `Run`.

## Running an experiment

Once the experiment is started by using the `Run` button, an overview appears showing the current status:

![alt text](images/execution_3.png)

When clicking on `Show details`, additional information is shown:

![alt text](images/execution_4.png)

For each experiment, you see detailed information like the configuration files, their status and the live logs of the current execution. `Open Tensorboard` will open the corresponding [tensorboard](https://www.tensorflow.org/tensorboard) and you can view live training metrics:

![alt text](images/tensorboard.png)

Once a tensorboard is opened, you can stop the tensorboard execution by clicking on `Stop Tensorboard`. 

You can stop the experiment suite execution by clicking on `Stop Experiment Suite`. 

## Completed an experiments

Once a experiment has completed it will appear in the Completed Experiment Suites section. 

![alt text](images/execution_5.png)

You can now archive the experiment, such that it is not on your dashboard anymore (but still accessible in the section `Archive`.) The tensorboard logs are still available and can be viewed in [tensorboard](https://www.tensorflow.org/tensorboard). `Show results` open the `Data Analysis` page with the corresponding results, which is described in more detail [here](03-data-analysis.md).

After clicking on `Show Details` you see option see options to open the individual `.yaml` configuration files or the logs.

# Configuration execution without

You can execute the experiment suite by using the testbed as described [here](../../testbed/README.md).