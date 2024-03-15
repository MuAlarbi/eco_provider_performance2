import os
import requests
import time
import subprocess
import re
import platform
import numpy as np
import json
import aiohttp
import asyncio
import configparser



def read_config(config_file='config.ini'):
    """
    Read configuration from a config file.

    :param config_file: Path to the configuration file
    :return: A dictionary with configuration values
    """
    config = configparser.ConfigParser()
    config.read(config_file)
    
    # Assuming all your configurations are under 'NetworkSettings'
    network_settings = config['NetworkSettings']
    
    return {
        'func1_host': network_settings.get('func1_host'),
        'func2_host': network_settings.get('func2_host'),
        'func3_host': network_settings.get('func3_host'),
        'expr_code': network_settings.get('expr_code'),
        'deployment_config': network_settings.get('deployment_config'),
        'country_code': network_settings.get('country_code'),
        'source_city': network_settings.get('source_city'),
        'telco_provider': network_settings.get('telco_provider'),
        'collection_name': network_settings.get('collection_name')
    }


def create_text_file(size_in_mb, file_name="dumpfile.txt"):
    """
    Create a text file of a specified size in megabytes.

    :param size_in_mb: Size of the text file in megabytes
    :param file_name: Name of the text file (default is 'dumpfile.txt')
    """
    try:
        # Calculate the total number of characters (assuming 1 char = 1 byte)
        total_chars = size_in_mb * 1024 * 1024

        # Write spaces (or any other character) to the file
        with open(file_name, 'w') as file:
            for _ in range(total_chars):
                file.write('X')  # Writing a single space character

        print(f"Text file '{file_name}' of {size_in_mb}MB created successfully.")
    except IOError as e:
        print(f"An error occurred: {e}")


def calculate_transmission_rate(file_size_bytes, upload_latency_ms):
    """
Calculate the transmission rate in megabits per second (Mbps) based on the file size and upload latency.

Parameters:
- file_size_bytes (int): The size of the file in bytes.
- upload_latency_ms (float): The upload latency in milliseconds.

Returns:
- transmission_rate_mbps (float): The transmission rate in Mbps.

Example:
transmission_rate = calculate_transmission_rate(1000000, 50)
print(transmission_rate)  # 160.0

Note:
- The file size is converted to bits before calculating the transmission rate.
- The upload latency is converted to seconds before calculating the transmission rate.
- The transmission rate is calculated by dividing the file size in bits by the upload latency in seconds.
- The result is then converted to Mbps by dividing by 1e6 (1 million).
"""
    # Convert file size to bits
    file_size_bits = file_size_bytes * 8

    # Convert latency to seconds
    upload_latency_s = upload_latency_ms / 1000

    # Calculate transmission rate in bits per second
    transmission_rate_bps = file_size_bits / upload_latency_s

    # Convert transmission rate to megabits per second
    transmission_rate_mbps = transmission_rate_bps / 1e6

    return transmission_rate_mbps


def get_latency_and_packet_loss(server_url, number_of_requests):
    """
This function calculates the latency statistics and packet loss for a given server URL using the ping command.

Parameters:
- server_url (str): The URL of the server to ping.
- number_of_requests (int): The number of ping requests to send.

Returns:
- latency_statistics (list): A list of latency statistics in milliseconds, including minimum, average, and maximum latency.
- packet_loss (float): The packet loss percentage as a decimal value.
- number_of_hops (list): A list of the number of hops taken by each ping request.

Example Usage:
latency_stats, loss, hops = get_latency_and_packet_loss("www.example.com", 10)
print(latency_stats)  # [10.0, 15.0, 20.0]
print(loss)  # 0.1
print(hops)  # [5, 4, 3]

Note:
- This function uses the ping command available in the operating system to measure latency and packet loss.
- The function works on both Windows and Unix-like systems.
- The default TTL value used for calculating the number of hops is 64.
"""
    param = '-n' if platform.system().lower()=='windows' else '-c'
    ping_result = subprocess.Popen(['ping', param, str(number_of_requests), server_url], stderr=subprocess.STDOUT,
                                   stdout=subprocess.PIPE).communicate()
    latency_statitcs = ping_result[0].decode('utf-8').split("\n")[-2].split(" = ")[-1].replace(" ms", "").split("/")
    packet_loss = int(re.findall("\d+%", ping_result[0].decode('utf-8'))[0].replace("%", "")) / 100

    # find os default TTL using the following commmnads 
    # MAC_OS sysctl net.inet.ip.ttl
    # LINUX sysctl net.ipv4.ip_default_ttl
    defualtTTL = 64
    numberOfHops = []
    lines = ping_result[0].decode('utf-8').split("\n")
    for lineIdx in range(1,len(lines)-5):
        lineTokens = lines[lineIdx].split(" ")
        if len(lineTokens) == 8:
            ttl = lineTokens[5].split("=")[1]
            print("****** defaultTTL: ", defualtTTL, " ttl: ", ttl, " ******")
            numberOfHops.append(defualtTTL - int(ttl))
        else:
            print("found ping request timed out")
    return latency_statitcs, packet_loss, numberOfHops



