import os
import shutil
import logging
import mimetypes
import hashlib
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from cryptography.fernet import Fernet

from docx import Document
import zipfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def move_file(source_path, target_path):
    """Move a file or folder to a new location."""
    try:
        shutil.move(source_path, target_path)
        logging.info(f"Moved {source_path} to {target_path}")
        log_operation('move', {'source': source_path, 'target': target_path})
    except Exception as e:
        logging.error(f"Error moving {source_path} to {target_path}: {e}")
        logging.error(f"Source path: {source_path}, Target path: {target_path}")
        logging.error(f"Exception details: {e}")

def copy_file(source_path, target_path):
    """Copy a file or folder to a new location."""
    try:
        if os.path.isdir(source_path):
            if not os.path.exists(target_path):
                shutil.copytree(source_path, target_path)
            else:
                for item in os.listdir(source_path):
                    s = os.path.join(source_path, item)
                    d = os.path.join(target_path, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)
        else:
            shutil.copy2(source_path, target_path)
        logging.info(f"Copied {source_path} to {target_path}")
        log_operation('copy', {'source': source_path, 'target': target_path})
    except Exception as e:
        logging.error(f"Error copying {source_path} to {target_path}: {e}")

def delete_file(path):
    """Delete a specified file or folder."""
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        logging.info(f"Deleted {path}")
        log_operation('delete', {'path': path})
    except Exception as e:
        logging.error(f"Error deleting {path}: {e}")

def summarize_file(file_path):
    """Generate an AI-based summary of a text file."""
    if not os.path.isfile(file_path):
        logging.error(f"Error summarizing file {file_path}: Not a file.")
        return None

    try:
        with open(file_path, 'r') as file:
            content = file.read()
            # Placeholder for AI-based summarization logic
            summary = content[:100]  # Example: take the first 100 characters as a summary
            logging.info(f"Summary for {file_path}: {summary}")
            return summary
    except Exception as e:
        logging.error(f"Error summarizing file {file_path}: {e}")
        return None

def display_log():
    """Display a log of previous operations."""
    try:
        with open('operations.log', 'r') as log_file:
            log_content = log_file.read()
            print(log_content)
            logging.info("Displayed log content.")
    except Exception as e:
        logging.error(f"Error displaying log: {e}")

def categorize_file(file_name, categories):
    """Categorize a file based on its extension."""
    _, ext = os.path.splitext(file_name)
    ext = ext.lower()
    for category, extensions in categories.items():
        if ext in extensions:
            return category
    return "Others"

def organize_files(source_dir, target_dir, model):
    """Organize files in the source directory using the provided model."""
    if not os.path.exists(source_dir):
        logging.error(f"Source directory {source_dir} does not exist.")
        return

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    for file_name in os.listdir(source_dir):
        file_path = os.path.join(source_dir, file_name)
        if os.path.isfile(file_path):
            file_metadata = {
                'name': file_name,
                'size': os.path.getsize(file_path),
                'type': mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            }
            category = model.predict_category(file_metadata)
            target_folder = os.path.join(target_dir, category)
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            move_file(file_path, os.path.join(target_folder, file_name))
    logging.info("File organization completed.")

def hash_file(file_path):
    """Generate a hash for the given file."""
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return None
    file_hash = hasher.hexdigest()
    logging.info(f"Hash for file {file_path}: {file_hash}")
    return file_hash

def find_duplicates(directory):
    """Detect and list duplicate files in the specified directory."""
    if not os.path.exists(directory):
        logging.error(f"Directory {directory} does not exist.")
        return

    file_hashes = {}
    duplicates = []

    for root, _, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_hash = hash_file(file_path)
            if file_hash:
                if file_hash in file_hashes:
                    duplicates.append((file_path, file_hashes[file_hash]))
                else:
                    file_hashes[file_hash] = file_path

    if duplicates:
        logging.info("Duplicate files found:")
        for dup in duplicates:
            logging.info(f"Duplicate: {dup[0]} and {dup[1]}")
    else:
        logging.info("No duplicate files found.")

def rename_files(directory):
    """Rename files intelligently based on content/type."""
    if not os.path.exists(directory):
        logging.error(f"Directory {directory} does not exist.")
        return

    for root, _, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                print(f"Current file: {file_path}")
                new_file_name = input(f"Enter new name for {file_name} (leave blank to skip): ").strip()
                if new_file_name:
                    new_file_path = os.path.join(root, new_file_name)
                    try:
                        os.rename(file_path, new_file_path)
                        logging.info(f"Renamed file {file_path} to {new_file_path}")
                    except Exception as e:
                        logging.error(f"Error renaming file {file_path} to {new_file_path}: {e}")
                else:
                    logging.info(f"Skipped renaming file {file_path}")
            else:
                logging.warning(f"Could not determine MIME type for file {file_path}")

