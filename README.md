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
docker-compose up
```

The **Replicated Log** allows you to append log messages to a Master node, which then asynchronously replicates these logs to multiple Secondary nodes. This ensures data consistency and reliability across your distributed system. Below are detailed instructions and examples on how to interact with the system using HTTP requests.

### 2. Append a Log Entry

To append a new log message to the system, send a `POST` request to the Master's `/logs` endpoint with the log message in the request body.

**Request:**

```bash
curl -X POST "http://localhost:8000/logs" \
     -H "Content-Type: application/json" \
     -d '{"message": "This is a test log entry."}'
```
**Response Example :**

```json
{
  "status": "success",
  "log": {
    "id": 1,
    "message": "This is a test log entry."
  }
}
```

### 3. Listing Logs

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
    "id": 1,
    "message": "System initialization complete."
  },
  {
    "id": 2,
    "message": "User login successful."
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
    "id": 1,
    "message": "System initialization complete."
  },
  {
    "id": 2,
    "message": "User login successful."
  }
]
```

**Note:**
Replace 8001 with the appropriate port number if you have additional Secondary nodes (e.g., 8002, 8003, etc.).