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

# models.py

import importlib
import logging

from db_mutex import DBMutexError, DBMutexTimeoutError
from db_mutex.db_mutex import db_mutex

from django.apps import apps
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.translation import gettext as _

from .callbacks import ModelCallback, WarehauseCallback, ProductCallback, EventCallback
from .status import WAREHAUSEDEF_STATUS_CODES, WAREHAUSE_STATUS_CODES, PRODUCTDEF_STATUS_CODES, PRODUCT_STATUS_CODES, EVENTDEF_STATUS_CODES, EVENT_STATUS_CODES, STATUS_DESTROY, STATUS_CLOSED, STATUS_PROCESSING, STATUS_ON_HOLD, STATUS_OPEN
from .utils import WarehauserError, WarehauserErrorCodes

CHARFIELD_MAX_LENGTH = settings.CHARFIELD_MAX_LENGTH

# Create your models here.

class AbstractModel(models.Model):
    external_id = models.CharField(max_length=CHARFIELD_MAX_LENGTH, null=True, blank=False,)
    created_at  = models.DateTimeField(auto_now_add=True, null=False, blank=False,)
    updated_at  = models.DateTimeField(auto_now_add=False, null=True, blank=False,)
    options     = models.JSONField(null=True, blank=False,)
    barcode     = models.CharField(max_length=CHARFIELD_MAX_LENGTH, null=False, blank=False,)
    descr       = models.CharField(max_length=CHARFIELD_MAX_LENGTH, null=True, blank=False, default=None,)
    is_virtual  = models.BooleanField(null=False, blank=False, default=False,)

    def lock(self):
        if self.id is None:
            raise WarehauserError(msg=f'Model object is not saved.', code=WarehauserErrorCodes.MODEL_NOT_SAVED)
        return db_mutex(f'{self.__class__.__name__.lower()}:{self.id}')

    def get_status(self):
        status = self.status
        for w in self.get_parents(include_self=False):
            if w.status < status:
                status = w.status
        return status

    def get_top_parent(self):
        result = self
        while result.parent is not None:
            result = result.parent
        return result

    def get_parents(self, include_self=False):
        relatives = set()

        if include_self:
            relatives.add(self)

        def _traverse_up(obj):
            nonlocal relatives

            parent = obj.parent
            if parent:
                if relatives.add(parent):
                    _traverse_up(obj=parent)

        _traverse_up(self)

        return list(relatives)

    def get_children(self, include_self=False):
        relatives = set()

        if include_self:
            relatives.add(self)

        if self.id is None:
            return relatives

        def _traverse_down(obj):
            nonlocal relatives

            children = obj.children.all()
            for child in children:
                if relatives.add(child):
                    _traverse_down(obj=child)

        _traverse_down(self)

        return list(relatives)

    # recursively get all parent and children.
    def get_relatives(self, include_self=False):
        return list(set(self.get_parents(include_self) + self.get_children(False)))

    def set_option(self, key, value):
        if value is None:
            try:
                del self.options[key]
            except:
                pass
        else:
            if self.options is None:
                self.options = dict()
            self.options[key] = value

        pass

    def append_option(self, key, value):
        if self.options is None:
            self.options = dict()

        if key not in self.options:
            self.options[key] = list()

        self.options[key].append(value)
        pass

    def log(self, level, msg, extra = None):
        logging.log(level=level, msg=msg, extra=extra)
        pass

    def clean_fields(self, fields):
        pass

    def save(self, *args, **kwargs):
        self.clean_fields(None)

        if self.id:
            self.updated_at = timezone.now()

        super().save(*args, **kwargs)
        logging.info(f'Saved {self.__str__()}')

    def __str__(self):
        if self.id:  # Check if the object has been saved to the database
            id = self.id
        else:
            id = '<None>'

        if self.barcode:
            barcode = f"\"{self.barcode}\""
        else:
            barcode = '<None>'

        return f"{self.__module__}.{self.__class__.__name__}(id={id}, barcode={barcode})"

    class Meta:
        abstract = True
        ordering = ['updated_at', 'created_at',]

