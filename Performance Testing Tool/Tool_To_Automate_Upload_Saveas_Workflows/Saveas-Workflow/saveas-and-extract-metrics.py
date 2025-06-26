# Author- Sahana Telugunta, 
# Modified by Nilesh
# Description- Enable required commands, do save as for n iterations, and extract timings from log and store in a CSV file.
import os
import re
import csv
import adsk.core, adsk.fusion, adsk.cam, traceback
from datetime import datetime
import time
import platform

app = adsk.core.Application.get()
ui = app.userInterface

# Global variable used to maintain a reference to all event handlers.
handlers = []

# A list to store the files being processed
createdFileCollection = []

def enable_commands():
    try:
        # Get the app and ui.
        app = adsk.core.Application.get()
        ui = app.userInterface
        # Execute the required commands within Fusion 360.
        app.executeTextCommand('PIM.executeCommand "pimdm:provisionBucket" provider=WIP bucketAlias=wipLegacy bucketId=wip.dm.stg')
        app.executeTextCommand('FeatureFlag.ForceEnable fusion-pim-dual-home-save /On') # On the feature flag
        #app.executeTextCommand('FeatureFlag.ForceDisable fusion-pim-dual-home-save /On')#off the ff
        app.executeTextCommand('pimdm.documentMetaData /on')
        app.executeTextCommand('pim.enable /on')
        app.executeTextCommand('Analytics.Enable /on')
        app.executeTextCommand('Analytics.Applog /on')
        app.executeTextCommand('pim.log /debug *')
    except Exception as e:
        ui.messageBox(f"Failed to enable commands: {e}")
        return False

def saveAsFiles(datafoldername, iterations):
    folder_names = []  # List to store the names of created folders
    ui = None

    try:
        # Get the app and UI
        app = adsk.core.Application.get()
        ui = app.userInterface
        # Get the current design and data
        design = app.activeProduct
        data = app.data
        # Get the root folder of the current project
        project = data.activeProject
        root_folder = project.rootFolder

        # Look for the folder by name
        dataset_folder = root_folder.dataFolders.itemByName(datafoldername)

        if not dataset_folder:
            ui.messageBox(f"Folder '{datafoldername}' not found in the project.")
            return

        # Function to handle the save status synchronously
        def handle_save_status_synchronously(document):
            while not (document.isSaved) :
                adsk.doEvents()

            while not (document.dataFile.isComplete):
                adsk.doEvents()

            while document.isActive():
                adsk.doEvents()

        # Function to ensure all internal components are loaded
        def load_internal_components(document):
            fusion_document = adsk.fusion.FusionDocument.cast(document)
            design = fusion_document.design

            if design:
                occurrences = design.rootComponent.occurrences
                for occurrence in occurrences:
                    if occurrence.isValid:  # Check if the occurrence is valid
                        # Access the component to force it to load
                        occurrence.component  # This forces loading of the component

        # Function to save the file within Fusion 360
        def save_file_in_fusion(file, target_folder, iteration):
            try:
                # Open the document using the DataFile's open method
                document = app.documents.open(file)

                # Ensure the document is opened properly
                while not document or not document.isValid:
                    adsk.doEvents()

                # Load internal components if present
                load_internal_components(document)

                # Generate the timestamp
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                # Perform the "Save As" operation
                new_name = f"{file.name}_saved{iteration}_{timestamp}"
                document.saveAs(new_name, target_folder, '', '')

                handle_save_status_synchronously(document)

                # Close the document after saving
                while document.isActive():
                    adsk.doEvents()
                    
            except Exception as e:
                pass

        # Function to create folders recursively and save files
        def process_folder(source_folder, target_folder, iteration):
            for file in source_folder.dataFiles:
                document = app.documents.open(file)
                save_file_in_fusion(file,target_folder, iteration)  # Save each file synchronously
                time.sleep(2)
                document.close(False)
                i=0
                while i<=6:
                    adsk.doEvents()
                    i+=1

            for subfolder in source_folder.dataFolders:
                # Generate the timestamp
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                # Create the same subfolder in the target folder if it doesn't exist
                existing_folders = [f.name for f in target_folder.dataFolders]
                new_subfolder_name = f"{subfolder.name.split('_')[0]}_saved{iteration}_{timestamp}"
                if new_subfolder_name not in existing_folders:
                    new_target_folder = target_folder.dataFolders.add(new_subfolder_name)
                else:
                    new_target_folder = next(f for f in target_folder.dataFolders if f.name == new_subfolder_name)
                process_folder(subfolder, new_target_folder, iteration)  # Process subfolder recursively

        # Perform "Save As" operation for all uploaded files for the given number of iterations
        if dataset_folder:
            for i in range(1, iterations + 1):
                # Generate the timestamp
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                savednew_folder = root_folder.dataFolders.add(f'ITERATION{i}__{timestamp}')
                process_folder(dataset_folder, savednew_folder, i)  # Save files for this iteration
                folder_names.append(savednew_folder.name)

        return folder_names

    except Exception as e:
        if ui:
            ui.messageBox(f"Failed:\n{traceback.format_exc()}")
        return folder_names  # Return the list even if there is an exception


