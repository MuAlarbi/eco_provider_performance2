from fastapi import Form, File, UploadFile, Request, FastAPI, Depends
from typing import List
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from fastapi.templating import Jinja2Templates
import time
import os
import subprocess
import re
import platform
import requests
import aiohttp 

app = FastAPI()
templates = Jinja2Templates(directory="templates")
# Deployer IP:
func3_host_ip = "35.183.78.90"

def calculate_transmission_rate(file_size_bytes, upload_latency_ms):
    # Convert file size to bits
    file_size_bits = file_size_bytes * 8

    # Convert latency to seconds
    upload_latency_s = upload_latency_ms / 1000

    # Calculate transmission rate in bits per second
    transmission_rate_bps = file_size_bits / upload_latency_s

    # Convert transmission rate to megabits per second
    transmission_rate_mbps = transmission_rate_bps / 1e6

    return transmission_rate_mbps

class LatencyTracker(BaseModel):
    func1_called_func2: int
    fun2_receivedAt: Optional[int] = None
    latency_to_func2: Optional[int] = None
    file_size: Optional[int] = None
    file_name: Optional[str] = None

class Metrics(BaseModel):
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    expr_code: Optional[str] = None
    deployment_config: Optional[str] = None
    file_size_reduction_rate: Optional[float] = None
    file_size_static: Optional[str] = None
    source_func1_latency_metrics: Optional[list] = None
    source_func1_packet_loss: Optional[float] = None
    source_func1_jitter: Optional[float] = None
    source_func1_numberOfHops: Optional[list] = None
    source_func1_uploadLatency: Optional[list] = None
    source_func1_bandwidth: Optional[list] = None
    func1_func2_file_size: Optional[int] = None
    func1_func2_latency_metrics: Optional[list] = None
    func1_func2_packet_loss: Optional[float] = None
    func1_func2_jitter: Optional[float] = None
    func1_func2_numberOfHops: Optional[list] = None
    func1_func2_uploadLatency: Optional[list] = None
    func1_func2_bandwidth: Optional[list] = None
    func2_func3_file_size: Optional[int] = None
    func2_func3_latency_metrics: Optional[list] = None
    func2_func3_latency_metrics: Optional[list] = None
    func2_func3_packet_loss: Optional[float] = None
    func2_func3_jitter: Optional[float] = None
    func2_func3_numberOfHops: Optional[list] = None
    func2_func3_uploadLatency: Optional[list] = None
    func2_func3_bandwidth: Optional[list] = None
    # func3_sink_file_size: Optional[int] = None
    # func3_sink_latency_metrics: Optional[list] = None
    # func3_sink_packet_loss: Optional[float] = None
    # func3_sink_jitter: Optional[float] = None
    # func3_sink_numberOfHops: Optional[list] = None
    # func3_sink_uploadLatency: Optional[list] = None
    # func3_sink_bandwidth: Optional[list] = None
    # end_to_end_latency: Optional[int] = None
    func1_host: Optional[str] = None, 
    func2_host: Optional[str] = None,
    func3_host: Optional[str] = None,
    country_code: Optional[str] = None,
    source_city: Optional[str] = None,
    telco_provider: Optional[str] = None,
    collection_name : Optional[str] = None



def get_latency_and_packet_loss(server_url, number_of_requests):
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

@app.post("/function2")
def submit(latencyTracker: LatencyTracker = Depends(), files: List[UploadFile] = File(...)):
    latencyTracker.fun2_receivedAt = int(time.time() * 1000)
    latencyTracker.latency_to_func2 = latencyTracker.fun2_receivedAt - latencyTracker.func1_called_func2
    # Now, you can pass the filename to the request
    file_contents = files[0].file.read()
    with open(files[0].filename, "wb") as f:
        f.write(file_contents)
    print(f"!!!!!! file {files[0].filename} arrived at func2 with size = {os.path.getsize(files[0].filename)} ")
    return {
        "JSON Payload ": latencyTracker.dict()}