# Base Model class for all Def models
class AbstractDefModel(AbstractModel):
    def merge_dfn_defaults(self, data):
        validated = dict()

        for field in self._meta.fields:
            validated[field.name] = getattr(self, field.name)

        if data:
            # Update default values with request validated
            for key, value in data.items():
                # If the value is a dict/JSONField, perform a deep copy
                if value is None:
                    try:
                        del validated[key]
                    except:
                        pass
                elif isinstance(value, dict):
                    if validated[key] is None or not isinstance(validated[key], dict):
                        validated[key] = value
                    else:
                        validated[key].update(value)
                else:
                    validated[key] = value
        else:
            try:
                del validated['parent']
            except KeyError as e:
                pass

        try:
            del validated['id']
        except KeyError as e:
            pass
        try:
            del validated['created_at']
        except KeyError as e:
            pass
        try:
            del validated['updated_at']
        except KeyError as e:
            pass

        # validated['dfn_id'] = self.id
        validated['dfn'] = self

        return validated

    class Meta:
        abstract = True

# Base Model class for all instance models
class AbstractInstModel(AbstractModel):
    _callback: ModelCallback = None

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, value):
        self._callback = value

    @callback.deleter
    def callback(self):
        del self._callback

    def clean_fields(self, fields):
        if self._callback is None:
            return

        if fields is None:
            fields = self._meta.fields

        for field in fields:
            # Generate method name for field
            method_name = f'clean_{field.name}'
            # Check if method exists and call it
            if hasattr(self.callback, method_name):
                getattr(self.callback, method_name)(self)
        pass

    class Meta:
        abstract = True


# WAREHAUSE Models

class WarehauseFields(models.Model):
    # This field is True if this WarehauseDef can store product. If False, then this WarehauseDef can only store product in
    # children (see parent above) WarehauseDefs.
    is_storage  = models.BooleanField(null=False, blank=False, default=True,)

    # True if this WarehauseDef is a mobile warehause such as a forklift or conveyor belt, or employee picker
    is_mobile   = models.BooleanField(null=False, blank=False, default=False,)

    # True if this warehause accepts Product chains (multiple different product kinds at once)
    is_permissive = models.BooleanField(null=False, blank=False, default=False,)

    # maximum total dimensions of stored or carried Product(s) allowed (arbitrary units)
    max_weight  = models.FloatField(null=True, blank=False,)
    max_height  = models.FloatField(null=True, blank=False,)
    max_width   = models.FloatField(null=True, blank=False,)
    max_length  = models.FloatField(null=True, blank=False,)

    # Tare (or empty) dimensions of this Warehause
    tare_weight = models.FloatField(null=True, blank=False,)
    tare_height = models.FloatField(null=True, blank=False,)
    tare_width  = models.FloatField(null=True, blank=False,)
    tare_length = models.FloatField(null=True, blank=False,)

    class Meta:
        abstract = True

class WarehauseDef(AbstractDefModel, WarehauseFields):
    parent      = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', null=True, blank=False,)
    status      = models.IntegerField(choices=WAREHAUSEDEF_STATUS_CODES, default=STATUS_OPEN, null=False, blank=False,)

    def create_instance(self, data:dict = None, callback = None):
        if callback is None:
            callback = WarehauseCallback

        callback.pre_create_instance(dfn=self, data=data)

        data = self.merge_dfn_defaults(data)
        model:Warehause = apps.get_model('core', 'Warehause')(**data)

        model._callback = callback

        callback.post_create_instance(dfn=self, data=data, model=model)

        return model

    class Meta(AbstractDefModel.Meta):
        abstract = False
        constraints = [
            models.UniqueConstraint(fields=['barcode'], name='constraint_unique_warehauserdef_barcode')
        ]
        verbose_name = 'warehausedef'
        verbose_name_plural = 'warehausedefs'

