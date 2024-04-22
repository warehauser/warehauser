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

# callbacks.py

import logging

from .status import STATUS_OPEN
from .utils  import WarehauserError, WarehauserErrorCodes

class ModelCallback:
    def check_status(self, model):
        if model.get_status() != STATUS_OPEN:
            raise WarehauserError(msg=f'{model._meta.verbose_name} status is not OPEN.', code=WarehauserErrorCodes.STATUS_ERROR, extra={'self': model, 'status': model.status})

    def check_not_none(self, instance, msg='', extra=None):
        if instance is None:
            raise WarehauserError(msg=msg, code=WarehauserErrorCodes.NONE_NOT_ALLOWED, extra=extra)

    # Override these clean_* methods as needed.
    # def clean_external_id(self, model):
    #     pass

    # def clean_parent(self, model):
    #     pass

    # def clean_options(self, model):
    #     pass

    # def clean_status(self, model):
    #     pass

    # def clean_barcode(self, model):
    #     pass

    # def clean_descr(self, model):
    #     pass

class WarehauseDefCallback(ModelCallback):
    """
    Callback class for WarehauseDefs.
    """
    def pre_create_instance(self, dfn, data):
        pass

    def post_create_instance(self, dfn, data, model, err):
        pass

class ProductDefCallback(ModelCallback):
    """
    Callback class for ProductDefs.
    """
    def pre_create_instance(self, dfn, data):
        pass

    def post_create_instance(self, dfn, data, model, err):
        pass

class EventDefCallback(ModelCallback):
    """
    Callback class for EventDefs.
    """
    def pre_create_instance(self, dfn, data):
        pass

    def post_create_instance(self, dfn, data, model, err):
        pass

# Warehause callback
class WarehauseCallback(ModelCallback):
    def check_has_capacity(self, model, product):
        # Check measurements and check that the product will fit in this warehause.
        error = False
        usage_report = model.usage()
        measurements = product.measure()

        if model.max_weight and model.max_weight < usage_report['weight'] + measurements['weight']:
            usage_report['product_weight'] = measurements['weight']
            error = True
        else:
            del usage_report['weight']
        if model.max_height and model.max_height < usage_report['height'] + measurements['height']:
            usage_report['product_height'] = measurements['height']
            error = True
        else:
            del usage_report['height']
        if model.max_width and model.max_width < usage_report['width'] + measurements['width']:
            usage_report['product_width'] = measurements['width']
            error = True
        else:
            del usage_report['width']
        if model.max_length and model.max_length < usage_report['length'] + measurements['length']:
            usage_report['product_length'] = measurements['length']
            error = True
        else:
            del usage_report['length']
        if model.stock_max and model.stock_max < usage_report['quantity'] + product.quantity:
            usage_report['product_quantity'] = measurements['quantity']
            error = True
        else:
            del usage_report['quantity']

        if error:
            raise WarehauserError('warehause overload.', WarehauserErrorCodes.WAREHAUSE_OVERLOAD, extra={'overcap': usage_report})

    def check_pre_receive_permissive(self, model, product):
        # If warehause is not permissive and warehause stock is not None and product dfn is not equal to stock dfn
        # then this product is unacceptable
        if model.is_permissive is False:
            stock = model.get_stock(dfn=product.dfn)
            if stock is None and len(model.stock.all()) != 0:
                raise WarehauserError(msg=f'warehause is not permissive and is already occupied with a different product type', code=WarehauserErrorCodes.DFN_NOT_ALLOWED, extra={'warehause': model, 'product': product, 'stock': stock})

    def check_pre_receive_compatible_product(self, model, product):
        # If this warehause has mapped productdefs then the product must be in that list.
        allowed_productdefs = model.get_mapped_productdefs()
        is_mapped = len(allowed_productdefs) if allowed_productdefs else False

        if not is_mapped:
            # This warehause will only accept certain productdefs.
            if product.dfn not in allowed_productdefs:
                # The product is not allowed in this warehause
                raise WarehauserError(f'warehause cannot accept unmapped product {product} ProductDef {product.dfn}.', WarehauserErrorCodes.WAREHAUSE_PRODUCTDEF_NOT_MAPPED, extra={'productdefs': allowed_productdefs})

    def check_pre_dispatch_quantity(self, model, dfn, quantity, stock):
        if quantity <= float(0.0):
            raise WarehauserError(msg=f'quantity must be positive.', code=WarehauserErrorCodes.BAD_PARAMETER, extra={'self': model, 'quantity': quantity})
        if stock and stock.quantity < quantity:
            raise WarehauserError(msg=f'Not enough stock to forfill dispatch.', code=WarehauserErrorCodes.WAREHAUSE_STOCK_TOO_LOW, extra={'self': model, 'stock': stock, 'quantity': quantity})

    def check_pre_dispatch_compatible_dfn(self, model, dfn, quantity, stock):
        if not model.is_permissive:
            if dfn is None:
                raise WarehauserError(msg=f'warehause is permissive and dfn is None.', code=WarehauserErrorCodes.NONE_NOT_ALLOWED, extra={'self': model})
            found = None
            for s in model.stock.all():
                if s.dfn == dfn:
                    found = s
                    break
            if found is None:
                raise WarehauserError(msg=f'warehause does not contain any product of type dfn supplied.', code=WarehauserErrorCodes.WAREHAUSE_NOT_CONTAINS, extra={'self': model, 'dfn.id': dfn.id})

    def pre_receive(self, model, product):
        self.check_status(model=model)
        self.check_not_none(instance=product, msg=f'product is None.')
        self.check_pre_receive_permissive(model=model, product=product)
        self.check_pre_receive_compatible_product(model=model, product=product)
        self.check_has_capacity(model=model, product=product)

    def post_receive(self, model, product, stock, err):
        pass

    def pre_dispatch(self, model, dfn, quantity, stock):
        self.check_status(model=model)
        self.check_pre_dispatch_quantity(model=model, dfn=dfn, quantity=quantity, stock=stock)
        self.check_pre_dispatch_compatible_dfn(model=model, dfn=dfn, quantity=quantity, stock=stock)

    def post_dispatch(self, model, dfn, quantity, stock, product, err):
        pass


