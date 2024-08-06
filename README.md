# 70102-AKI_KILLERS

## Overview

This project involves a hospital system designed to predict Acute Kidney Injury (AKI) based on incoming messages, specifically handling HL7 messages and creatine test results. This README provides instructions on running the system, a brief overview of the main script (`hospital_system.py`), and mentions additional modules and useful methods.

## How to Run

Run simulator in one terminal:
1. `./simulator/simulator.py`

Build the Docker image: 

2. `docker build -t container_name`

Run the Docker container: 

3. `docker run` \
  `--env MLLP_ADDRESS=host.docker.internal:8440` \
  `--env PAGER_ADDRESS=host.docker.internal:8441` \
  `container_name`

## How to run unit tests

  `sh bash.sh`

## hospital_system.py

The main script, `hospital_system.py`, serves as the entry point for the system. It connects to the input socket and orchestrates the processing of incoming messages. The key functionalities include:

- Interaction with `hospital_communication.py`: This module handles the processing of HL7 messages.
- Interaction with `message_distributor.py`: Responsible for distinguishing between different message contents and directing them to the corresponding modules. Additionally, this module predicts AKI based on creatine test results.

## Additional Modules

1. **memory_database.py:** Handles in-memory database operations (RAM).

2. **disk_database.py:** Manages database operations stored on the hard disk drive (HDD).

## Useful Methods

1. **utils.py:** Contains utility methods for handling CSV and Pandas operations.

2. **config.py:** Stores configuration parameters, including port and socket numbers, model names, and other variables.

## General Directory Structure

1. **data/** :
Contains the data regarding patient history, as well as the true labels for system testing and development.

2. **model/** :
Contains the predictive model.

3. **simulator/** :
Contains the simulator of the hospital, test for it as well as the data needed to run the simulator.

4. **src/** :
Contains the source code to run the system.
