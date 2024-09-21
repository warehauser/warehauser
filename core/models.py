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

# models.py

import importlib
import logging
import uuid
import json, pprint

from collections.abc import Mapping
from typing import Optional, Union

from db_mutex.db_mutex import db_mutex

from django.db import models
from django.db.models import ForeignKey, QuerySet
from django.db.models.fields.related import ManyToOneRel
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from django.utils.translation import gettext as _

from .callbacks import ModelCallback, WarehauseCallback, ProductCallback, EventCallback
from .status import *
from .utils import WarehauserError, WarehauserErrorCodes

try:
    CHARFIELD_MAX_LENGTH = settings.CHARFIELD_MAX_LENGTH
except Exception as e:
    CHARFIELD_MAX_LENGTH = 1024

logger = logging.getLogger(__name__)

class WarehauserAbstractModel(models.Model):
    """
    Abstract parent class for all warehauser core app models.

    Attributes:
        external_id (string):   convenience placeholder for external system id for this model object. Not used by any warehauser code.
        key         (string):   human readable description field naming this model object. Default is None.
        created_at  (datetime): date and time this model object was first saved to the database. Auto generated and not editable.
        updated_at  (datetime): date and time this model object was last saved to the database. Auto generated at save time.
        schema      (json):     optional dictionary of a json schema object to define the options field (sic).
        options     (json):     optional dictionary of key value pairs of arbitrary data.
        is_virtual  (bool):     True if this model object should have status set to DESTROY after first use is complete. Default is False.

        callback    (ModelCallback): optional delegate object used to make various pre and post checks of model object function calls.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.CharField(max_length=CHARFIELD_MAX_LENGTH, null=True, blank=True,)
    key         = models.CharField(max_length=CHARFIELD_MAX_LENGTH, null=True, blank=True, default=None,)
    created_at  = models.DateTimeField(auto_now_add=True, null=False, blank=False, editable=False,)
    updated_at  = models.DateTimeField(auto_now_add=False, null=True, blank=True,)
    schema      = models.JSONField(null=True, blank=True,)
    options     = models.JSONField(null=True, blank=True,)
    is_virtual  = models.BooleanField(null=False, blank=False, default=False,)

    _callback   = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Call the parent class constructor
        self.logs = []

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, callback):
        if callback is not None and not isinstance(callback, ModelCallback):
            raise AttributeError(_('Expected an instance of ModelCallback.'))

        self._callback = callback

    @callback.deleter
    def callback(self):
        try:
            del self._callback
        except Exception as e:
            pass

    def set_option(self, key, value):
        """
        Set an option in this model object's options field. This function will gracefully handle cases where
        options is not yet initialized, and remove keys when value is None.

        Args:
            key   (string): the key for this value. If None then there will be no change to this model object.
            value (string): the value to be stored in this model object's options field associated with the key. If None then the key will be deleted from options if it exists.
        """
        if key is None:
            return
        if value is None:
            try:
                del self.options[key]
            except Exception as ignr:
                pass
        else:
            if self.options is None:
                self.options = dict()
            self.options[key] = value
        pass

    def save(self, *args, **kwargs):
        """
        Overridde super().save(). If this model object has been saved the updated_at field is updated to the current date and time.
        """
        if self.callback is not None:
            if hasattr(self.callback, 'pre_save') and callable(self.callback.pre_save):
                self.callback.pre_save(model=self)

        err:Exception = None
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            err = e
            raise e
        finally:
            if self.callback is not None:
                if hasattr(self.callback, 'post_save') and callable(self.callback.post_save):
                    self.callback.post_save(model=self, err=err)

    def delete(self, *args, **kwargs):
        """
        Override super().delete() to log pending message(s) before the object is deleted.
        """
        # Log the delete action with an appropriate log level and message
        self.log(logging.INFO, _(f"Deleting product {repr(self)}"), {'product_id': self.id})
        self.flush_logs()

        # Call the original delete method to delete the object from the database
        super().delete(*args, **kwargs)

    def flush_logs(self):
        """
        Log all pending message(s) and clear the log queue.
        """
        # Loop through all logs and log them using the logging module
        for log in self.logs:
            # Log the message with the specified level, message, and extras
            if 'extra' in log:
                logger.log(level=log['level'], msg=log['msg'], extra=log['extra'])
            else:
                logger.log(level=log['level'], msg=log['msg'])

        # Clear the logs after logging
        self.logs.clear()

    def log(self, level, msg, extra:Optional[Mapping[str, object]]=None):
        """
        Log a message specific to this model object.

        Args:
            level (int):    one of logging.CRITICAL|DEBUG|INFO|ERROR.
            msg   (string): message string to log.
            extra (dict):   optional dictionary of extra information to log. Default is None.
        """
        # Define valid logging levels
        valid_levels = {logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL}

        # Throw an error if the level or msg is None, or if level is not valid
        if level is None or msg is None:
            raise ValueError(_("Both 'level' and 'msg' must be provided and cannot be None."))

        if level not in valid_levels:
            raise ValueError(_(f"Invalid logging level: {level}. Must be one of {valid_levels}."))

        # Ensure extra is a mutable dictionary and record the current datetime
        if extra is None:
            extra = {}
        elif not isinstance(extra, dict):
            extra = dict(extra)  # Convert to a mutable dictionary if not already

        # Add the current date and time to the extra dictionary
        if 'dt' not in extra:
            extra['dt'] = timezone.now()

        log_entry = {
            'level': level,
            'msg': msg,
            'extra': extra
        }

        self.logs.append(log_entry)

    def mutex(self):
        """
        Obtain a thread safe mutex object unique to this model object.

        Returns:
            db_mutex: the lock object. Automatically released when out of scope.

        Raises:
            WarehauserError: if this model object has not been saved.
        
        Example:
            ```
            try:
                with model.mutex():
                    # Your thread unsafe code here...
            except DBMutexError as e:
                raise WarehauserError(_('Unable to secure mutex.'), WarehauserErrorCodes.MUTEX_ERROR, {'self': model, 'error': e})
            except DBMutexTimeoutError as e:
                raise WarehauserError(_('Unable to secure mutex.'), WarehauserErrorCodes.MUTEX_TIMEOUT_ERROR, {'self': model, 'error': e})
            ```
        """
        if self.id is None:
            raise WarehauserError(msg=_('Model object is not saved.'), code=WarehauserErrorCodes.MODEL_NOT_SAVED)
        return db_mutex(f'{self.__module__}.{self.__class__.__name__.lower()}:{self.id}')

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            for field in [f.name for f in self._meta.fields if f.name not in ['id', 'created_at', 'updated_at']]:
                if getattr(self, field) != getattr(other, field):
                    self.log(level=logging.DEBUG, msg=_(f'{self.__class__.__name__}.__eq__() FALSE: self.{field} = {getattr(self, field)}, other.{field} = {getattr(other,field)}'))
                    return False
            return True
        return False

    def __hash__(self):
        return hash(self.id)

    def __del__(self):
        self.flush_logs()

    class Meta:
        abstract = True
        ordering = ['updated_at', 'created_at',]

class WarehauserAbstractDefinitionModel(WarehauserAbstractModel):
    """
    Abstract parent class for all warehauser core app definition models.
    """
    def _merge_dfn_defaults(self, data):
        validated = dict()

        for field in self._meta.fields:
            validated[field.name] = getattr(self, field.name)

        if data:
            # Update default values with request validated data
            for key, value in data.items():
                if value is None:
                    try:
                        del validated[key]
                    except:
                        pass
                # If the value is a dict/JSONField, perform a deep copy
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

        validated['dfn'] = self

        return validated

    def _create_instance(self, clazz:'WarehauserAbstractInstanceModel', data:dict, callback:ModelCallback, save:bool = True):
        if self.callback:
            if hasattr(self.callback, 'pre_create_instance') and callable(self.callback.pre_create_instance):
                self.callback.pre_create_instance(dfn=self, data=data)

        err: Exception = None
        try:
            data = self._merge_dfn_defaults(data)
            model = clazz.objects.create(**data)
            if isinstance(callback, ModelCallback):
                model.callback = callback
        except Exception as e:
            err = e
            raise e
        finally:
            if self.callback:
                if hasattr(self.callback, 'post_create_instance') and callable(self.callback.post_create_instance):
                    self.callback.post_create_instance(dfn=self, data=data, model=model, err=err)

        if save:
            model.save()

        return model

    def __str__(self) -> str:
        return self.key

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(id={self.id}, key=\'{self.key}\')'

    class Meta:
        abstract = True

class WarehauserAbstractInstanceModel(WarehauserAbstractModel):
    """
    Abstract parent class for all warehauser core app instance models.
        value       (string):   value string that identifies this model object. Usually a barcode or an address. If there are more than one value, it is best practice to add those to the options['values'] attribute (above).
    """
    value       = models.CharField(max_length=CHARFIELD_MAX_LENGTH, null=False, blank=False,)

    def get_parents(self, include_self=False):
        """
        Get a list of unique model objects that are parents to self.

        Args:
            include_self (bool): True if include self in returned list.
        
        Returns:
            list: a list of model objects related to self through parent relations.
        """
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

    def get_status(self):
        """
        Get the status of this model object restricted by the status of all parents.

        Returns:
            int: status code.
        """
        status = self.status
        for w in self.get_parents(include_self=False):
            if w.status < status:
                status = w.status
        return status

    def __str__(self) -> str:
        return f'{self.key}=\'{self.value}\''

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(id={self.id}, key=\'{self.key}\', value=\'{self.value}\')'

    class Meta:
        abstract = True


# WAREHAUSE Models

class WarehauseFields(models.Model):
    """
    Abstract model to declare common fields used by both WarehauseDef and Warehause models.

    Attributes:
        is_storage    (bool):  True if this Warehause is allowed to directly store Products. If False then Products in this Warehause must be stored in a child Warehause with is_storage equal to True.
        is_mobile     (bool):  True if this Warehause can physically move from one parent to another.
        is_permissive (bool):  True if this Warehause allows multiple ProductDefs to be stored at the same time. If True, is_storage needs to be True as well otherwise this makes no sense.
        max_weight    (float): maximum weight in arbitrary units this warehause is allowed to store. None means not limited by weight capacity.
        max_height    (float): maximum height in arbitrary units this warehause is allowed to store. None means not limited by height capacity.
        max_width     (float): maximum width in arbitrary units this warehause is allowed to store. None means not limited by width capacity.
        max_length    (float): maximum length in arbitrary units this warehause is allowed to store. None means not limited by length capacity.
        tare_weight   (float): unlaiden weight in arbitrary units of this Warehause. None means not measured/ ignored.
        tare_height   (float): unlaiden height in arbitrary units of this Warehause. None means not measured/ ignored.
        tare_width    (float): unlaiden width in arbitrary units of this Warehause. None means not measured/ ignored.
        tare_length   (float): unlaiden length in arbitrary units of this Warehause. None means not measured/ ignored.
    """
    is_storage  = models.BooleanField(null=False, blank=False, default=True,)
    is_mobile   = models.BooleanField(null=False, blank=False, default=False,)
    is_permissive = models.BooleanField(null=False, blank=False, default=False,)

    max_weight  = models.FloatField(null=True, blank=True,)
    max_height  = models.FloatField(null=True, blank=True,)
    max_width   = models.FloatField(null=True, blank=True,)
    max_length  = models.FloatField(null=True, blank=True,)

    tare_weight = models.FloatField(null=True, blank=True,)
    tare_height = models.FloatField(null=True, blank=True,)
    tare_width  = models.FloatField(null=True, blank=True,)
    tare_length = models.FloatField(null=True, blank=True,)

    class Meta:
        abstract = True

class WarehauseDef(WarehauserAbstractDefinitionModel, WarehauseFields):
    """
    Definition model for Warehauses. Always create Warehause objects through the appropriate WarehauseDef create_instance() method.

    Attributes:
        owner  (Client): the client that owns this data.

    Example:
        ```
        dfnid = # id of your desired WarehauseDef
        data = dict() # If you want all default values then this can be None
        # define override data for your Warehause that you want instead of the WarehauseDef defaults. e.g. data['max_weight'] = 10.0
        dfn = WarehuaseDef.objects.get(id=dfnid)
        model = dfn.create_instance(data=data)
        ```
    """
    owner       = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='warehausedefs', null=False, blank=False,)

    def create_instance(self, data:dict=None, callback=None, save:bool = True):
        """
        Create an instance of this definition.

        Args:
            data     (dict, optional): a key value pair dictionary of desired overridden data values for the new instance.
            callback (WarehauseCallback, optional): a callback delegate class that will be used by this instance model. If None then the standard WarehauseCallback class is used.
        """
        if not isinstance(callback, WarehauseCallback):
            callback = WarehauseCallback()
        return super()._create_instance(clazz=Warehause, data=data, callback=callback, save=save)

    class Meta(WarehauserAbstractDefinitionModel.Meta):
        abstract = False
        verbose_name = 'warehausedef'
        verbose_name_plural = 'warehausedefs'

class Warehause(WarehauserAbstractInstanceModel, WarehauseFields):
    """
    Warehause instance class.

    Attributes:
        owner     (Client):       the client that owns this data.
        parent    (Warehause):    parent Warehause or None if no parent.
        status    (int):          status of this Warehause with available choices of core.status.WAREHAUSE_STATUS_CODES.
        dfn       (WarehauseDef): WarehauseDef used to create this Warehause object.
        user      (User):         warehauser User that has custody of this Warehause.
        stock_min (float):        minimum amount of Product that is required in this Warehause. If the quantity decreases past this value then request a replenishment. None if product_def is None.
        stock_max (float):        maximum amount of Product that is allowed in this Warehause. None if product_def is None.
    """
    owner       = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='warehauses', null=False, blank=False,)
    parent      = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', null=True, blank=True,)
    status      = models.IntegerField(choices=WAREHAUSE_STATUS_CODES, default=STATUS_OPEN, null=False, blank=False,)
    dfn         = models.ForeignKey('WarehauseDef', on_delete=models.CASCADE, related_name='instances', null=False, blank=False, editable=False,)

    user        = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='warehause', null=True, blank=True, default=None,)

    stock_min   = models.FloatField(null=True, blank=True,)
    stock_max   = models.FloatField(null=True, blank=True,)

    def usage(self):
        """
        Get a report of the current usage statistics for this Warehause.

        Returns:
            dict: the usage report for this Warehause.
        """
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

        for prod in res['stock']:
            measure = prod.measure()
            res['quantity'] = res['quantity'] + measure['quantity']
            res['weight']   = res['weight']   + measure['weight']
            res['height']   = res['height']   + measure['height']
            res['width']    = res['width']    + measure['width']
            res['length']   = res['length']   + measure['length']

        return res

    def get_mapped_productdefs(self):
        """
        Get a set of ProductDefs that are mapped to this Warehause object and all its parents. If empty then this Warehause is considered to be allowed to store any Product if is_storage flag is True.

        Returns:
            set: the non None set of ProductDef objects assigned to this Warehause or all parents of this Warehause.
        """
        # Initialize an empty set to store all mapped ProductDef instances
        mapped_productdefs = set()
        parents = self.get_parents(include_self=True)
        for p in parents:
            pdefs = p.productdef_set.all()
            mapped_productdefs.add(pdefs)
        return mapped_productdefs

    def reserve(self, dfn:'ProductDef', quantity:float) -> 'Product':
        """
        Reserve a specified quantity of product from stock.

        This method fetches available stock of the given product definition (`dfn`), 
        splits the specified quantity from the stock, saves both the remaining stock 
        and the reserved portion, and returns the reserved portion.

        Args:
            dfn (ProductDef): The product definition to reserve stock from.
            quantity (float): The quantity of the product to reserve.

        Returns:
            Product: The reserved product with the specified quantity, or None if stock not found.

        Raises:
            Exception: If the quantity exceeds available stock or is not positive.
        """
        if dfn is None:
            raise ValueError('dfn must be specified.')

        stock:Product = self.get_stock(dfn=dfn)
        if not stock:
            return None

        reserved:Product = stock.split(quantity=quantity)

        # Save the objects
        stock.save()
        reserved.save()

        return reserved

    def unreserve(self, product: 'Product'):
        """
        Unreserve a product by joining it back to its parent.

        This method handles the process of unreserving a product, which involves:
        - Checking if the given product is None or has no parent. If either condition is true, the method will return early.
        - If the product has a parent, it will be joined back to the parent using the `join` method.

        Args:
            product (Product): The product to be unreserved. This product should have a parent.

        Returns:
            None
        """
        if product is None:
            return

        parent: Product = product.parent
        if parent is None:
            return

        parent.join(product=product)
        parent.save()

    def get_stock(self, dfn:'ProductDef'=None, seed_only:bool=True) -> Union['Product', QuerySet]:
        """
        Get the non depleted non reserved stock for with Warehause of a dfn type.

        Args:
            dfn (ProductDef, optional): the type of Product to search for.
            seed_only (bool, optional): Get the seed (unreserved stock only) if True (default), otherwise get all False

        Returns:
            Product: the seed Product object (if exists) matching the search criteria.
        """
        res = self.stock

        if seed_only:
            res = res.filter(parent__isnull=True)

        if dfn is None:
            # Filter for non-depleted stock where quantity is non negative and parent is None
            return res.filter(quantity__gte=0.0).order_by('dfn', 'created_at')

        res = res.filter(dfn=dfn, quantity__gte=0.0)
        if res.count() == 0:
            return None
        if res.count() == 1:
            return res.first()

        return res.order_by('dfn', 'created_at')

    def receive(self, product):
        """
        Receive a product unto this Warehause.

        Args:
            product (Product):  product to receive.
        """
        product:Product = product
        if self.callback:
            if hasattr(self.callback, 'pre_receive') and callable(self.callback.pre_receive):
                self.callback.pre_receive(model=self, product=product)

        err = None

        try:
            stock:Product = self.get_stock(dfn=product.dfn)
            if stock:
                stock.join(product=product)
            else:
                product.warehause = self
                stock = product
        except Exception as e:
            err = e
            raise e
        finally:
            if self.callback:
                if hasattr(self.callback, 'post_receive') and callable(self.callback.post_receive):
                    self.callback.post_receive(model=self, product=product, stock=stock, err=err)

        return stock

    def dispatch(self, dfn, quantity=float(1.0), save_stock:bool=True):
        """
        Dispatch a quantity of product of a given definition.

        Args:
            dfn      (ProductDef): definition of the Product to dispatch.
            quantity (float):      quantity of product to dispatch in arbitrary units.
        """
        if self.callback:
            if hasattr(self.callback, 'pre_dispatch') and callable(self.callback.pre_dispatch):
                self.callback.pre_dispatch(model=self, dfn=dfn, quantity=quantity)

        stock:Product = self.get_stock(dfn=dfn)

        err = None
        try:
            if stock is None:
                raise WarehauserError(msg=_(f'ProductDef not found in Warehause'), code=WarehauserErrorCodes.WAREHAUSE_STOCK_NOT_FOUND, extra={'self': self, 'dfn': dfn})
            product:Product = stock.split(quantity=quantity)
            if save_stock:
                stock.save()
        except Exception as e:
            err = e
            raise e
        finally:
            if self.callback:
                if hasattr(self.callback, 'post_dispatch') and callable(self.callback.post_dispatch):
                    self.callback.post_dispatch(model=self, dfn=dfn, quantity=quantity, product=product, stock=stock, err=err)

        return product, stock

    class Meta(WarehauserAbstractInstanceModel.Meta):
        abstract = False
        verbose_name = 'warehause'
        verbose_name_plural = 'warehauses'


# PRODUCT Models

class ProductFields(models.Model):
    """
    Abstract model to declare common fields used by both ProductDef and Product models.

    Attributes:
        code_count (int):   counting code defines how to count product instances. Values and meanings could be:
                                1: instance counting
                                2: weight unit counting (units being pounds or grams etc)
                                3: volume unit counting (units such as gallons or litres or cubic feet or cubic meters etc)
        atomic     (float): if this is a bundle of units, then atomic is the total number of measuring units contained per instance otherwise None/null
        is_fragile (bool):  True if this product is considered fragile to handle, False otherwise. Default is False.
        is_up      (bool):  True if this product must be stored in a particular orientation. ("This way up".) Default is False.
        is_expires (bool):  True if this product has a shelf life. All bundles of (assoc) product definitions should have share the same value for is_expires. Default is False.
        weight     (float): weight of a single unit of product in arbitrary units. If None (null) it denotes the weight is not measured or has an irregular dimension and is measured individually.
        height     (float): height of a single unit of product in arbitrary units. If None (null) it denotes the height is not measured or has an irregular dimension and is measured individually.
        width      (float): width of a single unit of product in arbitrary units. If None (null) it denotes the width is not measured or has an irregular dimension and is measured individually.
        length     (float): length of a single unit of product in arbitrary units. If None (null) it denotes the length is not measured or has an irregular dimension and is measured individually.
    """
    code_count  = models.IntegerField(null=False, blank=False,)
    atomic      = models.FloatField(null=True, blank=True, default=None,)
    is_fragile  = models.BooleanField(null=False, blank=False, default=False,)
    is_up       = models.BooleanField(null=False, blank=False, default=False,)
    is_expires  = models.BooleanField(null=False, default=False,)
    weight      = models.FloatField(null=True, blank=True,)
    height      = models.FloatField(null=True, blank=True,)
    width       = models.FloatField(null=True, blank=True,)
    length      = models.FloatField(null=True, blank=True,)

    class Meta:
        abstract = True

class ProductDef(WarehauserAbstractDefinitionModel, ProductFields):
    """
    Definition model for Products. Always create Product objects through the appropriate ProductDef create_instance() method.

    Attributes:
        owner      (Client):          the client that owns this data.
        warehauses (list(Warehause)): a list of appropriate Warehauses this ProductDef can be stored. If none are listed then store at any Warehause that returns is_storage True. All Warehauses listed mean this ProductDef can be stored at that
                                      Warehause and all children Warehauses that return is_storage True

    Example:
        ```
        dfnid = # id of your desired ProductDef
        data = dict() # If you want all default values then this can be None
        # define override data for your Product that you want instead of the ProductDef defaults. e.g. data['length'] = 10.0
        dfn = ProductDef.objects.get(id=dfnid)
        model = dfn.create_instance(data=data)
        ```
    """
    owner       = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='productdefs', null=False, blank=False,)
    warehauses  = models.ManyToManyField(Warehause)

    def create_instance(self, data:dict=None, callback=None, save:bool = True):
        if not isinstance(callback, ProductCallback):
            callback = ProductCallback()
        return super()._create_instance(clazz=Product, data=data, callback=callback, save=save)

    class Meta(WarehauserAbstractDefinitionModel.Meta):
        abstract = False
        verbose_name = 'productdef'
        verbose_name_plural = 'productdefs'

class Product(WarehauserAbstractInstanceModel, ProductFields):
    """
    Product instance class.

    Attributes:
        owner      (Client):     the client that owns this data.
        parent     (Product):    parent Product or None if no parent. Used to conceptually arrange Products into a nesting hierarchy, ignored otherwise.
        status     (int):        status of this Product with available choices of core.status.PRODUCT_STATUS_CODES.
        dfn        (ProductDef): ProductDef used to create this Product object.
        warehause  (Warehause):  location this product is currently stored in.
        quantity   (float):      quantity of product in arbitrary units.
        reserved   (float):      quantity of product reserved by an event or process in arbitrary units.
        expires    (Date):       date this product expires. If None then this product has infinite shelf life. Default None.
        is_damaged (bool):       True if this product is damaged. Default False.
    """
    owner       = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='products', null=False, blank=False,)
    parent      = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', null=True, blank=True,)
    status      = models.IntegerField(choices=PRODUCT_STATUS_CODES, default=STATUS_OPEN, null=False, blank=False,)
    dfn         = models.ForeignKey('ProductDef', on_delete=models.CASCADE, related_name='instances', null=False, blank=False, editable=False,)

    warehause   = models.ForeignKey('Warehause', on_delete=models.CASCADE, related_name='stock', null=False, blank=False,)

    quantity    = models.FloatField(null=False, blank=False, default=1.0,)

    expires     = models.DateField(null=True, blank=True, default=None,)
    is_damaged  = models.BooleanField(null=False, blank=False, default=False,)

    def total_weight(self) -> float:
        """
        Get the total weight of this Product object.
        Returns:
            float:  weight * quantity if self.weight is not None else 0.0.
        """
        return float(self.weight * self.quantity) if self.weight is not None else float(0.0)

    def total_height(self) -> float:
        """
        Get the total height of this Product object.
        Returns:
            float:  height * quantity if self.height is not None else 0.0.
        """
        return float(self.height * self.quantity) if self.height is not None else float(0.0)

    def total_width(self) -> float:
        """
        Get the total width of this Product object.
        Returns:
            float:  width * quantity if self.width is not None else 0.0.
        """
        return float(self.width * self.quantity) if self.width is not None else float(0.0)

    def total_length(self) -> float:
        """
        Get the total length of this Product object.
        Returns:
            float:  length * quantity if self.length is not None else 0.0.
        """
        return float(self.length * self.quantity) if self.length is not None else float(0.0)

    def measure(self):
        """
        Calculate and return the dimensions occupied by this product.
        """
        return {
            'weight':   self.total_weight(),
            'height':   self.total_height(),
            'width':    self.total_width(),
            'length':   self.total_length(),
            'quantity': float(self.quantity),
        }

    def join(self, product):
        """
        Join product to self if it is of the same ProductDef, and delete product.
        Note if multiple processes or threads can access this object you should consider acquiring a product.mutex() first.

        Args:
            product (Product): the other product to mix in with self.

        Example:
            ```
            try:
                # slf = some product!
                with slf.mutex():
                    # Put thread unsafe code here...
                    slf.join(product)
            except Exception as e:
                # Handle exception here...
            ```
        """
        if self.callback is not None:
            if hasattr(self.callback, 'pre_join') and callable(self.callback.pre_join):
                self.callback.pre_join(model=self, product=product)

        err:Exception = None
        try:
            self.quantity = self.quantity + product.quantity

            # Delete the product
            product.delete()
        except Exception as e:
            err = e
            raise e
        finally:
            if self.callback is not None:
                if hasattr(self.callback, 'post_join') and callable(self.callback.post_join):
                    self.callback.post_join(model=self, product=product, err=err)

    def split(self, quantity=float(1.0)) -> 'Product':
        """
        Remove a quantity of product out of this instance and returns a copy product object but with the specified quantity. 
        Note: If multiple processes or threads can access this object, consider acquiring a product.mutex() first.

        Args:
            quantity (float, optional): Quantity to remove. Default is float(1.0).

        Returns:
            Product: The new product with the specified quantity.

        Example:
            ```
            try:
                # product = some product!
                with product.mutex():
                    # Put thread unsafe code here...
                    new_product = product.split(1.0)
            except Exception as e:
                # Handle exception here...
            ```
        """
        if self.callback is not None:
            if hasattr(self.callback, 'pre_split') and callable(self.callback.pre_split):
                self.callback.pre_split(model=self, quantity=quantity)

        err: Exception = None
        try:
            if quantity > self.quantity:
                raise ValueError(_(f'Quantity {quantity} exceeds product self.quantity {self.quantity}'))

            remainder = float(self.quantity - quantity)
            self.quantity = remainder

            # Prepare data for the new Product instance
            data = {
                'id': None,
                'quantity': quantity,
            }

            for field in self._meta.get_fields(): # This is getting the 
                field_name = field.name
                if isinstance(field, ForeignKey):
                    if field_name not in ['parent',]:
                        # Handle foreign key fields
                        data[field_name] = getattr(self, field_name)
                elif not isinstance(field, ManyToOneRel) and field_name not in ['id', 'created_at', 'updated_at', 'quantity']:
                    # Handle other fields
                    data[field_name] = getattr(self, field_name)

            # Create the new Product instance
            split = Product(**data)

            # Set the parent for the new product
            split.parent = self

            # Logging
            self.log(level=logging.INFO, msg=_('Split product.'), extra={'self': self, 'split': split})

        except Exception as e:
            err = e
            raise e
        finally:
            if self.callback is not None:
                if hasattr(self.callback, 'post_split') and callable(self.callback.post_split):
                    self.callback.post_split(model=self, quantity=quantity, result=split, err=err)

        return split

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(id={self.id}, key=\'{self.key}\', value=\'{self.value}\', quantity={self.quantity})'

    class Meta(WarehauserAbstractInstanceModel.Meta):
        abstract = False
        verbose_name = 'product'
        verbose_name_plural = 'products'


# EVENT Models

class EventFields(models.Model):
    """
    Abstract model to declare common fields used by both EventDef and Event models.

    Attributes:
        is_batched (bool):  True if this event is processed by the batch processor, else processed on creation. Default is False.
        proc_name  (str):   process name (name of module.function) that this event will process or None if this event has no process.
    """
    is_batched  = models.BooleanField(null=False, blank=False, default=False,)
    proc_name   = models.CharField(max_length=CHARFIELD_MAX_LENGTH, null=True, blank=True,)

    class Meta:
        abstract = True

class EventDef(WarehauserAbstractDefinitionModel, EventFields):
    """
    Definition model for Events. Always create Event objects through the appropriate EventDef create_instance() method.

    Attributes:
        owner  (Client): the client that owns this data.

    Example:
        ```
        dfnid = # id of your desired EventDef
        data = dict() # If you want all default values then this can be None
        # define override data for your Event that you want instead of the EventDef defaults. e.g. data['is_virtual'] = True
        dfn = EventDef.objects.get(id=dfnid)
        model = dfn.create_instance(data=data)
        ```
    """
    owner       = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='eventdefs', null=False, blank=False,)

    def create_instance(self, data:dict = None, callback:ModelCallback = None, save:bool = True):
        if not isinstance(callback, EventCallback):
            callback = EventCallback()
        event:Event = super()._create_instance(clazz=Event, data=data, callback=callback, save=save)

        # If the event object is_batched is False then process immediately...
        if not event.is_batched:
            event.process()

        return event

    class Meta(WarehauserAbstractDefinitionModel.Meta):
        abstract = False
        verbose_name = 'eventdef'
        verbose_name_plural = 'eventdefs'

class Event(WarehauserAbstractInstanceModel, EventFields):
    """
    Event instance class.

    Attributes:
        owner      (Client):    the client that owns this data.
        parent     (Event):     parent Event or None if no parent. Used to conceptually arrange Events into a nesting hierarchy, ignored otherwise.
        status     (int):       status of this Event with available choices of core.status.EVENT_STATUS_CODES.
        dfn        (EventDef):  EventDef used to create this Event object.
        warehause  (Warehause): location this event is currently assigned to.
        user       (User):      user this event is assigned to.
        proc_start (DateTime):  timestamp this event started processing.
        proc_end   (DateTime):  timestamp this event ended processing.
    """
    owner       = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='events', null=False, blank=False,)
    parent      = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', null=True, blank=True,)
    status      = models.IntegerField(choices=EVENT_STATUS_CODES, default=STATUS_OPEN, null=False, blank=False,)
    dfn         = models.ForeignKey('EventDef', on_delete=models.CASCADE, related_name='instances', null=False, blank=False, editable=False,)

    warehause   = models.ForeignKey('Warehause', on_delete=models.CASCADE, related_name='events', null=True, blank=True,)
    user        = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='events', null=True, blank=True, editable=True,)

    proc_start  = models.DateTimeField(auto_now_add=False, null=True, blank=True, editable=False,)
    proc_end    = models.DateTimeField(auto_now_add=False, null=True, blank=True, editable=False,)

    def process(self):
        # Set EVENT_LOGIC_APP to 'logic' if it's None or doesn't exist
        event_logic_app = getattr(settings, 'EVENT_LOGIC_APP', 'logic')

        proc_name = str(self.proc_name)

        if self.callback is not None:
            if hasattr(self.callback, 'pre_process') and callable(self.callback.pre_process):
                self.callback.pre_process(event=self)

        err: Exception = None
        try:
            if self.proc_name is None:
                return None

            # Determine base_module based on whether proc_name contains a '.'
            if '.' not in proc_name:
                module_name = f'{event_logic_app}.{self.owner.group.name}.tasks'
            else:
                # Split the proc_name to check further conditions
                module_name = f'{event_logic_app}.{proc_name}'.rpartition('.')[0]
                proc_name = proc_name.rpartition('.')[2]

            # Load the module and function dynamically
            module = importlib.import_module(module_name)
            proc_func = getattr(module, proc_name)

            # Update status and timestamps
            self.proc_start = timezone.now()
            self.status = STATUS_PROCESSING
            self.save()

            try:
                proc_func(self)  # Call the process function
            finally:
                self.proc_end = timezone.now()
                self.save()
        except Exception as e:
            err = e
            raise e
        finally:
            if self.callback is not None:
                if hasattr(self.callback, 'post_process') and callable(self.callback.post_process):
                    self.callback.post_process(event=self, err=err)

        return self

    class Meta(WarehauserAbstractInstanceModel.Meta):
        abstract = False
        verbose_name = 'event'
        verbose_name_plural = 'events'

# Through models for custom ManyToManyFields

# Utility models

class Client(models.Model):
    """
    Internal use only. Used to interface client identities with data ownership.
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='client', null=False, blank=False,)

    class Meta(WarehauserAbstractInstanceModel.Meta):
        abstract = False
        verbose_name = 'client'
        verbose_name_plural = 'clients'
        constraints = [
            models.UniqueConstraint(
                fields=['group'],
                name='unique_group_in_client'
            )
        ]

class UserAux(models.Model):
    """
    Internal use only. Used to manage users such as manage forgotten password requests.
    """
    user     = models.OneToOneField(get_user_model(), related_name='userAux', on_delete=models.CASCADE, null=False, blank=False, editable=False,)
    options  = models.JSONField(null=False, blank=False,)

    class Meta:
        verbose_name = 'useraux'
        verbose_name_plural = 'useraux'
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                name='unique_user_in_user_aux'
            )
        ]

# Signals

# Utility functions

# def filter_owner_groups(groups:list):
#     return Client.objects.filter(group__in=groups)
    # return groups.filter(name__startswith='client_')

# def filter_owner_groups(groups: list):
#     return set(Group.objects.filter(id__in=Client.objects.filter(group__in=groups).values_list('group', flat=True)))
