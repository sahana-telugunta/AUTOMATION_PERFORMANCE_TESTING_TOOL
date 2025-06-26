# Automation Tool for Dual Home Performance Testing

## Overview
Designed to improve Fusion's performance testing efficiency by simplifying  the process by automating the Upload and Save-As workflows , ensuring faster and more reliable testing outcomes

## Key Features
**1. Upload Workflow:**
* Uploads files to Fusion and organizes them in timestamped folders.
* Automatically saves the workflow after upload.

**2. Save-As Workflow:**
* Supports multiple iterations: Specify the number of iterations for the test.
* For each iteration, the tool creates a folder with a timestamp (iteration_n).
* Captures lineage URNs from iteration folders.
* Matches lineage URNs in logs and collects the following performance metrics:
    - WIP All Time
    - WIP Time
    - PIM Total Time
* Dumps the collected data into a CSV file stored in the local log path for analysis.

## Prerequisites
**Fusion:** This tool is designed to work with Fusion’s Dev or Staging Streamer.

## Installation and Setup
**1.Clone the Repository:**
Clone this repository to your local machine using the following command:
```bash
git clone <repository-url>
```
**2.Configure Fusion:**
* Open Fusion Dev or Staging Streamer.
* In the top menu, navigate to Utilities → Add-ins → Scripts and Add-ins.
* Add Scripts:
    - Click the plus (+) icon next to My Scripts in the dialog box.
    - Select the folder containing the **saveas-and-extract-metrics script** from the cloned repository and click Select.
    - Repeat the process to add the **upload-dataset** script folder and click Select.
* Run the Scripts:
    - From the Add-ins menu, you can now select the script (either Upload or Save-As) you wish to run.
    - Click Run to execute the selected script.


## How to Use
#### Upload Workflow:

* Choose the Upload script from the Add-ins menu.
* Run the script to upload files to Fusion. The script will automatically create a timestamped folder for the uploaded files.

#### Save-As Workflow:

* Choose the Save-As script from the Add-ins menu.
* Specify the number of iterations for the test.
* The script will create timestamped iteration folders, capture performance metrics, and store the results in a CSV file and displays the path where it dumped the results.

### Performance Metrics Captured
* The Save-As workflow captures the following metrics and saves them to a CSV file:
    - **WIP All Time:** Total time the WIP (Work In Progress) was active.
    - **WIP Time:** Time spent on Work In Progress during the iteration.
    - **PIM Total Time:** Total time spent on PIM (Product Information Management) tasks during the iteration.
    These metrics are logged for each iteration and can be used for detailed performance analysis.

## Documentation
For detailed guidance and more in-depth information about using the tool, refer to the [Dual Home Save Performance Metrics](https://wiki.autodesk.com/display/MFG/Dual+Home+Save+performance+metrics) Wiki.

## Contribution
This tool includes contributions from **Sahana Telugunta**.

We welcome contributions to this repository. If you have suggestions or improvements, please create an issue or submit a pull request.
