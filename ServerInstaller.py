import paramiko  # Import paramiko for SSH connections
import logging
import re
from tabulate import tabulate  # Importing tabulate for table formatting
import time

# Set up logging
logging.basicConfig(filename="server_installer.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


# Function to display the ASCII logo
def display_logo():
    logo = """
  _____    _____   ______     __    __    _____   ______                                          
 / ____\  / ___/  (   __ \    ) )  ( (   / ___/  (   __ \                                         
( (___   ( (__     ) (__) )  ( (    ) ) ( (__     ) (__) )                                        
 \___ \   ) __)   (    __/    \ \  / /   ) __)   (    __/                                         
     ) ) ( (       ) \ \  _    \ \/ /   ( (       ) \ \  _                                        
 ___/ /   \ \___  ( ( \ \_))    \  /     \ \___  ( ( \ \_))                                       
/____/     \____\  )_) \__/      \/       \____\  )_) \__/                                        

  _____      __      _    _____   ________     ____     _____       _____        _____   ______   
 (_   _)    /  \    / )  / ____\ (___  ___)   (    )   (_   _)     (_   _)      / ___/  (   __ \  
   | |     / /\ \  / /  ( (___       ) )      / /\ \     | |         | |       ( (__     ) (__) ) 
   | |     ) ) ) ) ) )   \___ \     ( (      ( (__) )    | |         | |        ) __)   (    __/  
   | |    ( ( ( ( ( (        ) )     ) )      )    (     | |   __    | |   __  ( (       ) \ \  _ 
  _| |__  / /  \ \/ /    ___/ /     ( (      /  /\  \  __| |___) ) __| |___) )  \ \___  ( ( \ \_))
 /_____( (_/    \__/    /____/      /__\    /__(  )__\ \________/  \________/    \____\  )_) \__/ 
"""
    print(logo)


# Function to establish SSH connection
def connect_to_server(host, username, password=None, key_file=None, retries=3):
    """Try connecting to the server with retries in case of failure."""
    attempt = 0
    while attempt < retries:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if key_file:
                client.connect(host, username=username, key_filename=key_file)
            else:
                client.connect(host, username=username, password=password)
            client.get_transport().set_keepalive(30)
            print("Connected to server successfully.")
            logging.info("Connected to server.")
            return client
        except Exception as e:
            print(f"Failed to connect (Attempt {attempt + 1}/{retries}): {e}")
            logging.error(f"Connection attempt {attempt + 1} failed: {e}")
            attempt += 1
            time.sleep(2 ** attempt)  # Exponential backoff
    print("All connection attempts failed. Please check your network or server status.")
    return None


# Execute a command on the server and handle sudo with password input
def execute_command(client, command, host, username, password="", description=""):
    """Execute a command on the server with error handling and re-run options."""
    try:
        if "sudo" in command:
            command = f"echo {password} | sudo -S bash -c \"{command}\""
        stdin, stdout, stderr = client.exec_command(command)
        if password:
            stdin.write(password + '\n')
            stdin.flush()

        output = stdout.read().decode()
        error = stderr.read().decode()

        if error:
            logging.error(f"{description} Error: {error}")
            print(f"Command '{command}' failed with error: {error}")
            retry = input("Would you like to retry this command? (yes/no): ").lower()
            if retry == 'yes':
                return execute_command(client, command, host, username, password, description)

        return output, error

    except (paramiko.SSHException, ConnectionResetError) as e:
        print(f"Connection error during command execution: {e}. Retrying...")
        logging.error(f"Connection error: {e}")
        client.connect(host, username=username, password=password)
        time.sleep(1)
        return execute_command(client, command, host, username, password, description)


# Dashboard to display server health and summary
def display_dashboard(client):
    """Display server status summary including uptime, disk usage, and installed packages in table format."""
    print("\n--- Server Status Summary ---")

    # Server Uptime
    uptime, _ = execute_command(client, "uptime -p", "", "Fetching server uptime")
    uptime_data = [["Uptime", uptime.strip()]]
    print(tabulate(uptime_data, headers=["Metric", "Value"], tablefmt="fancy_grid"))

    # Disk Usage
    disk_usage, _ = execute_command(client, "df -h --output=source,fstype,size,used,avail,pcent /", "",
                                    "Checking disk usage")
    print("\nDisk Usage:")
    print(tabulate([line.split() for line in disk_usage.splitlines()], headers="firstrow", tablefmt="fancy_grid"))

    # Installed Services Summary
    services = ["nginx", "apache2", "mysql", "postgresql", "mongodb", "docker"]
    service_status_data = []
    for service in services:
        if is_installed(client, service):
            status, _ = execute_command(client, f"systemctl is-active {service}", "", f"Checking status of {service}")
            service_status_data.append([service.capitalize(), "Active" if "active" in status else "Inactive"])
        else:
            service_status_data.append([service.capitalize(), "Not Installed"])

    print("\nService Status:")
    print(tabulate(service_status_data, headers=["Service", "Status"], tablefmt="fancy_grid"))
    print("-----------------------------\n")


# Validate if input is a valid domain name
def validate_domain(domain):
    """Validate that the input is a proper domain name format."""
    pattern = re.compile(r"^(?!\-)([A-Za-z0-9\-]{1,63}\.)+[A-Za-z]{2,6}$")
    if not pattern.match(domain):
        print("Invalid domain format. Please enter a valid domain name (e.g., example.com).")
        return False
    return True


# Check if package is installed
def is_installed(client, package_name):
    """Check if a package is already installed on the server."""
    check_command = f"dpkg -l | grep {package_name}"
    output, _ = execute_command(client, check_command, "", f"Checking if {package_name} is installed")
    return package_name in output


# Confirm action prompt
def confirm_action(action, software):
    """Ask for user confirmation before proceeding with installation/uninstallation."""
    confirm = input(f"Are you sure you want to {action} {software}? (yes/no): ").lower()
    return confirm == "yes"


# Backup specified services
def backup_service(client, service, password):
    """Create a backup of specified services like databases or configuration files."""
    backup_commands = {
        "mysql": "mysqldump --all-databases > /root/mysql_backup.sql",
        "postgresql": "pg_dumpall > /root/postgres_backup.sql",
        "nginx": "tar -czvf /root/nginx_backup.tar.gz /etc/nginx",
        "apache": "tar -czvf /root/apache_backup.tar.gz /etc/apache2"
    }

    if service in backup_commands:
        print(f"Creating backup for {service}...")
        execute_command(client, f"echo {password} | sudo -S bash -c \"{backup_commands[service]}\"", password,
                        f"Backing up {service}")
        print(f"Backup for {service} completed and saved to /root/")
    else:
        print(f"No backup option available for {service}.")


# View service logs
def view_logs(client, service, lines=50):
    """Fetch and display the last few lines of logs for specified services."""
    log_files = {
        "nginx": "/var/log/nginx/error.log",
        "apache": "/var/log/apache2/error.log",
        "mysql": "/var/log/mysql/error.log",
        "postgresql": "/var/log/postgresql/postgresql-12-main.log",
        "docker": "/var/log/docker.log"
    }

    if service in log_files:
        command = f"tail -n {lines} {log_files[service]}"
        logs, _ = execute_command(client, command, "", f"Fetching logs for {service}")
        print(f"\n--- {service.capitalize()} Logs ---\n{logs}")
    else:
        print(f"No log viewing available for {service}.")


# Monitor critical services
def monitor_services(client):
    """Monitor services and send alerts if any service is down or if disk space is low."""
    critical_services = ["nginx", "apache2", "mysql", "postgresql"]
    for service in critical_services:
        status, _ = execute_command(client, f"systemctl is-active {service}", "", f"Checking status of {service}")
        if "inactive" in status:
            print(f"Alert: {service} is down! Please check.")

    # Check for low disk space
    disk_usage, _ = execute_command(client, "df -h / | grep -v Filesystem | awk '{print $5}'", "",
                                    "Checking disk usage")
    match = re.search(r'\d+', disk_usage)
    if match:
        usage_percentage = int(match.group())
        if usage_percentage > 80:  # Example threshold at 80%
            print("Alert: Disk space usage is above 80%!")
    else:
        print("Could not determine disk usage.")


# Monitor CPU and memory usage
def monitor_performance(client):
    """Monitor CPU and memory usage of key services."""
    services = ["nginx", "apache2", "mysql", "docker"]
    print("\n--- Service Performance ---")
    print(f"{'Service':<10} {'CPU %':<6} {'Memory %':<8}")
    for service in services:
        command = f"ps -C {service} -o %cpu,%mem --no-headers"
        output, _ = execute_command(client, command, "", f"Monitoring performance of {service}")

        output_lines = output.strip().splitlines()
        if output_lines:
            total_cpu, total_mem = 0.0, 0.0
            for line in output_lines:
                values = line.split()
                if len(values) >= 2:
                    try:
                        cpu, mem = float(values[0]), float(values[1])
                        total_cpu += cpu
                        total_mem += mem
                    except ValueError:
                        print(f"Warning: Could not parse CPU and memory for {service}.")
                        continue
            print(f"{service:<10} {total_cpu:<6.2f} {total_mem:<8.2f}")
        else:
            print(f"{service:<10} {'N/A':<6} {'N/A':<8}")
    print("---------------------------\n")


# Configure HTTPS with Certbot
def configure_https(client, server_type, domain, password):
    """Configure HTTPS using Certbot and redirect HTTP to HTTPS."""
    if server_type == "nginx":
        certbot_command = f"certbot --nginx -d {domain} -d www.{domain}"
    elif server_type == "apache":
        certbot_command = f"certbot --apache -d {domain} -d www.{domain}"
    else:
        print("Invalid server type. Only 'nginx' and 'apache' are supported.")
        return

    # Execute Certbot command to configure HTTPS
    execute_command(client, certbot_command, password, f"Configuring HTTPS for {domain}")

    # Test automatic renewal setup
    renew_test_command = "certbot renew --dry-run"
    execute_command(client, renew_test_command, password, "Testing Certbot auto-renewal")


# Main function
def main():
    display_logo()
    print("Welcome to the Server Software Installer and Uninstaller!")
    print("This script allows you to install or uninstall databases, web servers, and other common server software.")
    print("It also sets up HTTPS with Certbot for your domain.")
    print("Please ensure you have the server's IP address, username, password, and optionally a domain name.\n")

    # Get server connection details
    host = input("Enter server IP: ")
    username = input("Enter server username: ")
    password = input("Enter server password: ")
    domain = input("Enter your domain (or press Enter to skip HTTPS setup): ").strip()

    if domain and not validate_domain(domain):
        return

    # Connect to the server
    client = connect_to_server(host, username, password)
    if not client:
        print("Connection to server failed. Please check your credentials and try again.")
        return

    display_dashboard(client)

    while True:
        action = input(
            "\nChoose action (install/uninstall/configure_https/dashboard/logs/backup/monitor/exit): ").lower()
        if action == "install":
            print("Installation options...")
        elif action == "dashboard":
            display_dashboard(client)
        elif action == "backup":
            backup_service(client, "nginx", password)
        elif action == "logs":
            view_logs(client, "nginx")
        elif action == "monitor":
            monitor_services(client)
            monitor_performance(client)
        elif action == "configure_https":
            if domain:
                server_type = input("Enter the web server type (nginx/apache): ").lower()
                configure_https(client, server_type, domain, password)
            else:
                print("HTTPS configuration skipped because no domain was provided.")
        elif action == "exit":
            print("Exiting the script.")
            client.close()
            break
        else:
            print("Invalid action. Please choose a valid option.")


if __name__ == "__main__":
    main()
