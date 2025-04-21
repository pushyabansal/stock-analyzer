import sys
import os
import logging
from datetime import datetime

def setup_logging():
    """Set up logging configuration"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"data_acquisition_{timestamp}.log")
    
    # Configure root logger with a more aggressive configuration
    # This ensures all loggers (even from imported modules) will log to this file
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers to avoid duplicate logging
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add a file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(file_handler)
    
    # Add a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(console_handler)
    
    # Return the log file path for reference
    return log_file

# Setup logging before importing other modules
log_file = setup_logging()

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Now import modules that use logging
from app.services.data_acquisition import acquire_data

def main():
    """Main function to run the data acquisition job"""
    logger = logging.getLogger(__name__)
    
    logger.info("Starting data acquisition job")
    logger.info(f"Logging to file: {log_file}")
    
    # Get the number of days to fetch data for
    days = int(os.getenv("DATA_ACQUISITION_DAYS", "30"))
    
    try:
        success = acquire_data(days=days)
        if success:
            logger.info("Data acquisition job completed successfully")
        else:
            logger.error("Data acquisition job failed")
    except Exception as e:
        logger.exception(f"Error running data acquisition job: {e}")
    
    logger.info("Data acquisition job finished")

if __name__ == "__main__":
    main() 