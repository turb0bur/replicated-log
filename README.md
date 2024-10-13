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

## Example of docker-compose logs

```bash
master      | 2024-10-13 20:43:11,960 [INFO] Log #1. Received log entry request: async log entry.                                                                                   
master      | 2024-10-13 20:43:11,960 [INFO] Log #1. Appended log to the storage
master      | 2024-10-13 20:43:11,960 [INFO] Log #1. Secondary URLs to replicate to: ['http://secondary1:8000/replicate', 'http://secondary2:8000/replicate']                       
master      | 2024-10-13 20:43:11,960 [INFO] Replication count for message #1 is 1/2                                                                                                
master      | 2024-10-13 20:43:11,961 [INFO] Log #1. Attempting replication to http://secondary1:8000/replicate. Attempt 1/3                                                        
master      | 2024-10-13 20:43:11,967 [INFO] Log #1. Attempting replication to http://secondary2:8000/replicate. Attempt 1/3                                                        
secondary2  | 2024-10-13 20:43:11,976 [INFO] Log #1. Simulating replication delay of 7 seconds                                                                                      
secondary1  | 2024-10-13 20:43:11,978 [INFO] Log #1. Simulating replication delay of 10 seconds                                                                                     
secondary2  | 2024-10-13 20:43:18,978 [INFO] Log #1. Replicated to secondary node                                                                                                   
secondary2  | INFO:     172.23.0.4:50732 - "POST /replicate HTTP/1.1" 200 OK
master      | 2024-10-13 20:43:18,979 [INFO] HTTP Request: POST http://secondary2:8000/replicate "HTTP/1.1 200 OK"                                                                  
master      | 2024-10-13 20:43:18,980 [INFO] Replication count for message #1 is 2/2                                                                                                
master      | 2024-10-13 20:43:18,980 [INFO] Write concern 2 met. Responding to client.                                                                                             
master      | INFO:     172.23.0.1:51744 - "POST /logs HTTP/1.1" 200 OK                                                                                                             
master      | 2024-10-13 20:43:21,976 [ERROR] Log #1. Replication to http://secondary1:8000/replicate encountered an error on attempt 1:                                            
master      | 2024-10-13 20:43:21,976 [INFO] Log #1.Waiting for 10.0 seconds before next replication attempt to http://secondary1:8000/replicate
secondary1  | 2024-10-13 20:43:21,979 [INFO] Log #1. Replicated to secondary node                                                                                                   
master      | 2024-10-13 20:43:27,601 [INFO] Log #2. Received log entry request: async log entry.                                                                                   
master      | 2024-10-13 20:43:27,601 [INFO] Log #2. Appended log to the storage
master      | 2024-10-13 20:43:27,602 [INFO] Log #2. Secondary URLs to replicate to: ['http://secondary1:8000/replicate', 'http://secondary2:8000/replicate']                       
master      | 2024-10-13 20:43:27,602 [INFO] Replication count for message #2 is 1/3                                                                                                
master      | 2024-10-13 20:43:27,602 [INFO] Log #2. Attempting replication to http://secondary1:8000/replicate. Attempt 1/3                                                        
master      | 2024-10-13 20:43:27,602 [INFO] Log #2. Attempting replication to http://secondary2:8000/replicate. Attempt 1/3                                                        
secondary1  | 2024-10-13 20:43:27,607 [INFO] Log #2. Simulating replication delay of 5 seconds                                                                                      
secondary2  | 2024-10-13 20:43:27,607 [INFO] Log #2. Simulating replication delay of 5 seconds                                                                                      
master      | 2024-10-13 20:43:31,977 [INFO] Log #1. Attempting replication to http://secondary1:8000/replicate. Attempt 2/3                                                        
secondary1  | 2024-10-13 20:43:31,982 [INFO] Log #1. Simulating replication delay of 7 seconds
secondary1  | 2024-10-13 20:43:32,607 [INFO] Log #2. Replicated to secondary node                                                                                                   
secondary1  | INFO:     172.23.0.4:41448 - "POST /replicate HTTP/1.1" 200 OK
secondary2  | 2024-10-13 20:43:32,608 [INFO] Log #2. Replicated to secondary node                                                                                                   
secondary2  | INFO:     172.23.0.4:49468 - "POST /replicate HTTP/1.1" 200 OK                                                                                                        
master      | 2024-10-13 20:43:32,609 [INFO] HTTP Request: POST http://secondary1:8000/replicate "HTTP/1.1 200 OK"                                                                  
master      | 2024-10-13 20:43:32,610 [INFO] HTTP Request: POST http://secondary2:8000/replicate "HTTP/1.1 200 OK"                                                                  
master      | 2024-10-13 20:43:32,611 [INFO] Replication count for message #2 is 2/3                                                                                                
master      | 2024-10-13 20:43:32,611 [INFO] Replication count for message #2 is 3/3                                                                                                
master      | 2024-10-13 20:43:32,611 [INFO] Write concern 3 met. Responding to client.                                                                                             
master      | INFO:     172.23.0.1:39812 - "POST /logs HTTP/1.1" 200 OK                                                                                                             
master      | 2024-10-13 20:43:38,473 [INFO] Log #3. Received log entry request: async log entry.                                                                                   
master      | 2024-10-13 20:43:38,473 [INFO] Log #3. Appended log to the storage
master      | 2024-10-13 20:43:38,474 [INFO] Log #3. Secondary URLs to replicate to: ['http://secondary1:8000/replicate', 'http://secondary2:8000/replicate']                       
master      | 2024-10-13 20:43:38,474 [INFO] Replication count for message #3 is 1/1                                                                                                
master      | 2024-10-13 20:43:38,474 [INFO] Write concern 1 met. Responding immediately.                                                                                           
master      | INFO:     172.23.0.1:55350 - "POST /logs HTTP/1.1" 200 OK                                                                                                             
master      | 2024-10-13 20:43:38,474 [INFO] Log #3. Attempting replication to http://secondary1:8000/replicate. Attempt 1/3                                                        
master      | 2024-10-13 20:43:38,475 [INFO] Log #3. Attempting replication to http://secondary2:8000/replicate. Attempt 1/3                                                        
secondary2  | 2024-10-13 20:43:38,479 [INFO] Log #3. Simulating replication delay of 10 seconds                                                                                     
secondary1  | 2024-10-13 20:43:38,479 [INFO] Log #3. Simulating replication delay of 9 seconds                                                                                      
secondary1  | 2024-10-13 20:43:38,984 [INFO] Log #1. Replicated to secondary node                                                                                                   
secondary1  | INFO:     172.23.0.4:41458 - "POST /replicate HTTP/1.1" 200 OK
master      | 2024-10-13 20:43:38,985 [INFO] HTTP Request: POST http://secondary1:8000/replicate "HTTP/1.1 200 OK"                                                                  
secondary1  | 2024-10-13 20:43:47,480 [INFO] Log #3. Replicated to secondary node                                                                                                   
secondary1  | INFO:     172.23.0.4:46572 - "POST /replicate HTTP/1.1" 200 OK
master      | 2024-10-13 20:43:47,483 [INFO] HTTP Request: POST http://secondary1:8000/replicate "HTTP/1.1 200 OK"                                                                  
master      | 2024-10-13 20:43:48,480 [ERROR] Log #3. Replication to http://secondary2:8000/replicate encountered an error on attempt 1:                                            
master      | 2024-10-13 20:43:48,480 [INFO] Log #3.Waiting for 10.0 seconds before next replication attempt to http://secondary2:8000/replicate
secondary2  | 2024-10-13 20:43:48,480 [INFO] Log #3. Replicated to secondary node                                                                                                   
master      | 2024-10-13 20:43:58,482 [INFO] Log #3. Attempting replication to http://secondary2:8000/replicate. Attempt 2/3                                                        
secondary2  | 2024-10-13 20:43:58,489 [INFO] Log #3. Simulating replication delay of 7 seconds
secondary2  | INFO:     172.23.0.4:43080 - "POST /replicate HTTP/1.1" 200 OK                                                                                                        
secondary2  | 2024-10-13 20:44:05,490 [INFO] Log #3. Replicated to secondary node
master      | 2024-10-13 20:44:05,491 [INFO] HTTP Request: POST http://secondary2:8000/replicate "HTTP/1.1 200 OK"                                                                  
master      | 2024-10-13 20:44:13,932 [INFO] Received request to list all logs.                                                                                                     
master      | INFO:     172.23.0.1:55106 - "GET /logs HTTP/1.1" 200 OK
secondary1  | 2024-10-13 20:44:21,814 [INFO] Received request to list all replicated logs.                                                                                          
secondary1  | INFO:     172.23.0.1:40012 - "GET /logs HTTP/1.1" 200 OK
secondary2  | 2024-10-13 20:44:30,512 [INFO] Received request to list all replicated logs.                                                                                          
secondary2  | INFO:     172.23.0.1:47872 - "GET /logs HTTP/1.1" 200 OK
```