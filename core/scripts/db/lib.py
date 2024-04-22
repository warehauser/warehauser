# Copyright 2024 warehauser @ github.com

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# core/scripts/lib.py

import os
import csv
import logging
import re
import json

from datetime import datetime
from core.models import *

def upload_data_from_csv(csv_file, model_name):
    if not os.path.isfile(csv_file):
        logging.error(f"{csv_file} is not a valid file.")
        return False

    model = apps.get_model("core", model_name)
    logging.info(f'Loading data for model {model.__module__}.{model.__name__}.')

    fields = {}
    model_fields = model._meta.get_fields()
    for field in model_fields:
        typ = field.__class__.__name__
        if not (typ == 'ManyToOneRel' or
                typ == 'ManyToManyField' or
                field.name == 'created_at' or
                field.name == 'updated_at'):
            fields[field.name] = {"class": typ, "null": field.null, "blank": field.blank}

    recs = []
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            logging.debug(f'Read in row: {row}')
            rec = {}
            for key, val in row.items():
                # if this key is not in fields then continue
                if not key in fields or val.lower() == 'none' or val.lower() == 'null':
                    continue

                logging.debug(f"Processing key: {key}, value: {val}")

                # if this field is a JSONField then we need to process the val into a json object
                if fields[key]['class'] == 'JSONField':
                    try:
                        rec[key] = json.loads(val)
                    except json.JSONDecodeError as e:
                        logging.error(f"decoding JSON: {e}")
                        rec[key] = None
                        raise e
                # if the field is a ForeignKey and the value is of the form <REC:\d+> then this is
                # refering to a PREVIOUSLY listed row/record
                elif fields[key]['class'] == 'ForeignKey':
                    if re.match(rf'<REC:\d+>', val):
                        index = int(val.split(sep=":")[1].split(">")[0])-2
                        if index < 0 or index > len(recs) - 1:
                            continue
                        obj = recs[index]
                        rec[key + '_id'] = obj.id
                    else:
                        rec[key + '_id'] = val
                else:
                    rec[key] = val

            logging.debug(f'record: {rec}')

            obj = model.objects.create(**rec)
            recs.append(obj)

        logging.info(f"Data from {csv_file} uploaded successfully.")
        return True

def search_for_data_and_upload(data_dir, archive=True):
    for filename in os.listdir(data_dir):
        if filename.endswith(".csv") and not os.path.isdir(filename):
            model_name = os.path.splitext(filename)[0]
            csv_file_path = os.path.join(data_dir, filename)
            if upload_data_from_csv(csv_file_path, model_name):
                if archive:
                    archive_csv_file(filename)

def archive_csv_file(filename):
        date_time_suffix = datetime.now().strftime("%Y%m%d%H%M%S")
        new_file_path = f"{filename}.{date_time_suffix}"
        os.rename(filename, new_file_path)
        logging.info(f"File {filename} renamed to {new_file_path}")

def reset_csv_files(directory):
    # Iterate over files in the directory
    logging.info('Searching in ' + directory + '.')
    for filename in os.listdir(directory):
        logging.debug(f'{filename}')
        if re.match(rf"\w+\.csv\.\d+$", filename):
            logging.debug(f'Found candidate {filename}.')

            # Extract the numeric suffix using regular expression
            match = re.search(r'\d+$', filename)
            if match:
                numeric_suffix = match.group()
                new_filename = filename.replace(numeric_suffix, "")
                os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
                logging.info(f"Renamed {filename} to {new_filename}")
