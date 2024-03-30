# Copyright 2024 stingermissile @ github.com

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# scheduler.py

import sys
import os
import schedule
import time
import django

# Add the directory containing your Django project to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Manually set the DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'warehauser.settings')

# Initialize Django
django.setup()

import tasks

# Set schedule for tasks
cron = [
    schedule.every().day.at("00:00").do(lambda: tasks.ArchiverThread().start()),
    schedule.every().day.at("17:00").do(lambda: tasks.GenerateReportsThread().start()),
    schedule.every(1).minutes.do(lambda: tasks.EventQueueThread().start()),
    schedule.every(1).minutes.do(lambda: tasks.GarbageCollectorThread().start()),
]

def main():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        schedule.clear()