def upload_metrics_next_func(file_path,filename, url):
    """
Upload metrics to the next function and calculate bandwidth.

This function uploads a file to a specified URL (representing the next function in a workflow) multiple times, measuring the upload latency and calculating the bandwidth for each upload. 
The upload is performed using a POST request, with the file included as multipart form data. The function returns lists of upload latencies and calculated bandwidths for each iteration.

Parameters:
- file_path (str): The path to the file to be uploaded.
- filename (str): The name of the file to be uploaded.
- url (str): The URL of the next function to which the file will be uploaded.

Returns:
- upload_latency_next_func (list of float): A list of upload latencies to the next function, measured in milliseconds.
- bandwidth_next_func (list of float): A list of calculated bandwidths to the next function, measured in Mbps (Megabits per second).

Example:
upload_latency, bandwidth = upload_metrics_next_func('/path/to/file.txt', 'file.txt', 'http://next_function_endpoint.com')
print(upload_latency)  # Example output: [10.0, 15.0, 20.0]
print(bandwidth)       # Example output: [100.0, 150.0, 200.0]

Note:
- The function iterates 10 times, performing the upload and measurements for each iteration.
- It calculates the bandwidth based on the file size and the measured upload latency for each iteration.
- The function assumes successful uploads for latency and bandwidth calculations. Errors during upload are logged but do not halt the function.
"""  
    upload_latency_next_func = []
    bandwidth_next_func = []
    print("******************************************")
    print("*                                        *")
    print(url)
    print("*                                        *")
    print("******************************************")
    for i in range(10):
        # Send the file to the next function
        print("uploading file to next function. iteration: ",i)
        file_size_bytes = os.path.getsize(file_path)
        files = [('files', (filename, open(file_path, 'rb')))]
        payload = {"source_called_func1": int(time.time() * 1000),"file_name": filename, "file_size": os.path.getsize(file_path)}
        resp = requests.post(url=url, params=payload, files=files, timeout=None) 
        # Print the response
        if resp.status_code == 200:
            latency_to_func = resp.json()['JSON Payload ']['latency_to_func1']
            upload_latency_next_func.append(latency_to_func)
            # Calculate bandwidth in Mbps (Megabits per second)
            bandwidth_Mbps = calculate_transmission_rate(file_size_bytes, latency_to_func)
            bandwidth_next_func.append(bandwidth_Mbps)
            if latency_to_func is not None:
                print(f'Sent {filename}, Latency to func1: {latency_to_func} ms')
            else:
                print(f'Sent {filename}, Response does not contain latency_to_next_func')
        else:
            print(f'Sent {filename}, Error: {resp.status_code}')
    
    return upload_latency_next_func, bandwidth_next_func

async def send_metrics_async(metrics_url, payload):
    """
Send metrics asynchronously to the specified metrics URL.

:param metrics_url: The URL to send the metrics to.
:param payload: The payload containing the metrics data.
:return: None
"""
    async with aiohttp.ClientSession() as session:
        async with session.post(metrics_url, json=payload) as response:
            if response.status != 200:
                print(f"Error: {response.status}")
            else:
                print("Metrics sent successfully")
