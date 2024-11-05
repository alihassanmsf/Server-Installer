# Server Installer and Manager

This script allows remote management of servers via SSH. You can install, configure, monitor, and back up various services like databases and web servers. It also provides server health monitoring and can set up HTTPS using Certbot.

## Features
- SSH connection handling with retries and error logging
- Command execution with sudo support and retry prompts
- Server monitoring dashboard for uptime, disk usage, and service statuses
- HTTPS setup using Certbot for nginx and apache servers
- Backup, log viewing, and performance monitoring for key services

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/ServerInstaller.git
   cd ServerInstaller