def get_lineage_urns(folder_name):
    global lineage_info
    try:
        # Get the app and ui
        app = adsk.core.Application.get()
        ui = app.userInterface
        data = app.data

        # Get the root folder of the current project opened
        project = data.activeProject
        root_folder = project.rootFolder

        # Find the specified folder
        target_folder = root_folder.dataFolders.itemByName(folder_name)
        if not target_folder:
            ui.messageBox(f"Folder '{folder_name}' not found.")
            return

        # Function to process files and subfolders
        def process_folder(folder):
            for file in folder.dataFiles:
                lineage_info.append((file.name, file.id))  # Collect file name and id
            for subfolder in folder.dataFolders:
                process_folder(subfolder)

        # Process the target folder
        process_folder(target_folder)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def extract_log_data(log_file_path, csv_file_path, lineage_urns):
    try:
        # Get the app and ui
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Open log file
        with open(log_file_path, 'r', encoding='utf-8') as log_file:
            log_lines = log_file.readlines()

        # Create a dictionary to map lineage URNs to file names
        lineage_dict = {urn: name for name, urn in lineage_urns}

        # Check for any SaveDoc fail statuses for the lineage URNs
        save_fail_pattern = re.compile(r'"component_name":\s*"SaveDoc fail"')
        lineage_uri_pattern = re.compile(r'"lineageUri":\s*"([^"]+)"')
        for line in log_lines:
            if save_fail_pattern.search(line):
                lineage_match = lineage_uri_pattern.search(line)
                if lineage_match and lineage_match.group(1) in lineage_dict:
                    ui.messageBox(f"SaveDoc failure found for lineage URI: {lineage_match.group(1)}. Not extracting.")
                    return

        # Initialize variables
        save_success = False
        lineage_uri = ""
        wip_all_time = ""
        wip_time = ""
        pim_total_time = ""
        data_to_write = []

        # Regex patterns
        save_success_pattern = re.compile(r'"component_name":\s*"SaveDoc success"')
        wip_all_time_pattern = re.compile(r'"wipAllTime":\s*"([^"]+)"')
        wip_time_pattern = re.compile(r'"wipTime":\s*"([^"]+)"')
        pim_total_time_pattern = re.compile(r'"PIMTotalTime":\s*"([^"]+)"')

        for line in log_lines:
            lineage_match = lineage_uri_pattern.search(line)
            if lineage_match:
                lineage_uri = lineage_match.group(1)

            wip_all_time_match = wip_all_time_pattern.search(line)
            if wip_all_time_match:
                wip_all_time = wip_all_time_match.group(1)

            wip_time_match = wip_time_pattern.search(line)
            if wip_time_match:
                wip_time = wip_time_match.group(1)

            pim_total_time_match = pim_total_time_pattern.search(line)
            if pim_total_time_match:
                pim_total_time = pim_total_time_match.group(1)

            if save_success_pattern.search(line):
                save_success = True

            # Check if all required data is collected and save success is true
            if save_success and lineage_uri and wip_all_time and wip_time and pim_total_time:
                # Find the corresponding file name for the lineage URI
                file_name = lineage_dict.get(lineage_uri, "Unknown")
                if file_name != "Unknown": 
                    data_to_write.append([file_name, lineage_uri, wip_all_time, wip_time, pim_total_time])
                # Reset variables for the next entry
                save_success = False
                lineage_uri = ""
                wip_all_time = ""
                wip_time = ""
                pim_total_time = ""

        # Write to CSV
        with open(csv_file_path, 'a', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['File Name', 'Lineage URN', 'WIP All Time', 'WIP Time', 'PIM Total Time'])
            csv_writer.writerows(data_to_write)

        ui.messageBox(f"Data extracted and written to CSV successfully at {csv_file_path}.")

    except Exception as e:
        ui.messageBox(f"Failed to extract log data: {e}")
        raise

def monitor_log_file_size(log_file_path, duration=8):
    """Monitors the log file size every seconds and triggers data extraction when the size remains unchanged."""
    previous_size = os.path.getsize(log_file_path)
    while True:
        for i in range(0,duration):
            adsk.doEvents()
        current_size = os.path.getsize(log_file_path)

        if current_size == previous_size:
            # If the size remains unchanged, proceed with data extraction
            extract_log_data(log_file_path, csv_file_path, lineage_info)
            break  # Exit the loop after extraction

        previous_size = current_size  # Update the previous size for the next check

#Main execution
datafoldername = ui.inputBox('Enter the folder name to save as:', 'Folder Name', '')

# If datafoldername is coming from user input, ensure it is sanitized
if isinstance(datafoldername, list):
    datafoldername = datafoldername[0]  # Extract the string from the list if needed
datafoldername = datafoldername.strip()  # Trim any leading/trailing whitespace

# Ensure that datafoldername is valid
if not datafoldername:
    ui.messageBox("Invalid folder name: The folder name is empty.")
    adsk.terminate()

# Get the number of iterations from the user
input_result = ui.inputBox('Enter the number of iterations:', 'Iterations', '1')
iterations = int(input_result[0]) if isinstance(input_result, list) else int(input_result)

lineage_info = []

status=enable_commands()
if status == False:
    ui.messageBox("commands not executed so ending execution")
    adsk.autoTerminate(True)
    exit()
adsk.autoTerminate(False)
iteration_folders = saveAsFiles(datafoldername, iterations)
# time.sleep(10)

# Run the get_lineage_urns function for all iteration folder names
for folder in iteration_folders:
    get_lineage_urns(folder)
    time.sleep(10)

latest_log_file=app.applicationFolders.appLogFilePath
# Define the CSV file path
csv_file_name = 'results.csv'
log_directory=os.path.dirname(latest_log_file)

# Generate an incremental CSV file name
base_csv_file_name = os.path.splitext(csv_file_name)[0]
csv_counter = 1
while os.path.exists(os.path.join(log_directory, f"{base_csv_file_name}{csv_counter}.csv")):
    csv_counter += 1
csv_file_path = os.path.join(log_directory, f"{base_csv_file_name}{csv_counter}.csv")

# Run the extract_log_data function
#to wait sometime
i=0
while i<=10:
    adsk.doEvents()
    i+=1

monitor_log_file_size(latest_log_file)
adsk.terminate()