# Product callback
class ProductCallback(ModelCallback):
    def check_status(self, model):
        if model.status != STATUS_OPEN:
            raise WarehauserError(msg=f'{model.Meta.verbose_name} status is not OPEN.', code=WarehauserErrorCodes.STATUS_ERROR, extra={'self': model, 'status': model.status})

    def pre_reserve(self, model, quantity):
        self.check_status(model=model)

        if quantity is None or quantity <= 0:
            raise WarehauserError(msg=f'quantity must be a positive value.', code=WarehauserErrorCodes.BAD_PARAMETER, extra={'self': model, 'quantity': quantity})
        if model.id is None:
            raise WarehauserError(msg=f'Product is not saved and therefor cannot reserve.', code=WarehauserErrorCodes.MODEL_NOT_SAVED, extra={'self': model, 'quantity': quantity})

    def post_reserve(self, model, quantity, err):
        pass

    def pre_unreserve(self, model, quantity):
        self.check_status(model=model)

        if quantity is not None and quantity <= 0:
            raise WarehauserError(msg=f'quantity must be a positive value.', code=WarehauserErrorCodes.BAD_PARAMETER, extra={'self': model, 'quantity': quantity})
        if model.id is None:
            raise WarehauserError(msg=f'Product is not saved and therefor cannot reserve.', code=WarehauserErrorCodes.MODEL_NOT_SAVED, extra={'self': model, 'quantity': quantity})

    def post_unreserve(self, model, quantity, err):
        pass

    def pre_join(self, model, product):
        self.check_status(model)
        self.check_not_none(instance=product, msg=f'product is None.', extra={'self': model})

        # Make sure the ProductDefs of self and product are the same.
        if model.dfn != product.dfn:
            raise WarehauserError('self.dfn value does not match product.dfn.', WarehauserErrorCodes.DFN_MISMATCH, {'self.dfn': model.dfn, 'product.dfn': product.dfn})

        # If the stock expires before the self stock expires then log error and raise exception
        if model.expires != product.expires:
            msg = 'Not allowed to mix stock with mismatching expires.'
            data = {'self.expires': model.expires, 'product.expires': product.expires}

            model.log(level=logging.ERROR, msg=msg, extra=data)
            raise WarehauserError(msg, WarehauserErrorCodes.PRODUCT_EXPIRES_MISMATCH, data)

    def post_join(self, model, product, err):
        pass

    def pre_split(self, model, quantity):
        self.check_status(model)
        self.check_not_none(instance=model, msg=f'quantity is None.', extra={'self': model})

        if quantity > model.quantity:
            raise WarehauserError(msg=f'Not enough quantity in warehause to perform split.',
                                  code=WarehauserErrorCodes.WAREHAUSE_QUANTITY_LOW,
                                  extra={'self': model, 'quantity': quantity})

        if quantity <= float(0.0):
            raise WarehauserError(msg=f'quantity must be a positive float value.',
                                  code=WarehauserErrorCodes.BAD_PARAMETER,
                                  extra={'self': model, 'quantity': quantity})

        pass

    def post_split(self, model, quantity, result, err):
        pass


# Event callback
class EventCallback(ModelCallback):
    def pre_process(self, event):
        pass

    def post_process(self, event, err):
        pass
