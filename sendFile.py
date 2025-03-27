import requests
import os
import logging

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def send_file(file_path):
    """
    Sends a single file from the Raspberry Pi to the laptop using HTTP.
    :param file_path: Full path of the file to send.
    """
    laptop_ip = 'http://192.168.24.1:5001/upload'  # Change to your laptop's IP address
    file_name = os.path.basename(file_path)

    # Check if the file exists
    if not os.path.exists(file_path):
        logger.error(f"File {file_path} does not exist.")
        return

    # Open the file and send it via HTTP POST
    try:
        with open(file_path, 'rb') as file:
            response = requests.post(laptop_ip, files={'file': (file_name, file)})
            if response.status_code == 200:
                logger.info(f"File {file_name} sent successfully!")
            else:
                logger.error(f"Failed to send file {file_name}. Response: {response.text}")
    except Exception as e:
        logger.error(f"Error sending file {file_name}: {str(e)}")

# Test with specific files
send_file("C:/Users/Sujan/Downloads/send_files/test.mp4")
send_file("C:/Users/Sujan/Downloads/send_files/test.json")
