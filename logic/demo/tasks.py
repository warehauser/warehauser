# tasks.py

from ...core.models import *
from ...core.serializers import *

# Define your process logic here.

# How to create a task:
#
# 1. Create a Client <clientname> (see python manage.py authtool client create -h)
# 2. Create a module logic.<clientname> in <warehauser base dir>/logic/<clientname>/:
#       * add a __init__.py empty file, and
#       * add a tasks.py file and copy the contents of this template into that file.
# 3. Tasks take the form of:
#
#       def <your task name>(event: Event):
#           # Your code here...
#           pass
#
# 4. Create an EventDef with the proc_name = 'logic.<clientnamne>.tasks.<your task name|my_event_process>' using the appropriate warehauser API (default is POST /api/eventdefs/).
# 5. Create an Event via its <EventDef> using the appropriate warehauser API (default is POST /api/eventdefs/<id>/do_spawn/).
# 6. If the Event.is_batched is False then the <your task name> function will be
#    executed immediately. Otherwise it will be executed when Event.process()
#    is called.
#
# NOTE: the warehauser/scheduler.py can schedule an EventQueueThread which will
#    process unprocessed Events that are is_batched True

def my_event_process(event:Event):
    pass
