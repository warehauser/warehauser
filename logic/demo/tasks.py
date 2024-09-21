# tasks.py

import logging

from django.utils.translation import gettext as _

from core.models import *
from core.serializers import *

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

logger = logging.getLogger(__name__)

class magic_warehause_callback(WarehauseCallback):
    def pre_dispatch(self, model, dfn, quantity):
        super().pre_dispatch(model, dfn, quantity)
        existing = model.stock.filter(parent__isnull=True, dfn=dfn, quantity__gte=0.0)
        if existing.exists():
            existing = existing.first()
            existing.quantity += quantity
            existing.save()
        else:
            data = {
                'quantity': quantity,
                'warehause': model,
            }

            dfn.create_instance(data=data)

def my_event_process(event:Event):
    # Remember to set the owner of any model object you create to the owner of the event like so:
    # client:Client = event.owner
    # dfn:WarehauseDef = WarehauseDef(owner=client,[...])

    logger.info(_('Hello World!'))

    # Also remember to set the event status (see core/status.py for more info)
    event.status = STATUS_CLOSED

def prepare_json(clazz, options):
    data = dict()

    if 'data' in options:
        # Loop through the model fields
        for field in clazz._meta.get_fields():
            fieldname = field.name

            if fieldname in options['data']:
                # if the field is a foreign key...
                if isinstance(field, models.ForeignKey):
                    # Get the related model
                    related_model = field.related_model
                    # Convert UUID (string) into actual object
                    if options['data'][fieldname] is None:
                        data[fieldname] = None
                    else:
                        data[fieldname] = related_model.objects.get(id=options['data'][fieldname])
                elif isinstance(field, models.ManyToOneRel) or isinstance(field, models.ManyToManyRel):
                    pass
                else:
                    data[fieldname] = options['data'][fieldname]

    return data

def inbound(event:Event):
    options = event.options

    if options['type'] == 1:
        # Inbound a new Warehause...
        dfn = WarehauseDef.objects.get(id=options['dfn'])

        data = prepare_json(Warehause, options)

        warehause = dfn.create_instance(data=data, callback=None)

        event.set_option(key='result', value={'id': str(warehause.id),})
    elif options['type'] == 2:
        # Inbound a new Product...
        dfn = ProductDef.objects.get(id=options['dfn'])

        data = prepare_json(Product, options)

        warehause:Warehause = data['warehause']
        quantity:float = data['quantity'] if 'quantity' in data else 1.0

        warehause.callback = magic_warehause_callback()

        product, _ = warehause.dispatch(dfn=dfn, quantity=quantity)

        event.set_option(key='result', value={'id': str(product.id),})

def outbound(event:Event):
    pass

def transfer(event:Event):
    options = event.options

    quantity = options['quantity']
    product:Product = Product.objects.get(id=options['product_id'])
    warehause:Warehause = Warehause.objects.get(id=options['warehause_id'])

    transfered = product.split(quantity=quantity)
    product.warehause.dispatch()
    product.warehause = warehause
    product.save()
