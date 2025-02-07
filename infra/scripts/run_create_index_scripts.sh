#!/bin/bash
echo "started the script"

# Variables
baseUrl="$1"
keyvaultName="$2"
requirementFile="requirements.txt"
requirementFileUrl=${baseUrl}"infra/scripts/index_scripts/requirements.txt"

echo "Script Started"

# Download the create_index and create table python files

# RUN apt-get update
# RUN apt-get install python3 python3-dev g++ unixodbc-dev unixodbc libpq-dev
# apk add python3 python3-dev g++ unixodbc-dev unixodbc libpq-dev
 
# # RUN apt-get install python3 python3-dev g++ unixodbc-dev unixodbc libpq-dev
# pip install pyodbc

# Download the requirement file
curl --output "$requirementFile" "$requirementFileUrl"

echo "Download completed"

#Replace key vault name 
sed -i "s/kv_to-be-replaced/${keyvaultName}/g" "01_create_search_index.py"
sed -i "s/kv_to-be-replaced/${keyvaultName}/g" "02_create_cu_template_text.py"
sed -i "s/kv_to-be-replaced/${keyvaultName}/g" "02_create_cu_template_audio.py"
sed -i "s/kv_to-be-replaced/${keyvaultName}/g" "03_cu_process_data_text.py"

pip install -r requirements.txt

python 01_create_search_index.py
python 02_create_cu_template_text.py
python 02_create_cu_template_audio.py
python 03_cu_process_data_text.py