class Warehause(AbstractInstModel, WarehauseFields):
    parent      = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', null=True, blank=False,)
    status      = models.IntegerField(choices=WAREHAUSE_STATUS_CODES, default=STATUS_OPEN, null=False, blank=False,)
    dfn         = models.ForeignKey('WarehauseDef', on_delete=models.CASCADE, related_name='instances', null=False, blank=False,)

    user        = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='warehause', null=True, blank=False, default=None,)

    # Minimum amount of Product that is required in this Warehause. If the quantity decreases past this value then request a replenishment. None if product_def is None.
    stock_min   = models.FloatField(null=True, blank=False,)
    # Maximum amount of Product that is allowed in this Warehause. None if product_def is None.
    stock_max   = models.FloatField(null=True, blank=False,)

    @property
    def callback(self):
        if self._callback:
            return self._callback
        return WarehauseCallback

    def usage(self):
        res = {
            'stock':      self.stock.all(),
            'stock_min':  self.stock_min,
            'stock_max':  self.stock_max,
            'max_weight': self.max_weight,
            'max_height': self.max_height,
            'max_width':  self.max_width,
            'max_length': self.max_length,
            'quantity':   float(0.0),
            'weight':     float(0.0),
            'height':     float(0.0),
            'width':      float(0.0),
            'length':     float(0.0),
        }

        for prod in  res['stock']:
            measure = prod.measure()
            res['quantity'] = res['quantity'] + measure['quantity']
            res['weight']   = res['weight']   + measure['weight']
            res['height']   = res['height']   + measure['height']
            res['width']    = res['width']    + measure['width']
            res['length']   = res['length']   + measure['length']

        return res

    def get_mapped_productdefs(self):
        # Initialize an empty set to store all mapped ProductDef instances
        mapped_productdefs = set()
        parents = self.get_parents(include_self=True)
        for p in parents:
            pdefs = p.productdef_set.all()
            mapped_productdefs.add(pdefs)
        return mapped_productdefs

    def get_stock(self, dfn):
        if dfn is None:
            try:
                return self.stock.filter(quantity=float(-1.0)).first()
            except:
                return None

        try:
            return self.stock.filter(dfn=dfn).first()
        except:
            return None

    def reserve(self, dfn, quantity = float(1.0)):
        product: Product = self.get_stock(dfn=dfn)

        self.callback().pre_reserve(warehause=self, dfn=dfn, quantity=quantity, product=product)
        product.reserve(quantity=quantity)
        self.callback().post_reserve(warehause=self, dfn=dfn, quantity=quantity, product=product)

        return product

    def unreserve(self, dfn, quantity = float(1.0)):
        product: Product = self.get_stock(dfn=dfn)

        self.callback().pre_unreserve(warehause=self, dfn=dfn, quantity=quantity, product=product)
        product.unreserve(quantity=quantity)
        self.callback().post_unreserve(warehause=self, dfn=dfn, quantity=quantity, product=product)

        return product

    def receive(self, product):
        product: Product = product
        self.callback().pre_receive(warehause=self, product=product)

        stock: Product = None

        # If the product is indeterminate then if this warehause (self) contains
        # an indeterminate stock then return the existing indeterminate stock,
        # else attach product
        try:
            stock = self.get_stock(dfn=product.dfn)
            stock.join(product=product, save=True)
        except:
            stock = product
            stock.warehause = self

        self.callback().post_receive(warehause=self, product=product, stock=stock)

        return stock

    def dispatch(self, dfn, quantity = float(1.0), unreserve = False):
        stock: Product = self.get_stock(dfn=dfn)
        self.callback().pre_dispatch(warehause=self, dfn=dfn, quantity=quantity, stock=stock)

        product = stock.split(quantity=quantity, save=(not unreserve))

        if unreserve:
            stock.unreserve(quantity=quantity)
            stock.save()

        self.callback().post_dispatch(warehause=self, dfn=dfn, quantity=quantity, stock=stock, product=product)

        return product

    def transfer(self, to_warehause, dfn, quantity = float(1.0)):
        to_warehause: Warehause = to_warehause
        self.callback().pre_transfer(to_warehause=to_warehause, dfn=dfn, quantity=quantity)

        product: Product = self.dispatch(dfn=dfn, quantity=quantity)
        stock: Product = to_warehause.receive(product=product)

        self.callback().post_transfer(to_warehause=to_warehause, dfn=dfn, quantity=quantity, stock=stock)

        return stock

    class Meta(AbstractInstModel.Meta):
        abstract = False
        verbose_name = 'warehause'
        verbose_name_plural = 'warehauses'


