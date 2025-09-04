#!/bin/bash

sudo apt-get update
sudo apt-get install -y curl wget git

echo "Installing admin_Inventarsystem..."
# Clone the repository to /var
git clone https://github.com/AIIrondev/admin_Inventarsystem.git /opt/admin_Inventarsystem || {
    echo "Failed to clone repository to /opt/admin_Inventarsystem. Exiting."
    exit 1
}

cd /opt/admin_Inventarsystem
# Check if the start.sh script exists
if [ ! -f "./start.sh" ]; then
    echo "start.sh script not found in /opt/admin_Inventarsystem"
    exit 1
fi

# Make the script executable
chmod +x ./start.sh

echo "========================================================"
echo "                  INSTALLATION COMPLETE                 "
echo "========================================================"

cd /opt/admin_Inventarsystem
# Run the script
# Ask the user if they want to run the script now
echo "Running the script now..."
./start.sh
if [ $? -ne 0 ]; then
    echo "Failed to run the script. Please check the logs for more details."
    exit 1
fi
echo "Script executed successfully!"

echo "========================================================"
echo "              AUTOSTART INSTALLATION COMPLETED          "
echo "========================================================"
