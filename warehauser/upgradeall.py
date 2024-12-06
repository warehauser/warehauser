import subprocess
import json

try:
    # Get outdated packages in JSON format
    result = subprocess.check_output(['pip', 'list', '--outdated', '--format=json'], text=True)
    outdated_packages = json.loads(result)

    # Extract package names
    package_names = [pkg['name'] for pkg in outdated_packages]

    # Upgrade each package
    for package in package_names:
        print(f"Upgrading {package}...")
        subprocess.run(['pip', 'install', '--upgrade', package], check=True)

    print("All packages have been upgraded.")

except subprocess.CalledProcessError as e:
    print(f"Error: {e}")