# PRODUCT Models

class ProductFields(models.Model):
    # counting code defines how to count product instances
    # values and meanings could be:
    #  1: instance counting
    #  2: weight unit counting (units being pounds or grams etc)
    #  3: volume unit counting (units such as gallons or litres or cubic feet or cubic meters etc)
    code_count  = models.IntegerField(null=False, blank=False,)

    # if this is a bundle of units, then atomic is the total number of measuring units contained per instance otherwise None/null
    atomic      = models.FloatField(null=True, blank=False, default=None,)

    # Flag True if this product is considered fragile to handle, False otherwise
    is_fragile  = models.BooleanField(null=False, blank=False, default=False,)

    # Flag True if this product must be stored in a particular orientation. ("This way up".)
    is_up       = models.BooleanField(null=False, blank=False, default=False,)

    # Flag True if this product has a shelf life. All bundles of (assoc) product definitions should have share the same value for is_expires
    is_expires  = models.BooleanField(null=False, default=False,)

    # dimensions and measurements (arbitrary units)
    # if a dimension is None (null) it denotes the product has
    # an irregular dimension and is measured individually
    weight      = models.FloatField(null=True, blank=False,)
    height      = models.FloatField(null=True, blank=False,)
    width       = models.FloatField(null=True, blank=False,)
    length      = models.FloatField(null=True, blank=False,)

    class Meta:
        abstract = True

class ProductDef(AbstractDefModel, ProductFields):
    parent      = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', null=True, blank=False,)
    status      = models.IntegerField(choices=PRODUCTDEF_STATUS_CODES, default=STATUS_OPEN, null=False, blank=False,)

    # a list of appropriate Warehauses this ProductDef can be stored
    # if none are listed then store at any Warehause that returns is_storage True
    # all Warehauses listed mean this ProductDef can be stored at that Warehause and all children Warehauses that return
    # is_storage True
    warehauses  = models.ManyToManyField(Warehause)

    def create_instance(self, data:dict = None, callback = None):
        if callback is None:
            callback = ProductCallback

        callback.pre_create_instance(dfn=self, data=data)

        data = self.merge_dfn_defaults(data)
        model:Product = apps.get_model('core', 'Product')(**data)

        model._callback = callback

        callback.post_create_instance(dfn=self, data=data, model=model)

        return model

    def get_warehauses(self):
        warehauses = set()

        def _get_parent_warehauses(dfn):
            nonlocal warehauses
            warehauses |= set(dfn.warehauses.all())
            if dfn.parent:
                _get_parent_warehauses(dfn.parent)

        _get_parent_warehauses(self)
        return {warehause for warehause in warehauses if warehause is not None}

    class Meta(AbstractDefModel.Meta):
        abstract = False
        constraints = [
            models.UniqueConstraint(fields=['barcode'], name='constraint_unique_productdef_barcode')
        ]
        verbose_name = 'productdef'
        verbose_name_plural = 'productdefs'

