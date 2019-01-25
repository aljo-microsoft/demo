__author__ = "Alexander Johnson"
__email__ = "aljo-microsoft@github.com"
__status__ = "Development"

import json
import os
from pathlib import Path
from subprocess import PIPE
from subprocess import Popen
import sys
import zipfile

def sfpkg_staging(self): 
        # Create app_v1.0.sfpkg
        # Create Storage Account
        # Get Connection String to Storage Account
        # Create Storage Account Blob Container
        # Upload SF Packge to Account blob
        # Get Public url to file in storage account blob
        app_package_name = "app_v1.0.sfpkg"
        app_package_path = "minecraftPkg"
        storage_account_name = "mcraftstorage"
        deployment_resource_group = "mcraftdeployrg"
        location = "westus"
        container_name "mcraftcontainer"
        parameters_file = "AzureDeploy.parameters.json"
        
        print("Staging SFPKG")

        # Use Public URL instead of creating one
        # Create Storate
        create_storage_process = Popen(["az", "storage", "account", "create", "-n", storage_account_name, "-g", deployment_resource_group, "-l", location, "--sku", "Standard_LRS"], stdout=PIPE, stderr=PIPE)

        stdout, stderr = create_storage_process.communicate()

        if create_storage_process.wait() == 0:
            print("Storage Account Created")
        else:
            sys.exit(stderr)

        # Get Connection String
        connection_string_process = Popen(["az", "storage", "account", "show-connection-string", "-g", deployment_resource_group, "-n", storage_account_name], stdout=PIPE, stderr=PIPE)

        stdout, stderr = connection_string_process.communicate()

        if connection_string_process.wait() == 0:
            connection_string = str(json.loads(stdout.decode("utf-8"))['connectionString'])
            print("Got Storage Connection String")
        else:
            sys.exit(stderr)

        # Create Blob Container
        create_container_process = Popen(["az", "storage", "container", "create", "--name", container_name, "--connection-string", connection_string, "--public-access", "container"], stdout=PIPE, stderr=PIPE)

        stdout, stderr = create_container_process.communicate()

        if create_container_process.wait() == 0:
            print("Blob Container Created")
        else:
            sys.exit(stderr)

        # Zip SFPKG to Upload to Blob Container
        sfpkg = zipfile.ZipFile(app_package_name, 'w', zipfile.ZIP_DEFLATED)
        package_length = len(app_package_path)

        for root, dirs, files in os.walk(app_package_path):
            root_folder = root[package_length:]
            for file in files:
                sfpkg.write(os.path.join(root, file), os.path.join(root_folder, file))

        sfpkg.close()

        # Upload SFPKG to Blob Container
        upload_sfpkg_process = Popen(["az", "storage", "blob", "upload", "--file", app_package_name, "--name", app_package_name, "--connection-string", connection_string, "--container-name", container_name], stdout=PIPE, stderr=PIPE)

        stdout, stderr = upload_sfpkg_process.communicate()
        
        
        # Get URL for SFPKG in Storage Account Blob Container
        url_sfpkg_process = Popen(["az", "storage", "blob", "url", "--container-name", self.container_name, "--connection-string", connection_string, "--name", self.microservices_app_package_name], stdout=PIPE, stderr=PIPE)

        stdout, stderr = url_sfpkg_process.communicate()

        if upload_sfpkg_process.wait() == 0:
            print("Uploaded SFPKG To Storage Account Blob Container")
            app_package_url = stdout.decode("utf-8").replace('\n', '').replace('"', '')
        else:
            sys.exit(stderr)

        # Update Parameters File
        parameters_file_json = json.load(open(parameters_file, 'r'))
        
        parameters_file_json['parameters']['sfpkg_url_0']['value'] = app_package_url
        json.dump(parameters_file_json, open(parameters_file, 'w'))

def main():
    sfpkg_staging() 

if __name__ == '__main__':
    main()
