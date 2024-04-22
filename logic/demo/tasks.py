# tasks.py

from ...core.models import *
from ...core.serializers import *

# Define your process logic here.

# How to create a task:
#
# 1. Rename this file to core/tasks.py (remove the .git extension).
#
# 2. Tasks take the form of:
#
#    def <your task name>(event: Event):
#       # Your code here...
#       pass
#
# 3. create an EventDef with the proc_name = '<your task name>' using the appropriate warehauser API (default is POST /api/eventdefs/).
# 4. create an Event via its <EventDef> using the appropriate warehauser API (default is POST /api/eventdefs/<id>/do_spawn/).
# 5. if the Event.is_batched is False then the <your task name> function will be
#    executed immediately. Otherwise it will be executed when Event.process()
#    is called.
#
# NOTE: the warehauser/scheduler.py can schedule an EventQueueThread which will
#    process unprocessed Events that are is_batched True

def my_event_process(event:Event):
    pass