def upload_metrics_next_func(file_path,filename, url):
    # file_path = os.path.join(files_directory, filename)
    
    # Check if the item is a file (not a directory)
    if not os.path.isfile(file_path):
        print(f"############### file {file_path} does not exist ############### ")
        return None, None
    upload_latency_next_func = []
    bandwidth_next_func = []
    for i in range(10):
        # Send the file to the next function
        print("uploading file to next function. iteration: ",i)
        file_size_bytes = os.path.getsize(file_path)
        files = [('files', (filename, open(file_path, 'rb')))]
        
        payload = {"func2_called_func3": int(time.time() * 1000),"file_name": filename, "file_size": os.path.getsize(file_path)}
        resp = requests.post(url=url, params=payload, files=files) 
        # Print the response
        if resp.status_code == 200:
            latency_to_func = resp.json()['JSON Payload ']['latency_to_func3']
            upload_latency_next_func.append(latency_to_func)
            # Calculate bandwidth in Mbps (Megabits per second)
            bandwidth_Mbps = calculate_transmission_rate(file_size_bytes, latency_to_func)
            bandwidth_next_func.append(bandwidth_Mbps)
            if latency_to_func is not None:
                print(f'Sent {filename}, Latency to func3: {latency_to_func} ms')
            else:
                print(f'Sent {filename}, Response does not contain latency_to_next_func')
        else:
            print(f'Sent {filename}, Error: {resp.status_code}')
    
    return upload_latency_next_func, bandwidth_next_func


async def send_data_async(url, payload):
    async with aiohttp.ClientSession() as session:
        await session.post(url, json=payload)
@app.post("/metrics")
async def receive_metrics(metrics: Metrics):
    # Do something with the metrics here.
    nextUrl = "http://"+metrics.func3_host+':8003/function3'
    print("func2 metrics received",metrics)

    print("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")

    print("pinging function 3 host to collect latency packet_loss and numberOfHops metrics ...")
    latency_metrics, packet_loss, numberOfHops = get_latency_and_packet_loss(metrics.func3_host,10)
    print("Sending files to function 3 to collect upload latency and bandwidth metrics ...")
    file_path = os.path.join("/", metrics.file_name)
    upload_latency_next_func, bandwidth_next_func = upload_metrics_next_func(metrics.file_name, metrics.file_name, nextUrl)

    payload = {
            "source_func1_latency_metrics": metrics.source_func1_latency_metrics,
            "source_func1_packet_loss":metrics.source_func1_packet_loss,
            "source_func1_numberOfHops":metrics.source_func1_numberOfHops,
            "source_func1_uploadLatency":metrics.source_func1_uploadLatency,
            "source_func1_bandwidth":metrics.source_func1_bandwidth,
            "func1_func2_latency_metrics": metrics.func1_func2_latency_metrics,
            "func1_func2_packet_loss":metrics.func1_func2_packet_loss,
            "func1_func2_numberOfHops":metrics.func1_func2_numberOfHops,
            "func1_func2_uploadLatency":metrics.func1_func2_uploadLatency,
            "func1_func2_bandwidth":metrics.func1_func2_bandwidth,

            "func2_func3_latency_metrics": latency_metrics,
            "func2_func3_packet_loss":packet_loss,
            "func2_func3_numberOfHops":numberOfHops,
            "func2_func3_uploadLatency":upload_latency_next_func,
            "func2_func3_bandwidth":bandwidth_next_func,
            "file_name": metrics.file_name,
            "file_size": metrics.file_size,
            "func1_host": metrics.func1_host, 
            "func2_host": metrics.func2_host,
            "func3_host": metrics.func3_host,
            "expr_code" : metrics.expr_code, 
            "deployment_config" : metrics.deployment_config,
            "country_code" : metrics.country_code,
            "source_city" : metrics.source_city,
            "telco_provider" : metrics.telco_provider,
            "collection_name" : metrics.collection_name
            }
    metrics.func2_func3_latency_metrics = latency_metrics
    metrics.func2_func3_packet_loss = packet_loss
    metrics.func2_func3_numberOfHops = numberOfHops
    metrics.func2_func3_uploadLatency = upload_latency_next_func
    metrics.func2_func3_bandwidth = bandwidth_next_func

    next_url = f"http://{metrics.func3_host}:8003/metrics"
    await send_data_async(next_url, payload)
    
    if os.path.isfile(metrics.file_name):
        print("FILE to BE DELETED ####### file_size_at func2",os.path.getsize(metrics.file_name))
        # os.remove(metrics.file_name)

    # return {"message": metrics_response.json()['message']}
@app.get("/")
def main():
    return "This is function 2"

# python3 -m uvicorn func2_async:app --host 0.0.0.0 --port 8002 --reload
# source ~/venv-metal/bin/activate



# docker-compose up --build 