class Product(AbstractInstModel, ProductFields):
    parent      = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', null=True, blank=False,)
    status      = models.IntegerField(choices=PRODUCT_STATUS_CODES, default=STATUS_OPEN, null=False, blank=False,)
    dfn         = models.ForeignKey('ProductDef', on_delete=models.CASCADE, related_name='instances', null=False, blank=False,)

    warehause   = models.ForeignKey('Warehause', on_delete=models.CASCADE, related_name='stock', null=True, blank=False,)

    quantity    = models.FloatField(null=False, blank=False, default=1.0,)
    reserved    = models.FloatField(null=False, blank=False, default=0.0,)

    expires     = models.DateField(null=True, blank=False,)
    is_damaged  = models.BooleanField(null=False, blank=False, default=False,)

    @property
    def callback(self):
        if self._callback:
            return self._callback
        return ProductCallback

    # Calculate and return the dimensions occupied by this product.
    def measure(self):
        return {
            'weight':   float(self.weight * self.quantity) if self.weight is not None else float(0.0),
            'height':   float(self.height * self.quantity) if self.height is not None else float(0.0),
            'width':    float(self.width  * self.quantity) if self.width is not None else float(0.0),
            'length':   float(self.length * self.quantity) if self.length is not None else float(0.0),
            'quantity': float(self.quantity) if self.quantity is not None else float(0.0),
        }

    def reserve(self, quantity = float(1.0)):
        self.callback().pre_reserve(self, quantity)

        try:
            with self.lock():
                unreserved = self.quantity - self.reserved
                if quantity > unreserved:
                    raise WarehauserError('warehause does not have enough unreserved stock.', WarehauserErrorCodes.WAREHAUSE_STOCK_TOO_LOW, {'product': self, 'quantity': self.quantity, 'reserved': self.reserved})

                self.reserved = self.reserved + quantity
                self.save()
        except DBMutexError as e:
            raise WarehauserError('Unable to secure mutex for product.', WarehauserErrorCodes.MUTEX_ERROR, {'self': self, 'error': e})
        except DBMutexTimeoutError as e:
            raise WarehauserError('Unable to secure mutex for stock.', WarehauserErrorCodes.MUTEX_TIMEOUT_ERROR, {'self': self, 'error': e})

        self.callback().post_reserve(self, quantity)

        pass

    def unreserve(self, quantity = None):
        self.callback().pre_unreserve(self, quantity)

        try:
            with self.lock():
                if quantity is None:
                    self.reserved = float(0.0)
                else:
                    self.reserved = max(float(0.0), self.reserved - quantity)
                self.save()
        except DBMutexError as e:
            raise WarehauserError('Unable to secure mutex for stock.', WarehauserErrorCodes.MUTEX_ERROR, {'self': self, 'error': e})
        except DBMutexTimeoutError as e:
            raise WarehauserError('Unable to secure mutex for stock.', WarehauserErrorCodes.MUTEX_TIMEOUT_ERROR, {'self': self, 'error': e})

        self.callback().post_unreserve(self, quantity)

        pass

    def join(self, product, save = False):
        self.callback().pre_join(self, product)

        self.quantity = float(self.quantity + product.quantity)
        product.quantity = float(0.0)

        self.log(   level=logging.INFO, msg='Transfered from product to self.', extra={'from': product})
        product.log(level=logging.INFO, msg='Transfered from self to product.', extra={'to': self})

        self.callback().post_join(self, product)

        if save:
            self.save()

        pass

    def split(self, dfn = None, quantity = float(1.0), save = False):
        self.callback().pre_split(self, dfn, quantity)

        if quantity > self.quantity:
            raise WarehauserError('Not enough current quantity to complete the split.', WarehauserErrorCodes.WAREHAUSE_STOCK_TOO_LOW, {'self': self})

        self.quantity = float(self.quantity - quantity)

        data = model_to_dict(self)

        try:
            del data['id']
        except KeyError:
            pass
        try:
            del data['created_at']
        except KeyError:
            pass
        try:
            del data['updated_at']
        except KeyError:
            pass
        try:
            del data['warehause']
        except KeyError:
            pass

        data['quantity'] = quantity

        if isinstance(data['dfn'], int):
            data['dfn'] = ProductDef.objects.get(id=data['dfn'])

        if dfn:
            data['dfn'] = dfn
            data['barcode'] = dfn.barcode
            data['descr'] = dfn.descr

        product = Product(**data)

        product.log(level=logging.INFO, msg='Split product.', extra={'from': self})

        if self.quantity == float(0.0):
            if self.is_virtual:
                self.status = STATUS_DESTROY
            else:
                self.status = STATUS_CLOSED
            self.warehause = None

        self.callback().post_split(self, dfn, quantity, product)

        if save:
            self.save()

        return product

    class Meta(AbstractInstModel.Meta):
        abstract = False
        verbose_name = 'product'
        verbose_name_plural = 'products'


