# Replicated Log

A simple distributed log system built with Python and Docker, featuring one **Master** node and multiple **Secondary** nodes. The Master node handles log append and retrieval operations, while Secondary nodes replicate logs from the Master and provide read-only access to the logs.

## Table of Contents

- [Introduction](#introduction)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)

## Introduction

This project implements a **Distributed Log System** using Python, FastAPI, and Docker. 
The system consists of one Master node and multiple Secondary nodes. 
The Master node allows clients to append and retrieve log messages, 
while Secondary nodes replicate these logs to ensure data consistency and provide read-only access.

## Architecture

1. **Master Node**:
   - Handles `POST /logs` request to append logs and `GET /logs` to retrieve list of logs.
   - Maintains an in-memory list of logs.
   - Replicates logs to all Secondary nodes and waits for acknowledgments (ACKs).

2. **Secondary Nodes**:
   - Handle retrieving list of replicated logs via `GET /logs` request.
   - Receive replicated logs from the Master.
   - Introduce a configurable delay to simulate replication latency.

3. **Clients**:
   - Interact with the Master for appending and retrieving logs.
   - Interact with Secondaries for retrieving replicated logs.
   - Could be used any 3rd party HTTP client like `curl`, `Postman`, etc.

## Technology Stack

- **Programming Language**: Python 3.12
- **Web Framework**: FastAPI
- **HTTP Client**: `requests` library
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Logging**: Python's built-in `logging` module

## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Docker**: [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: [Install Docker Compose](https://docs.docker.com/compose/install/)
- **Git**: [Install Git](https://git-scm.com/downloads)

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/distributed-log-system.git
   cd distributed-log-system

## Usage

To run the Replicated Log using Docker Compose, follow the steps below:

###  1. Start the Application with Docker Compose

Open your terminal and navigate to the directory containing your `docker-compose.yml` file

```bash
cd /path/to/your/project/replicated-log
``` 
and run the command to start the Master and Secondary nodes:

```bash
docker-compose up --build
```

The **Replicated Log** allows you to append log messages to a Master node, which then asynchronously replicates these logs to multiple Secondary nodes. This ensures data consistency and reliability across your distributed system. Below are detailed instructions and examples on how to interact with the system using HTTP requests.

### 2. Setup Environment Variables

Copy `.env.example` to `.env` file in your project root directory and set the values:

`SECONDARY_URLS`: Comma-separated list of Secondary node URLs.
`RETRY_COUNT`: Number of retry attempts for replication in case of failure.
`RETRY_DELAY`: Delay in seconds between retry attempts.
`REPLICATE_SECRET`: API key for securing replication endpoints.
`MAX_REPLICATION_DELAY`: Maximum delay in seconds for simulating replication latency.

```bash

### 3. Append a Log Entry

To append a new log message to the system, send a `POST` request to the Master's `/logs` endpoint with the log message in the request body.

**Request:**

```bash
curl -X POST "http://localhost:8000/logs" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "System initialization complete.",
       "write_concern": 3
       }'
```
**Response Example :**

```json
{
   "id": "bab0f486-96de-40ad-b784-b8411de1be15",
   "message": "System initialization complete.",
   "write_concern": 3,
   "sequence_number": 1
}
```

### 4. Listing Logs

Retrieving log entries from your Distributed Log System is straightforward. You can fetch logs from both the **Master** and **Secondary** nodes using `GET` requests. Below are detailed instructions and examples on how to list logs from different nodes.

#### A. Retrieving Logs from the Master Node

To fetch all log entries stored in the Master node, send a `GET` request to the Master's `/logs` endpoint.

**Request:**

```bash
curl -X GET "http://localhost:8000/logs"
```
**Response Example :**

```json
[
  {
    "id": "bab0f486-96de-40ad-b784-b8411de1be15",
    "message": "System initialization complete.",
    "write_concern": 3,
    "sequence_number": 1
  },
  {
    "id": "8ae10d46-ae8b-470e-9b04-509049924154",
    "message": "User login successful.",
    "write_concern": 1,
    "sequence_number": 2 
  }
]
```

#### B. Retrieving Logs from a Secondary Node

To verify that logs have been successfully replicated, you can fetch logs from any Secondary node by sending a GET request to its `/logs` endpoint.
**Request:**

```bash
curl -X GET "http://localhost:8001/logs"
```
**Response Example :**

```json
[
  {
    "id": "bab0f486-96de-40ad-b784-b8411de1be15",
    "message": "System initialization complete.",
    "write_concern": 3,
    "sequence_number": 1
  },
  {
    "id": "8ae10d46-ae8b-470e-9b04-509049924154",
    "message": "User login successful.",
    "write_concern": 1,
    "sequence_number": 2 
  }
]
```

**Note:**
Replace 8001 with the appropriate port number if you have additional Secondary nodes (e.g., 8002, 8003, etc.).

## Deduplication
The Replicated Log system includes a deduplication mechanism to ensure that each log entry is only saved once, preventing duplicates. This is achieved by maintaining a set of unique log entries and checking for duplicates before saving them to the storage file.

The deduplication functionality is implemented in the `BaseStorageStrategy` class. This class uses a set data structure to track unique log entries and ensures that only new, unique entries are appended to the storage file

## Total Ordering
The Replicated Log system ensures total ordering of log entries across secondary nodes. 
This guarantees that all logs are retrieved in the same order they were received, maintaining consistency and reliability.
Sequence validation is performed to ensure that logs are appended and replicated in the correct order and their amount is equal to the maximum sequence number across all log records.

## Health Checking
The Replicated Log system includes a health checking mechanism to monitor the status of the Secondary nodes. 
This ensures that the system can detect and respond to node failures, maintaining the reliability and consistency of the log replication process.  

#### Configuration
The health check functionality can be configured using environment variables:  
- `HEALTH_CHECK_INTERVAL`: The interval in seconds between health check requests.
- `HEALTH_CHECK_TIMEOUT`: The timeout in seconds for each health check request.
- `HEALTHY_THRESHOLD`: The number of consecutive successful health checks required to mark a node as healthy.
- `UNHEALTHY_THRESHOLD`: The number of consecutive failed health checks required to mark a node as unhealthy.

#### Statuses
- **Healthy**: A node is considered healthy if it responds successfully to the `HEALTHY_THRESHOLD` check requests.
- **Suspected**: A node is considered suspected if it intermittently fails to respond to health check requests but does not meet the `UNHEALTHY_THRESHOLD` to be marked as unhealthy.
- **Unhealthy**: A node is considered unhealthy if it fails to respond to the health check requests within a specified `UNHEALTHY_THRESHOLD`.

#### Health Status Endpoint
**Request:**
```bash
curl -X GET "http://localhost:8000/health"
```
**Response Example :**

```json
{
  "nodes": [
    {
      "node_url": "http://secondary1:8000",
      "healthy_count": 12,
      "unhealthy_count": 0,
      "status": "healthy",
      "last_updated": "2024-12-09T14:38:19.540197"
    },
    {
      "node_url": "http://secondary2:8000",
      "healthy_count": 4,
      "unhealthy_count": 0,
      "status": "healthy",
      "last_updated": "2024-12-09T14:40:51.535589"
    }
  ]
}
```

## Quorum Checking
The Replicated Log system uses a quorum-based approach to ensure data consistency and reliability across the distributed nodes. The quorum functionality is crucial for maintaining the integrity of the log replication process.

The Master node is responsible for appending log entries and replicating them to the Secondary nodes. It waits for acknowledgments (ACKs) from a quorum of Secondary nodes before confirming the log entry to the client. 

#### Quorum Calculation
The quorum is typically defined as a majority of the nodes. The formula for calculating the quorum is 50% of the total number of nodes plus 1.

For example:
- if there are 2 Secondary nodes, a quorum would be 2 nodes;
- if there are 3 Secondary nodes, a quorum would be 3 nodes; 
- if there are 4 Secondary nodes, a quorum would be 3 nodes as well

**Response example when quorum is not met:**
```json
{
    "detail": "Read-only mode due to insufficient nodes quorum."
}
```

## Example of docker-compose logs

```bash
secondary2  | 2024-12-09 17:34:29,365 [INFO] Max Replication Delay set to: 1 seconds. 
secondary2  | INFO:     Started server process [1]
secondary2  | INFO:     Waiting for application startup.                                                                                                                                                                            
secondary2  | INFO:     Application startup complete.                                                                                                                                                                               
secondary2  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)                                                                                                                                              
secondary1  | 2024-12-09 17:34:29,382 [INFO] Max Replication Delay set to: 1 seconds.                                                                                                                                               
secondary1  | INFO:     Started server process [1]
secondary1  | INFO:     Waiting for application startup.                                                                                                                                                                            
secondary1  | INFO:     Application startup complete.                                                                                                                                                                               
secondary1  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)                                                                                                                                             
master      | 2024-12-09 17:34:29,707 [INFO] Loaded 2 secondary URLs.                                                                                                                                                               
master      | 2024-12-09 17:34:29,707 [INFO] Initial Retry Delay set to: 2 seconds.
master      | 2024-12-09 17:34:29,707 [INFO] Max Retry Delay set to: 30 seconds.                                                                                                                                                    
master      | INFO:     Started server process [1]                                                                                                                                                                                  
master      | INFO:     Waiting for application startup.
master      | INFO:     Application startup complete.                                                                                                                                                                               
master      | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)                                                                                                                                            
secondary2  | INFO:     172.21.0.4:44324 - "GET /ping HTTP/1.1" 200 OK
secondary1  | INFO:     172.21.0.4:60774 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
master      | 2024-12-09 17:34:29,818 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                       
master      | 2024-12-09 17:34:29,818 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                      
master      | 2024-12-09 17:34:29,819 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:34:29,819 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
secondary2  | INFO:     172.21.0.4:36286 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary1  | INFO:     172.21.0.4:41998 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:34:34,894 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:34:34,896 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:34:34,896 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:34:34,897 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:34:35,268 [INFO] Master node switched to writable mode.                                                                                                                                                 
master      | 2024-12-09 17:34:35,268 [INFO] Log #1. Received log entry request: async log entry.  ### 1st Log message received on Master
master      | 2024-12-09 17:34:35,268 [INFO] Log #1. Appended log to the storage                                                                                                                                                    
master      | 2024-12-09 17:34:35,268 [INFO] Log #1. Secondary URLs to replicate to: ['http://secondary1:8000', 'http://secondary2:8000']                                                                                           
master      | 2024-12-09 17:34:35,269 [INFO] Replication count for message #1 is 1/1                                                                                                                                         
master      | 2024-12-09 17:34:35,269 [INFO] Write concern 1 met. Responding immediately.                                                                                                                                           
master      | INFO:     172.21.0.1:59572 - "POST /logs HTTP/1.1" 200 OK   ### Client response for 1st Log message                                                                                                                                                             
master      | 2024-12-09 17:34:35,269 [INFO] Log #1. Attempting replication to http://secondary1:8000. Attempt 1                                                                                                                    
master      | 2024-12-09 17:34:35,270 [INFO] Log #1. Attempting replication to http://secondary2:8000. Attempt 1                                                                                                                    
secondary2  | 2024-12-09 17:34:35,281 [INFO] Log #1. Simulating replication delay of 1 seconds                                                                                                                                      
secondary1  | 2024-12-09 17:34:35,281 [INFO] Log #1. Simulating replication delay of 1 seconds                                                                                                                                      
secondary2  | 2024-12-09 17:34:36,282 [INFO] Log #1. Replicated to secondary node                                                                                                                                                   
secondary2  | INFO:     172.21.0.4:36302 - "POST /replicate HTTP/1.1" 200 OK
secondary1  | 2024-12-09 17:34:36,283 [INFO] Log #1. Replicated to secondary node                                                                                                                                                   
secondary1  | INFO:     172.21.0.4:42008 - "POST /replicate HTTP/1.1" 200 OK                                                                                                                                                   
master      | 2024-12-09 17:34:36,285 [INFO] HTTP Request: POST http://secondary1:8000/replicate "HTTP/1.1 200 OK"                                                                                                                  
master      | 2024-12-09 17:34:36,286 [INFO] HTTP Request: POST http://secondary2:8000/replicate "HTTP/1.1 200 OK"                                                                                                                  
secondary1  | INFO:     172.21.0.4:42016 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary2  | INFO:     172.21.0.4:36314 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:34:39,962 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:34:39,962 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:34:39,963 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:34:39,963 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:34:44,017 [INFO] Master node switched to writable mode.                                                                                                                                                 
master      | 2024-12-09 17:34:44,018 [INFO] Log #2. Received log entry request: async log entry.
master      | 2024-12-09 17:34:44,018 [INFO] Log #2. Appended log to the storage                                                                                                                                                    
master      | 2024-12-09 17:34:44,018 [INFO] Log #2. Secondary URLs to replicate to: ['http://secondary1:8000', 'http://secondary2:8000']                                                                                           
master      | 2024-12-09 17:34:44,018 [INFO] Replication count for message #2 is 1/3                                                                                                                                                
master      | 2024-12-09 17:34:44,018 [INFO] Log #2. Attempting replication to http://secondary1:8000. Attempt 1                                                                                                                    
master      | 2024-12-09 17:34:44,019 [INFO] Log #2. Attempting replication to http://secondary2:8000. Attempt 1                                                                                                                    
secondary2  | 2024-12-09 17:34:44,022 [INFO] Log #2. Simulating replication delay of 1 seconds                                                                                                                                      
secondary1  | 2024-12-09 17:34:44,022 [ERROR] Log #2. Simulated error for log replication with 10.0% chance                                                                                                                         
secondary1  | 2024-12-09 17:34:44,022 [ERROR] Log #2. Unexpected error in replication: 500: Simulated internal server error                                                                                                         
secondary1  | INFO:     172.21.0.4:57190 - "POST /replicate HTTP/1.1" 500 Internal Server Error                                                                                                                                     
master      | 2024-12-09 17:34:44,023 [INFO] HTTP Request: POST http://secondary1:8000/replicate "HTTP/1.1 500 Internal Server Error"                                                                                               
master      | 2024-12-09 17:34:44,024 [WARNING] Log #2. Replication to http://secondary1:8000 failed with status code 500 on attempt 1                                                                                              
master      | 2024-12-09 17:34:44,024 [INFO] Waiting for 3.56 seconds before retrying...                                                                                                                                            
secondary2  | 2024-12-09 17:34:45,023 [INFO] Log #2. Replicated to secondary node                                                                                                                                                   
secondary2  | INFO:     172.21.0.4:45618 - "POST /replicate HTTP/1.1" 200 OK
master      | 2024-12-09 17:34:45,054 [INFO] HTTP Request: POST http://secondary2:8000/replicate "HTTP/1.1 200 OK"                                                                                                                  
master      | 2024-12-09 17:34:45,056 [INFO] Replication count for message #2 is 2/3
secondary2  | INFO:     172.21.0.4:45634 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary1  | INFO:     172.21.0.4:57198 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
master      | 2024-12-09 17:34:45,060 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"
master      | 2024-12-09 17:34:45,062 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:34:45,063 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:34:45,063 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:34:47,590 [INFO] Log #2. Attempting replication to http://secondary1:8000. Attempt 2                                                                                                                    
secondary1  | 2024-12-09 17:34:47,594 [INFO] Log #2. Simulating replication delay of 1 seconds
secondary1  | 2024-12-09 17:34:48,596 [INFO] Log #2. Replicated to secondary node                                                                                                                                                   
secondary1  | INFO:     172.21.0.4:57190 - "POST /replicate HTTP/1.1" 200 OK
master      | 2024-12-09 17:34:48,602 [INFO] HTTP Request: POST http://secondary1:8000/replicate "HTTP/1.1 200 OK"                                                                                                                  
master      | 2024-12-09 17:34:48,603 [INFO] Replication count for message #2 is 3/3                                                                                                                                                
master      | 2024-12-09 17:34:48,604 [INFO] Write concern 3 met. Responding to client.                                                                                                                                             
master      | INFO:     172.21.0.1:40990 - "POST /logs HTTP/1.1" 200 OK                                                                                                                                                             
secondary1  | INFO:     172.21.0.4:57202 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary2  | INFO:     172.21.0.4:45650 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:34:50,146 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:34:50,146 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:34:50,147 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:34:50,147 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
secondary1  | INFO:     172.21.0.4:36940 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary2  | INFO:     172.21.0.4:50574 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:34:55,208 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:34:55,208 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:34:55,209 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:34:55,209 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:34:56,307 [INFO] Master node switched to writable mode.                                                                                                                                                 
master      | 2024-12-09 17:34:56,307 [INFO] Log #3. Received log entry request: async log entry.
master      | 2024-12-09 17:34:56,308 [INFO] Log #3. Appended log to the storage                                                                                                                                                    
master      | 2024-12-09 17:34:56,308 [INFO] Log #3. Secondary URLs to replicate to: ['http://secondary1:8000', 'http://secondary2:8000']                                                                                           
master      | 2024-12-09 17:34:56,308 [INFO] Replication count for message #3 is 1/2                                                                                                                                                
master      | 2024-12-09 17:34:56,308 [INFO] Log #3. Attempting replication to http://secondary1:8000. Attempt 1                                                                                                                    
master      | 2024-12-09 17:34:56,309 [INFO] Log #3. Attempting replication to http://secondary2:8000. Attempt 1                                                                                                                    
secondary2  | 2024-12-09 17:34:56,314 [INFO] Log #3. Simulating replication delay of 1 seconds                                                                                                                                      
secondary1  | 2024-12-09 17:34:56,314 [INFO] Log #3. Simulating replication delay of 1 seconds                                                                                                                                      
secondary2  | 2024-12-09 17:34:57,315 [INFO] Log #3. Replicated to secondary node
secondary2  | INFO:     172.21.0.4:50576 - "POST /replicate HTTP/1.1" 200 OK
master      | 2024-12-09 17:34:57,316 [INFO] HTTP Request: POST http://secondary2:8000/replicate "HTTP/1.1 200 OK"                                                                                                                  
secondary1  | 2024-12-09 17:34:57,316 [INFO] Log #3. Replicated to secondary node                                                                                                                                                   
master      | 2024-12-09 17:34:57,316 [INFO] Replication count for message #3 is 2/2                                                                                                                                                
secondary1  | INFO:     172.21.0.4:36944 - "POST /replicate HTTP/1.1" 200 OK                                                                                                                                                        
master      | 2024-12-09 17:34:57,316 [INFO] Write concern 2 met. Responding to client.                                                                                                                                             
master      | INFO:     172.21.0.1:51864 - "POST /logs HTTP/1.1" 200 OK                                                                                                                                                             
master      | 2024-12-09 17:34:57,318 [INFO] HTTP Request: POST http://secondary1:8000/replicate "HTTP/1.1 200 OK"                                                                                                                  
secondary2  | INFO:     172.21.0.4:50578 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary1  | INFO:     172.21.0.4:36956 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:35:00,307 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:35:00,308 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:35:00,309 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:35:00,309 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
secondary2  | INFO:     Shutting down                                                                                                                                                                                               
secondary1  | INFO:     172.21.0.4:47932 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:35:05,372 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"
master      | 2024-12-09 17:35:05,373 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:35:05,373 [INFO] Node http://secondary2:8000 is suspected                                                                                                                                               
secondary2  | INFO:     Waiting for application shutdown.                                                                                                                                                                           
secondary2  | INFO:     Application shutdown complete.
secondary2  | INFO:     Finished server process [1]                                                                                                                                                                                 
secondary2 exited with code 0
secondary1  | INFO:     172.21.0.4:47936 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:35:10,435 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"
master      | 2024-12-09 17:35:12,269 [INFO] Master node switched to writable mode.                                                                                                                                                 
master      | 2024-12-09 17:35:12,269 [INFO] Log #4. Received log entry request: async log entry.
master      | 2024-12-09 17:35:12,269 [INFO] Log #4. Appended log to the storage                                                                                                                                                    
master      | 2024-12-09 17:35:12,270 [INFO] Log #4. Secondary URLs to replicate to: ['http://secondary1:8000', 'http://secondary2:8000']                                                                                           
master      | 2024-12-09 17:35:12,270 [INFO] Replication count for message #4 is 1/2                                                                                                                                                
master      | 2024-12-09 17:35:12,270 [INFO] Log #4. Attempting replication to http://secondary1:8000. Attempt 1                                                                                                                    
master      | 2024-12-09 17:35:12,270 [INFO] Node http://secondary2:8000 is suspected. Skipping replication.                                                                                                                        
master      | 2024-12-09 17:35:12,270 [INFO] Waiting for 3.10 seconds before retrying...                                                                                                                                            
secondary1  | 2024-12-09 17:35:12,273 [ERROR] Log #4. Simulated error for log replication with 10.0% chance                                                                                                                         
secondary1  | 2024-12-09 17:35:12,273 [ERROR] Log #4. Unexpected error in replication: 500: Simulated internal server error                                                                                                         
secondary1  | INFO:     172.21.0.4:34432 - "POST /replicate HTTP/1.1" 500 Internal Server Error                                                                                                                                     
master      | 2024-12-09 17:35:12,274 [INFO] HTTP Request: POST http://secondary1:8000/replicate "HTTP/1.1 500 Internal Server Error"                                                                                               
master      | 2024-12-09 17:35:12,275 [WARNING] Log #4. Replication to http://secondary1:8000 failed with status code 500 on attempt 1                                                                                              
master      | 2024-12-09 17:35:12,275 [INFO] Waiting for 3.62 seconds before retrying...                                                                                                                                            
master      | 2024-12-09 17:35:13,434 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:35:13,434 [INFO] Node http://secondary2:8000 is unhealthy
master      | 2024-12-09 17:35:15,370 [INFO] Node http://secondary2:8000 is unhealthy. Skipping replication.                                                                                                                        
master      | 2024-12-09 17:35:15,370 [INFO] Waiting for 7.38 seconds before retrying...
master      | 2024-12-09 17:35:15,899 [INFO] Log #4. Attempting replication to http://secondary1:8000. Attempt 2                                                                                                                    
secondary1  | 2024-12-09 17:35:15,901 [INFO] Log #4. Simulating replication delay of 1 seconds
secondary1  | 2024-12-09 17:35:16,902 [INFO] Log #4. Replicated to secondary node                                                                                                                                                   
secondary1  | INFO:     172.21.0.4:34432 - "POST /replicate HTTP/1.1" 200 OK
master      | 2024-12-09 17:35:16,904 [INFO] HTTP Request: POST http://secondary1:8000/replicate "HTTP/1.1 200 OK"                                                                                                                  
master      | 2024-12-09 17:35:16,906 [INFO] Replication count for message #4 is 2/2                                                                                                                                                
master      | 2024-12-09 17:35:16,906 [INFO] Write concern 2 met. Responding to client.                                                                                                                                             
master      | INFO:     172.21.0.1:41290 - "POST /logs HTTP/1.1" 200 OK                                                                                                                                                             
secondary1  | INFO:     172.21.0.4:34442 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
master      | 2024-12-09 17:35:18,543 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"
master      | 2024-12-09 17:35:21,514 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:35:21,514 [INFO] Node http://secondary2:8000 is unhealthy
master      | 2024-12-09 17:35:22,746 [INFO] Node http://secondary2:8000 is unhealthy. Skipping replication.                                                                                                                        
master      | 2024-12-09 17:35:22,746 [INFO] Waiting for 11.57 seconds before retrying...
master      | 2024-12-09 17:35:25,487 [INFO] Master node switched to writable mode.                                                                                                                                                 
master      | 2024-12-09 17:35:25,488 [INFO] Log #5. Received log entry request: async log entry.
master      | 2024-12-09 17:35:25,488 [INFO] Log #5. Appended log to the storage                                                                                                                                                    
master      | 2024-12-09 17:35:25,509 [INFO] Log #5. Secondary URLs to replicate to: ['http://secondary1:8000', 'http://secondary2:8000']                                                                                           
master      | 2024-12-09 17:35:25,510 [INFO] Replication count for message #5 is 1/3
master      | 2024-12-09 17:35:25,510 [INFO] Log #5. Attempting replication to http://secondary1:8000. Attempt 1
master      | 2024-12-09 17:35:25,513 [INFO] Node http://secondary2:8000 is unhealthy. Skipping replication.                                                                                                                        
master      | 2024-12-09 17:35:25,514 [INFO] Waiting for 2.34 seconds before retrying...                                                                                                                                            
secondary1  | 2024-12-09 17:35:25,524 [INFO] Log #5. Simulating replication delay of 1 seconds                                                                                                                                      
secondary1  | 2024-12-09 17:35:26,525 [INFO] Log #5. Replicated to secondary node                                                                                                                                                   
secondary1  | INFO:     172.21.0.4:38640 - "POST /replicate HTTP/1.1" 200 OK
master      | 2024-12-09 17:35:26,574 [INFO] HTTP Request: POST http://secondary1:8000/replicate "HTTP/1.1 200 OK"                                                                                                                  
master      | 2024-12-09 17:35:26,575 [INFO] Replication count for message #5 is 2/3
secondary1  | INFO:     172.21.0.4:38652 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
master      | 2024-12-09 17:35:26,578 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:35:27,858 [INFO] Node http://secondary2:8000 is unhealthy. Skipping replication.                                                                                                                        
master      | 2024-12-09 17:35:27,858 [INFO] Waiting for 6.30 seconds before retrying...
master      | 2024-12-09 17:35:29,574 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:35:29,574 [INFO] Node http://secondary2:8000 is unhealthy
master      | 2024-12-09 17:35:34,165 [INFO] Node http://secondary2:8000 is unhealthy. Skipping replication.                                                                                                                        
master      | 2024-12-09 17:35:34,165 [INFO] Waiting for 15.60 seconds before retrying...
master      | 2024-12-09 17:35:34,318 [INFO] Node http://secondary2:8000 is unhealthy. Skipping replication.                                                                                                                        
master      | 2024-12-09 17:35:34,318 [INFO] Waiting for 17.44 seconds before retrying...
secondary1  | INFO:     172.21.0.4:38376 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
master      | 2024-12-09 17:35:34,662 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"
master      | 2024-12-09 17:35:37,661 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:35:37,661 [INFO] Node http://secondary2:8000 is unhealthy
secondary1  | INFO:     172.21.0.4:54182 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
master      | 2024-12-09 17:35:42,735 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"
master      | 2024-12-09 17:35:45,733 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:35:45,733 [INFO] Node http://secondary2:8000 is unhealthy
secondary2  | 2024-12-09 17:35:46,870 [INFO] Max Replication Delay set to: 1 seconds.                                                                                                                                               
secondary2  | INFO:     Started server process [1]
secondary2  | INFO:     Waiting for application startup.                                                                                                                                                                            
secondary2  | INFO:     Application startup complete.                                                                                                                                                                               
secondary2  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)                                                                                                                                               
master      | 2024-12-09 17:35:49,768 [INFO] Node http://secondary2:8000 is unhealthy. Skipping replication.                                                                                                                        
master      | 2024-12-09 17:35:49,768 [INFO] Waiting for 16.30 seconds before retrying...
secondary1  | INFO:     172.21.0.4:54184 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary2  | INFO:     172.21.0.4:51914 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:35:50,817 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:35:50,820 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:35:50,821 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:35:50,821 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:35:51,763 [INFO] Log #4. Attempting replication to http://secondary2:8000. Attempt 5                                                                                                                    
secondary2  | 2024-12-09 17:35:51,770 [ERROR] Log #4. Simulated error for log replication with 10.0% chance
secondary2  | 2024-12-09 17:35:51,770 [ERROR] Log #4. Unexpected error in replication: 500: Simulated internal server error                                                                                                         
secondary2  | INFO:     172.21.0.4:60442 - "POST /replicate HTTP/1.1" 500 Internal Server Error                                                                                                                                     
master      | 2024-12-09 17:35:51,772 [INFO] HTTP Request: POST http://secondary2:8000/replicate "HTTP/1.1 500 Internal Server Error"                                                                                               
master      | 2024-12-09 17:35:51,772 [WARNING] Log #4. Replication to http://secondary2:8000 failed with status code 500 on attempt 5                                                                                              
master      | 2024-12-09 17:35:51,772 [INFO] Waiting for 30.00 seconds before retrying...                                                                                                                                           
secondary1  | INFO:     172.21.0.4:36200 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary2  | INFO:     172.21.0.4:60458 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:35:55,922 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:35:55,922 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:35:55,923 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:35:55,923 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
secondary1  | INFO:     172.21.0.4:36210 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary2  | INFO:     172.21.0.4:60464 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:36:01,004 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:01,005 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:01,008 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:36:01,008 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:36:06,088 [INFO] Log #5. Attempting replication to http://secondary2:8000. Attempt 5                                                                                                                    
secondary1  | INFO:     172.21.0.4:56468 - "GET /ping HTTP/1.1" 200 OK
secondary2  | INFO:     172.21.0.4:60266 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
master      | 2024-12-09 17:36:06,093 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
secondary2  | 2024-12-09 17:36:06,094 [INFO] Log #5. Simulating replication delay of 1 seconds                                                                                                                                      
master      | 2024-12-09 17:36:06,094 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:06,095 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:36:06,095 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
secondary2  | 2024-12-09 17:36:07,095 [INFO] Log #5. Replicated to secondary node                                                                                                                                                   
secondary2  | INFO:     172.21.0.4:60282 - "POST /replicate HTTP/1.1" 200 OK
master      | 2024-12-09 17:36:07,098 [INFO] HTTP Request: POST http://secondary2:8000/replicate "HTTP/1.1 200 OK"                                                                                                                  
master      | 2024-12-09 17:36:07,101 [INFO] Replication count for message #5 is 3/3                                                                                                                                                
master      | 2024-12-09 17:36:07,101 [INFO] Write concern 3 met. Responding to client.                                                                                                                                             
master      | INFO:     172.21.0.1:45566 - "POST /logs HTTP/1.1" 200 OK                                                                                                                                                             
secondary2  | INFO:     172.21.0.4:60286 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary1  | INFO:     172.21.0.4:56482 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:36:11,158 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:11,159 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:11,159 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:36:11,159 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:36:13,547 [INFO] Received request to list all logs.                                                                                                                                                     
master      | INFO:     172.21.0.1:55018 - "GET /logs HTTP/1.1" 200 OK
secondary1  | INFO:     172.21.0.4:37036 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary2  | INFO:     172.21.0.4:49080 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:36:16,253 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:16,254 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:16,255 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:36:16,255 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
secondary1  | 2024-12-09 17:36:18,465 [INFO] Received request to list all replicated logs.                                                                                                                                          
secondary1  | INFO:     172.21.0.1:39286 - "GET /logs HTTP/1.1" 200 OK
secondary2  | INFO:     172.21.0.4:49090 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary1  | INFO:     172.21.0.4:37048 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:36:21,314 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:21,316 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:21,317 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:36:21,317 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:36:21,773 [INFO] Log #4. Attempting replication to http://secondary2:8000. Attempt 6                                                                                                                    
secondary2  | 2024-12-09 17:36:21,775 [ERROR] Log #4. Simulated error for log replication with 10.0% chance
secondary2  | 2024-12-09 17:36:21,776 [ERROR] Log #4. Unexpected error in replication: 500: Simulated internal server error                                                                                                         
secondary2  | INFO:     172.21.0.4:41134 - "POST /replicate HTTP/1.1" 500 Internal Server Error                                                                                                                                     
master      | 2024-12-09 17:36:21,776 [INFO] HTTP Request: POST http://secondary2:8000/replicate "HTTP/1.1 500 Internal Server Error"                                                                                               
master      | 2024-12-09 17:36:21,777 [WARNING] Log #4. Replication to http://secondary2:8000 failed with status code 500 on attempt 6                                                                                              
master      | 2024-12-09 17:36:21,777 [INFO] Waiting for 30.00 seconds before retrying...                                                                                                                                           
secondary2  | 2024-12-09 17:36:23,465 [INFO] Received request to list all replicated logs.                                                                                                                                          
secondary2  | 2024-12-09 17:36:23,465 [WARNING] Log sequence is incomplete. Missing sequence numbers. Please wait for replication.
secondary2  | INFO:     172.21.0.1:46700 - "GET /logs HTTP/1.1" 500 Internal Server Error                                                                                                                                           
secondary1  | INFO:     172.21.0.4:41906 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary2  | INFO:     172.21.0.4:41144 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:36:26,387 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:26,388 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:26,389 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:36:26,389 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
secondary2  | INFO:     172.21.0.4:41148 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
master      | 2024-12-09 17:36:31,457 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"
secondary1  | INFO:     172.21.0.4:41910 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
master      | 2024-12-09 17:36:31,457 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:31,460 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:36:31,460 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
secondary2  | 2024-12-09 17:36:33,301 [INFO] Received request to list all replicated logs.                                                                                                                                          
secondary2  | 2024-12-09 17:36:33,302 [WARNING] Log sequence is incomplete. Missing sequence numbers. Please wait for replication.
secondary2  | INFO:     172.21.0.1:54566 - "GET /logs HTTP/1.1" 500 Internal Server Error                                                                                                                                           
secondary1  | INFO:     172.21.0.4:41358 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary2  | INFO:     172.21.0.4:56044 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:36:36,534 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:36,536 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:36,537 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:36:36,537 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
secondary2  | INFO:     172.21.0.4:56058 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary1  | INFO:     172.21.0.4:41362 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:36:41,626 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:41,627 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:41,627 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:36:41,628 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
secondary1  | INFO:     172.21.0.4:37818 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary2  | INFO:     172.21.0.4:59336 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:36:46,693 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:46,694 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:46,696 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:36:46,696 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
secondary2  | INFO:     172.21.0.4:59352 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary1  | INFO:     172.21.0.4:37822 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:36:51,758 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:51,759 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:51,759 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:36:51,759 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:36:51,777 [INFO] Log #4. Attempting replication to http://secondary2:8000. Attempt 7                                                                                                                    
secondary2  | 2024-12-09 17:36:51,780 [INFO] Log #4. Simulating replication delay of 1 seconds                                                                                                                                      
secondary2  | 2024-12-09 17:36:52,778 [INFO] Log #4. Replicated to secondary node
secondary2  | INFO:     172.21.0.4:52760 - "POST /replicate HTTP/1.1" 200 OK
master      | 2024-12-09 17:36:52,780 [INFO] HTTP Request: POST http://secondary2:8000/replicate "HTTP/1.1 200 OK"                                                                                                                  
secondary2  | 2024-12-09 17:36:56,793 [INFO] Received request to list all replicated logs.                                                                                                                                          
secondary2  | INFO:     172.21.0.1:57608 - "GET /logs HTTP/1.1" 200 OK
secondary1  | INFO:     172.21.0.4:39496 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary2  | INFO:     172.21.0.4:52776 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:36:56,850 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:56,851 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:36:56,851 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:36:56,852 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
secondary1  | INFO:     172.21.0.4:36346 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
secondary2  | INFO:     172.21.0.4:50004 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:37:01,936 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:37:01,937 [INFO] HTTP Request: GET http://secondary2:8000/ping "HTTP/1.1 200 OK"                                                                                                                        
master      | 2024-12-09 17:37:01,938 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:37:01,938 [INFO] Node http://secondary2:8000 is healthy                                                                                                                                                 
secondary2  | INFO:     Shutting down                                                                                                                                                                                               
secondary2  | INFO:     Waiting for application shutdown.
secondary2  | INFO:     Application shutdown complete.
secondary2  | INFO:     Finished server process [1]                                                                                                                                                                                 
secondary2 exited with code 0
secondary1  | INFO:     172.21.0.4:36360 - "GET /ping HTTP/1.1" 200 OK
master      | 2024-12-09 17:37:07,010 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"
master      | 2024-12-09 17:37:10,009 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:37:10,010 [INFO] Node http://secondary2:8000 is suspected
secondary1  | INFO:     172.21.0.4:47250 - "GET /ping HTTP/1.1" 200 OK                                                                                                                                                              
master      | 2024-12-09 17:37:15,082 [INFO] HTTP Request: GET http://secondary1:8000/ping "HTTP/1.1 200 OK"
master      | 2024-12-09 17:37:18,080 [INFO] Node http://secondary1:8000 is healthy                                                                                                                                                 
master      | 2024-12-09 17:37:18,080 [INFO] Node http://secondary2:8000 is unhealthy
secondary1  | INFO:     Shutting down                                                                                                                                                                                               
secondary1  | INFO:     Waiting for application shutdown.
secondary1  | INFO:     Application shutdown complete.
secondary1  | INFO:     Finished server process [1]                                                                                                                                                                                 
secondary1 exited with code 0
master      | 2024-12-09 17:37:26,150 [INFO] Node http://secondary1:8000 is suspected
master      | 2024-12-09 17:37:26,155 [INFO] Node http://secondary2:8000 is unhealthy
master      | 2024-12-09 17:37:33,989 [WARNING] Master node switched to read-only mode due to insufficient quorum.                                                                                                                  
master      | 2024-12-09 17:37:33,989 [INFO] Master node is in read-only mode, rejecting log append request.
master      | INFO:     172.21.0.1:41676 - "POST /logs HTTP/1.1" 503 Service Unavailable                                                                                                                                            
master      | 2024-12-09 17:37:34,240 [INFO] Node http://secondary1:8000 is unhealthy                                                                                                                                               
master      | 2024-12-09 17:37:34,240 [INFO] Node http://secondary2:8000 is unhealthy
```