# Server Installer and Manager

A Python script designed for remote management and monitoring of Linux servers over SSH. This script enables streamlined installation, configuration, monitoring, and backup of various services (e.g., databases, web servers) and provides server health summaries. HTTPS can also be set up with Certbot for secure web services.



## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation Guide](#installation-guide)
4. [Usage](#usage)

## Features

- **Robust SSH Connection Management**: Handles SSH connections with retry logic and logging for errors.
- **Health Monitoring Dashboard**: Displays uptime, disk usage, and the status of essential services in a formatted table.
- **Service Monitoring & Alerts**: Monitors critical services (e.g., nginx, MySQL) and triggers alerts if any service is inactive or disk usage is high.
- **Automated HTTPS Configuration**: Simplifies HTTPS setup with Certbot for `nginx` and `apache` servers, including HTTP to HTTPS redirection.
- **Backup & Log Management**: Provides options to back up configurations and view recent logs for diagnostics.
- **Performance Monitoring**: Monitors CPU and memory usage of key services, allowing identification of resource-intensive processes.

## Prerequisites

- **Python 3.x**
- **pip** (Python package installer)
- **sudo** privileges on the remote server (if using commands that require elevated permissions)
- **SSH access** enabled on the server

## Installation Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/ServerInstaller.git
cd ServerInstaller
```
### Step 2: Set Up a Virtual Environment
1. Create the virtual environment:
   ```bash
   python3 -m venv venv
   ```
2. Activate the virtual environment
   - On Linux/macOS
     ```bash
     source venv/bin/activate
     ```
   - On Windows
     ```bash
     venv\Scripts\activate
     ```
### Step 3: Install Required Packages
```bash
pip install -r requirements.txt
```

## Usage
```bash
python server_installer.py
```




