

import subprocess
import re
import platform
import numpy as np

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
    defualtTTL = 256
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





print(get_latency_and_packet_loss("www.google.com", 10))