# EVENT Models

class EventFields(models.Model):
    is_batched  = models.BooleanField(null=False, blank=False, default=False,)
    proc_name   = models.CharField(max_length=CHARFIELD_MAX_LENGTH, null=True, blank=False,)

    class Meta:
        abstract = True

class EventDef(AbstractDefModel, EventFields):
    parent      = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', null=True, blank=False,)
    status      = models.IntegerField(choices=EVENTDEF_STATUS_CODES, default=STATUS_OPEN, null=False, blank=False,)

    def create_instance(self, data:dict = None, callback = None):
        if callback is None:
            callback = EventCallback

        callback.pre_create_instance(dfn=self, data=data)

        data = self.merge_dfn_defaults(data)
        model:Event = apps.get_model('core', 'Event')(**data)

        model._callback = callback

        callback.post_create_instance(dfn=self, data=data, model=model)

        return model

    class Meta(AbstractDefModel.Meta):
        abstract = False
        constraints = [
            models.UniqueConstraint(fields=['barcode'], name='constraint_unique_eventdef_barcode')
        ]
        verbose_name = 'eventdef'
        verbose_name_plural = 'eventdefs'

class Event(AbstractInstModel, EventFields):
    parent      = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', null=True, blank=False,)
    status      = models.IntegerField(choices=EVENT_STATUS_CODES, default=STATUS_OPEN, null=False, blank=False,)
    dfn         = models.ForeignKey('EventDef', on_delete=models.CASCADE, related_name='instances', null=False, blank=False,)

    warehause   = models.ForeignKey('Warehause', on_delete=models.CASCADE, related_name='events', null=True, blank=False,)
    user        = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='events', null=True, blank=False, default=None,)

    proc_start  = models.DateTimeField(auto_now_add=False, null=True, blank=False,)
    proc_end    = models.DateTimeField(auto_now_add=False, null=True, blank=False,)

    @property
    def callback(self):
        if self._callback:
            return self._callback
        return EventCallback

    def process(self):
        self.callback().pre_process(event=self)

        if self.proc_name is None:
            return None

        base_module = 'core.tasks'
        proc_name = str(self.proc_name)

        try:
            try:
                if '.' in proc_name:
                    module_name, function_name = proc_name.rsplit('.', 1)
                    module = importlib.import_module(f'{base_module}.{module_name}')
                    proc_func = getattr(module, function_name)
                else:
                    module = importlib.import_module(f'{base_module}')
                    proc_func = getattr(module, proc_name)
            except:
                err = f"Unable to load function '{base_module}.{self.proc_name}'."
                self.register_process_results(STATUS_CLOSED, {'error': err})

                self.save()
                return self

            self.proc_start = timezone.now()
            self.status = STATUS_PROCESSING
            self.save()

            try:
                proc_func(self)
            finally:
                self.proc_end = timezone.now()

            if self.status == STATUS_DESTROY:
                try:
                    self.delete()
                except:
                    pass
                logging.error(msg=f'Event [{self}] is deleted.')
                return None
            else:
                self.save()
        finally:
            self.callback().post_process(event=self)

        return self

    class Meta(AbstractInstModel.Meta):
        abstract = False
        verbose_name = 'event'
        verbose_name_plural = 'events'

# Through models for custom ManyToManyFields

# Utility models
