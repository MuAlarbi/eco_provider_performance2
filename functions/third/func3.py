from fastapi import Form, File, UploadFile, Request, FastAPI, Depends,HTTPException
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
from motor.motor_asyncio import AsyncIOMotorClient



app = FastAPI() 
# MongoDB connection details
MONGO_DETAILS = "mongodb://localhost:27017"
DATABASE = "metrics_database"  


client = AsyncIOMotorClient(MONGO_DETAILS)
db = client[DATABASE]

collection = db["eco_local_test"]


templates = Jinja2Templates(directory="templates")

results = list()


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
    func2_called_func3: int
    func3_receivedAt: Optional[int] = None
    latency_to_func3: Optional[int] = None
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
    collection_name: Optional[str] = None

async def write_to_collection(name: str):

    document = {"name": name}
    result = await collection.insert_one(document)
    print("expriment record inserted with id: ", result.inserted_id)
    return result.inserted_id


async def add_to_collection(metrics: Metrics, collection_name: str = "eco_local_test"):

    try:
        print("Inside add_to_collection")
        collection = db[collection_name]
        inserted_id = await collection.insert_one(metrics.dict())
        print("#### inserted_id: ",inserted_id)
        return {"inserted_id": str(inserted_id)}
    except Exception as e:
        print("#### Exception: ",e)
        raise HTTPException(status_code=500, detail=str(e))
    

metricsList = []


def get_latency_and_packet_loss(server_url, number_of_requests):
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


@app.post("/function3")
def submit(latencyTracker: LatencyTracker = Depends(), files: List[UploadFile] = File(...)):
    latencyTracker.func3_receivedAt = int(time.time() * 1000)
    latencyTracker.latency_to_func3 = latencyTracker.func3_receivedAt - latencyTracker.func2_called_func3
    # Now, you can pass the filename to the request
    file_contents = files[0].file.read()
    with open(files[0].filename, "wb") as f:
        f.write(file_contents)

    print(f"!!!!!! file {files[0].filename} arrived at func3 with size = {os.path.getsize(files[0].filename)} ")
    return {
        "JSON Payload ": latencyTracker.dict()}

def upload_metrics_next_3(file_path,file_name, url):
    upload_latency_next_func = []
    bandwidth_next_func = []
    file_size_bytes = os.path.getsize(file_path)
    files = [('files', (file_name, open(file_path, 'rb')))]
    # Create a tuple with the file data 
    payload = {"func2_called_func3": int(time.time() * 1000),"file_name": file_name, "file_size": os.path.getsize(file_path)}

    for i in range(10):
        # Send the file to the next function
        print("uploading file to next function. iteration: ",i)
        resp = requests.post(url=url, params=payload, files=files) 
        # Print the response
        if resp.status_code == 200:
            latency_to_func = resp.json()['JSON Payload ']['latency_to_sink']
            upload_latency_next_func.append(latency_to_func)
            # Calculate bandwidth in Mbps (Megabits per second)
            bandwidth_Mbps = calculate_transmission_rate(file_size_bytes, latency_to_func)
           
            bandwidth_next_func.append(bandwidth_Mbps)
            if latency_to_func is not None:
                print(f'Sent {file_name}, Latency to sink: {latency_to_func} ms')
            else:
                print(f'Sent {file_name}, Response does not contain latency_to_next_func')
        else:
            print(f'Sent {file_name}, Error: {resp.status_code}')
    
    return upload_latency_next_func, bandwidth_next_func

async def send_data_async(url, payload):
    async with aiohttp.ClientSession() as session:
        await session.post(url, json=payload)
@app.post("/metrics")
async def receive_metrics(metrics: Metrics):
    print("##############################################################################################################")
    print("##############################################################################################################")
    print("###################################### PIPELINE METRICS ######################################################")
    print("##############################################################################################################")
    print("##############################################################################################################")

    # print("func3 metrics received",metrics.model_dump_json())
    results.append(metrics)

    url = f"https://nhionvk7u2.execute-api.ca-central-1.amazonaws.com?collection_name={metrics.collection_name}"

    data = metrics.dict()
    response = requests.post(url, json=data)
    # Check the response (assuming it's JSON)
    response_data = response.json()
    print("metrics sent to the database")
   

@app.get("/", response_class=HTMLResponse)
def main():
    return "This is the main page of the function 3."


@app.get("/results")
def getResults():
    return results


@app.get("/latest_record_file_name/{collection_name}/")
async def get_latest_record_file_name(collection_name: str):

    # Dynamically access the collection
    collection = db[collection_name]
    # Fetch only the 'file_name' field of the most recent document
    latest_document = await collection.find_one({}, sort=[("_id", -1)], projection={"file_name": 1, "_id": 0})
    if latest_document:
        return latest_document.get("file_name")
    else:
        return {"message": "No records found"}

# python3 -m uvicorn func3_async:app --host 0.0.0.0 --port 8003 --reload
# source ~/venv-metal/bin/activate
    


# docker-compose up --build