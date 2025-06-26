#Author: SAHANA TELUGUNTA
#Description :uploads the f3d or f3z files from local system.

import os
import re
import adsk.core, adsk.fusion, adsk.cam, traceback
from datetime import datetime

app = adsk.core.Application.get()
ui = app.userInterface

def upload_files_to_fusion(folder_name, source_path):
    try:
        # Get the current design and data
        design = app.activeProduct
        data = app.data
        
        # Get the root folder of the current project
        project = data.activeProject
        root_folder = project.rootFolder

        # Generate the timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        folder_name = f'{folder_name}__{timestamp}'
        dataset_folder = root_folder.dataFolders.add(folder_name)

        # Function to sanitize folder names
        def sanitize_folder_name(name):
            return re.sub(r'[<>:"/\\|?*.]', '_', name)

        # Function to create folders recursively
        def create_folders_recursively(current_folder, relative_path):
            parts = relative_path.split(os.sep)
            for part in parts:
                if part in ['.', '..']:
                    continue
                sanitized_part = sanitize_folder_name(part)
                try:
                    existing_folders = [f.name for f in current_folder.dataFolders]
                    if f"{sanitized_part}__{timestamp}" not in existing_folders:
                        current_folder = current_folder.dataFolders.add(f"{sanitized_part}__{timestamp}")
                    else:
                        current_folder = next(f for f in current_folder.dataFolders if f.name == f"{sanitized_part}__{timestamp}")
                except RuntimeError as e:
                    ui.messageBox(f"Failed to create folder '{sanitized_part}': {e}")
                    continue
            return current_folder

        total_files = 0  # Initialize total_files

        for root, dirs, files in os.walk(source_path):
            total_files += len(files)
            relative_path = os.path.relpath(root, source_path)
            current_folder = create_folders_recursively(dataset_folder, relative_path)
            for filename in files:
                file_path = os.path.join(root, filename)
                if os.path.isfile(file_path):
                    current_folder.uploadFile(file_path)
                    #ui.messageBox(f"Uploading {filename}...")  # msg for each file
        if total_files==0:
            ui.messageBox(f"no files are present for upload.ending execution.")
            return
        ui.messageBox(f"Upload initiated for {total_files} files.please wait till upload progress complete.")
        return folder_name

    except Exception as e:
        if ui:
            ui.messageBox(f'Failed:\n{traceback.format_exc()}')

# Main Execution
source_path = ui.inputBox('Enter the source path:', 'Source Path', '')
if isinstance(source_path, list):
    source_path = source_path[0]

folder_name = os.path.basename(os.path.normpath(source_path))
uploaded_folder_name = upload_files_to_fusion(folder_name, source_path)
