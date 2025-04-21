import os
import logging

# Create directories if they don't exist
def create_directories():
    """Create necessary directories for the application"""
    dirs = ["data", "logs"]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        logging.info(f"Created directory: {dir_path}")

# Initialize the application
create_directories() 