def search_files(directory, keyword):
    """Find files using AI-powered semantic search."""
    if not os.path.exists(directory):
        logging.error(f"Directory {directory} does not exist.")
        return

    matching_files = []

    for root, _, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if keyword.lower() in file_name.lower():
                matching_files.append(file_path)
            else:
                try:
                    with open(file_path, 'r', errors='ignore') as file:
                        content = file.read()
                        if keyword.lower() in content.lower():
                            matching_files.append(file_path)
                except Exception as e:
                    logging.error(f"Error reading file {file_path}: {e}")

    if matching_files:
        logging.info("Matching files found:")
        for file in matching_files:
            logging.info(file)
    else:
        logging.info("No matching files found.")

def log_operation(operation, details):
    """Log an operation to the operations log."""
    log_entry = {
        'operation': operation,
        'details': details
    }
    with open('operations.log', 'a') as log_file:
        log_file.write(json.dumps(log_entry) + '\n')

class DirectoryEventHandler(FileSystemEventHandler):
    def __init__(self, model, target_directory):
        self.model = model
        self.target_directory = target_directory

    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            logging.info(f"New file detected: {file_path}")
            self.organize_file(file_path)

    def organize_file(self, file_path):
        file_name = os.path.basename(file_path)
        file_metadata = {
            'name': file_name,
            'size': os.path.getsize(file_path),
            'type': mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        }
        category = self.model.predict_category(file_metadata)
        target_folder = os.path.join(self.target_directory, category)
        if not os.path.exists(target_folder):
            try:
                os.makedirs(target_folder)
                logging.info(f"Created directory: {target_folder}")
            except Exception as e:
                logging.error(f"Error creating directory {target_folder}: {e}")
                return
        else:
            logging.info(f"Directory already exists: {target_folder}")
        try:
            move_file(file_path, os.path.join(target_folder, file_name))
        except Exception as e:
            logging.error(f"Error moving file {file_path} to {target_folder}: {e}")