def wait_for_file_arrival(file_name, metrics_app_url):
    """
Waits for a specific file to arrive to the flow sink method which is func3 in this case.

Parameters:
- file_name (str): The name of the file to wait for.
- metrics_app_url (str): The URL of the metrics application to check for the arrival of the file.

Returns:
- has_arrived (bool): True if the file has arrived, False otherwise.

Description:
This function continuously checks if a specific file has arrived at the given metrics application URL. It uses a while loop to repeatedly check for the arrival of the file. The function sleeps for 1 second between each check to avoid excessive resource usage.

If the file has arrived, the function sets the 'has_arrived' flag to True and breaks out of the loop. If the file has not arrived, the function prints a message indicating the latest file name and continues checking.

If an error occurs during the request to the metrics application URL, the function prints an error message and continues checking.

Once the file has arrived, the function prints a message indicating that the file has arrived and returns the 'has_arrived' flag.

Note: This function assumes that the metrics application URL returns the latest file name as plain text.

Example:
wait_for_file_arrival("file_1.txt", "http://func3:8003/latest_record_file_name/")
"""
    has_arrived = False
    while not has_arrived:
        time.sleep(1)
        print(f"Checking if {file_name} has arrived")
        try:
            latest_file_name = requests.get(metrics_app_url).json().get("file_name")
            print("latest_file_name: ", latest_file_name)
           
            if latest_file_name == file_name:
                has_arrived = True
                print("File has arrived")
                break
            else:
                print(f"{file_name} has not arrived. Latest File is : {latest_file_name.text}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            # Handle the error as needed
    print("File has arrived. Done.")
    return has_arrived

        


def main():
    """
This is the main function of the Data Source Application.

The function performs the following steps:
1. Reads the configuration values from the 'config.ini' file.
2. Sets up the necessary variables and parameters.
3. Starts a timer to measure the total execution time.
4. Iterates over a specified number of files, creating each file and performing the following operations for each file:
    a. Measures the latency statistics and packet loss for the specified server URL using the ping command.
    b. Uploads the file to the next function in the workflow, measuring the upload latency and calculating the bandwidth for each upload.
    c. Constructs a payload containing the metrics data and sends it to the metrics URL.
    d. Waits for the file to arrive at the sink function by continuously checking the metrics application URL.
5. Stops the timer and prints the total execution time and total data transferred.

"""
    print("Data Source Application Started ...")
    config_values = read_config()
    

    expr_code = config_values['expr_code']
    deployment_config = config_values['deployment_config']
    country_code = config_values['country_code']
    source_city = config_values['source_city']
    telco_provider = config_values['telco_provider']
    collection_name = config_values['collection_name']


    start = time.time()
   
    func1_host_ip = config_values['func1_host']
    func2_host_ip = config_values['func2_host']
    func3_host_ip = config_values['func3_host']
    ping_host = func1_host_ip

    # ping_host = "0.0.0.0" if func1_host_ip == "func1" else func1_host_ip
    
    # MEC_MEC_CLOUD ips
    # func1_host_ip = "207.61.170.193"
    # func2_host_ip = "207.61.169.119"
    # func3_host_ip = "99.79.49.51"
    # ping_host= "207.61.170.193"
    # CLOUD_CLOUD_CLOUD ips
    # func1_host_ip = "3.96.230.173"
    # func2_host_ip = "3.96.178.66"
    # func3_host_ip = "99.79.49.51"
    # ping_host= "3.96.230.173"
 
   
    # file_size = int(input("Enter file size in MB: "))
    file_size = 1
    files_directory = 'upload_files/'

    total_size = 0
    number_of_files = 0
    while number_of_files <=10:
        total_size += file_size
        number_of_files += 1
        file_name = f"file_{file_size}.txt"
        file_path = os.path.join(files_directory, file_name)
        create_text_file(file_size, f"{files_directory}{file_name}")
        print("----------- Testing for file : ", file_name, " -----------")
        file_path = os.path.join(files_directory, file_name)
        nextUrl = f"http://{func1_host_ip}:8001/function1"

        latency_metrics, packet_loss, number_of_hops = get_latency_and_packet_loss(ping_host,10)
        upload_latency_next_func, bandwidth_next_func = upload_metrics_next_func(file_path,file_name, nextUrl)

        payload = {
               "file_sent_at": int(time.time() * 1000),
               "source_func1_latency_metrics": latency_metrics,
               "source_func1_packet_loss":packet_loss,
               "source_func1_numberOfHops":number_of_hops,
               "source_func1_uploadLatency":upload_latency_next_func,
               "source_func1_bandwidth":bandwidth_next_func,
               "file_name": file_name,
               "file_size": os.path.getsize(file_path),
               "func1_host": func1_host_ip, 
               "func2_host": func2_host_ip,
               "func3_host": func3_host_ip, 
               "expr_code" : expr_code, 
               "deployment_config" : deployment_config,
               "country_code" : country_code,
               "source_city" : source_city,
               "telco_provider" : telco_provider,
               "collection_name": collection_name,   
        }

        print("-- [MAIN] sending metrics down the stream: ", file_name)
       
        metrics_url = f"http://{func1_host_ip}:8001/metrics"
        print("******************************************")
        print("*                                        *")
        print("*                                        *")
        print(payload)
        print("*                                        *")
        print("******************************************")
        asyncio.run(send_metrics_async(metrics_url, payload))  
        print("-- [MAIN] waiting for file to arrive at sink: ", file_name)
        # wait_for_file_arrival(file_name, f"http://func3:8003/latest_record_file_name/")
        wait_for_file_arrival(file_name, f"https://t5e9nqlxrh.execute-api.ca-central-1.amazonaws.com/?collection_name={collection_name}")
        # wait_for_file_arrival(file_name, f"http://func3:8003/latest_record_file_name/{collection_name}/")
        print("-------------- Done for file : ", file_name, " --------------")
        print("starting next iteration with new file")
        # file_size = int(input("Enter file size in MB: "))
        file_size += 100
    
    end = time.time()
    print("Total time taken =  ", end - start)
    print("Total Data Transferred = ", total_size)
   

if __name__ == "__main__":
    main()

# docker build -t source-app .
# docker run -it source-app
# docker run source-app