def monitor_directory(source_directory, target_directory, model):
    """Watch the directory and organize new files in real time."""
    event_handler = DirectoryEventHandler(model, target_directory)
    observer = Observer()
    observer.schedule(event_handler, path=source_directory, recursive=False)
    observer.start()
    logging.info("Monitoring directory...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def sort_files_by_date(source_directory, target_directory):
    """Organize files based on creation/modification date."""
    if not os.path.exists(source_directory):
        logging.error(f"Source directory {source_directory} does not exist.")
        return

    if not os.path.exists(target_directory):
        os.makedirs(target_directory)

    for file_name in os.listdir(source_directory):
        file_path = os.path.join(source_directory, file_name)
        if os.path.isfile(file_path):
            # Get the file's modification time
            mod_time = os.path.getmtime(file_path)
            mod_time_struct = time.localtime(mod_time)
            year = mod_time_struct.tm_year
            month = mod_time_struct.tm_mon
            day = mod_time_struct.tm_mday

            # Create target subdirectory based on the modification date
            target_subdir = os.path.join(target_directory, f"{year}-{month:02d}-{day:02d}")
            if not os.path.exists(target_subdir):
                os.makedirs(target_subdir)

            # Move the file to the target subdirectory
            target_path = os.path.join(target_subdir, file_name)
            try:
                shutil.move(file_path, target_path)
                logging.info(f"Moved {file_path} to {target_path}")
            except Exception as e:
                logging.error(f"Error moving {file_path} to {target_path}: {e}")

    logging.info("File sorting by date completed.")

def generate_key():
    """Generate a key for encryption."""
    key = Fernet.generate_key()
    with open('encryption.key', 'wb') as key_file:
        key_file.write(key)
    return key

def load_key():
    """Load the encryption key from a file."""
    return open('encryption.key', 'rb').read()

def encrypt_file(file_path):
    """Encrypt a file for security."""
    try:
        # Generate or load the encryption key
        if not os.path.exists('encryption.key'):
            key = generate_key()
        else:
            key = load_key()

        fernet = Fernet(key)

        # Read the file data
        with open(file_path, 'rb') as file:
            file_data = file.read()

        # Encrypt the file data
        encrypted_data = fernet.encrypt(file_data)

        # Write the encrypted data back to the file
        with open(file_path, 'wb') as file:
            file.write(encrypted_data)

        logging.info(f"Encrypted file: {file_path}")
        log_operation('encrypt', {'file': file_path})
    except Exception as e:
        logging.error(f"Error encrypting file {file_path}: {e}")

def decrypt_file(file_path):
    """Decrypt a file."""
    try:
        if not os.path.exists('encryption.key'):
            logging.error("Encryption key not found.")
            return
        key = load_key()
        fernet = Fernet(key)

        with open(file_path, 'rb') as file:
            encrypted_data = file.read()

        decrypted_data = fernet.decrypt(encrypted_data)

        with open(file_path, 'wb') as file:
            file.write(decrypted_data)

        logging.info(f"Decrypted file: {file_path}")
        log_operation('decrypt', {'file': file_path})
    except Exception as e:
        logging.error(f"Error decrypting file {file_path}: {e}")

def create_directory(path, name):
    """Create a new directory."""
    try:
        full_path = os.path.join(path, name)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            logging.info(f"Created directory: {full_path}")
            log_operation('create_directory', {'path': full_path})
        else:
            logging.warning(f"Directory already exists: {full_path}")
    except Exception as e:
        logging.error(f"Error creating directory {full_path}: {e}")

def delete_directory(path, name):
    """Delete a specified directory."""
    try:
        full_path = os.path.join(path, name)
        if os.path.exists(full_path) and os.path.isdir(full_path):
            shutil.rmtree(full_path)
            logging.info(f"Deleted directory: {full_path}")
            log_operation('delete_directory', {'path': full_path})
        else:
            logging.warning(f"Directory does not exist: {full_path}")
    except Exception as e:
        logging.error(f"Error deleting directory {full_path}: {e}")

def list_files_in_directory(path):
    """List files in a specified directory."""
    try:
        if os.path.exists(path) and os.path.isdir(path):
            files = os.listdir(path)
            logging.info(f"Files in directory {path}: {files}")
            return files
        else:
            logging.warning(f"Directory does not exist: {path}")
            return []
    except Exception as e:
        logging.error(f"Error listing files in directory {path}: {e}")
        return []

def rename_directory(current_path, current_name, new_name):
    """Rename a specified directory."""
    try:
        full_current_path = os.path.join(current_path, current_name)
        full_new_path = os.path.join(current_path, new_name)
        if os.path.exists(full_current_path) and os.path.isdir(full_current_path):
            os.rename(full_current_path, full_new_path)
            logging.info(f"Renamed directory from {full_current_path} to {full_new_path}")
            log_operation('rename_directory', {'from': full_current_path, 'to': full_new_path})
        else:
            logging.warning(f"Directory does not exist: {full_current_path}")
    except Exception as e:
        logging.error(f"Error renaming directory from {full_current_path} to {full_new_path}: {e}")

def create_text_file(path, name, content=""):
    """Create a new text file with optional content."""
    try:
        full_path = os.path.join(path, f"{name}.txt")
        with open(full_path, 'w') as file:
            file.write(content)
        logging.info(f"Created text file: {full_path}")
        log_operation('create_text_file', {'path': full_path, 'content': content})
    except Exception as e:
        logging.error(f"Error creating text file {full_path}: {e}")

def create_video_file(path, name):
    """Create a placeholder video file."""
    try:
        full_path = os.path.join(path, f"{name}.mp4")
        with open(full_path, 'wb') as file:
            # Write a placeholder header for an MP4 file
            file.write(b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom')
        logging.info(f"Created video file: {full_path}")
        log_operation('create_video_file', {'path': full_path})
    except Exception as e:
        logging.error(f"Error creating video file {full_path}: {e}")

def create_word_file(path, name, content=""):
    """Create a new MS Word document with optional content."""
    try:
        full_path = os.path.join(path, f"{name}.docx")
        document = Document()
        document.add_paragraph(content)
        document.save(full_path)
        logging.info(f"Created Word document: {full_path}")
        log_operation('create_word_file', {'path': full_path, 'content': content})
    except Exception as e:
        logging.error(f"Error creating Word document {full_path}: {e}")

def compress_directory(path, output_name):
    """Compress a directory into a zip file."""
    try:
        with zipfile.ZipFile(f"{output_name}.zip", 'w') as zipf:
            for root, dirs, files in os.walk(path):
                for file in files:
                    zipf.write(os.path.join(root, file),
                               os.path.relpath(os.path.join(root, file), path))
        logging.info(f"Compressed directory {path} into {output_name}.zip")
        log_operation('compress_directory', {'path': path, 'output': f"{output_name}.zip"})
    except Exception as e:
        logging.error(f"Error compressing directory {path}: {e}")

def decompress_file(zip_path, extract_to):
    """Decompress a zip file into a directory."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(extract_to)
        logging.info(f"Decompressed {zip_path} into {extract_to}")
        log_operation('decompress_file', {'zip_path': zip_path, 'extract_to': extract_to})
    except Exception as e:
        logging.error(f"Error decompressing file {zip_path}: {e}")

def view_file_metadata(file_path):
    """View metadata of a file."""
    try:
        if os.path.exists(file_path):
            metadata = {
                "Size": os.path.getsize(file_path),
                "Created": time.ctime(os.path.getctime(file_path)),
                "Modified": time.ctime(os.path.getmtime(file_path)),
                "Type": mimetypes.guess_type(file_path)[0]
            }
            logging.info(f"Metadata for {file_path}: {metadata}")
            return metadata
        else:
            logging.warning(f"File does not exist: {file_path}")
            return None
    except Exception as e:
        logging.error(f"Error retrieving metadata for {file_path}: {e}")
        return None

def preview_file(file_path, lines=10):
    """Preview the first few lines of a text file."""
    try:
        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                content = ''.join([file.readline() for _ in range(lines)])
            logging.info(f"Preview of {file_path}:\n{content}")
            return content
        else:
            logging.warning(f"File does not exist or is not a text file: {file_path}")
            return None
    except Exception as e:
        logging.error(f"Error previewing file {file_path}: {e}")
        return None
