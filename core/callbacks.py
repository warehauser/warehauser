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

# callbacks.py

import logging

from .status import STATUS_OPEN
from .utils  import WarehauserError, WarehauserErrorCodes

class ModelCallback:
    @classmethod
    def pre_create_instance(cls, dfn, data):
        pass

    @classmethod
    def post_create_instance(cls, dfn, data, model):
        pass

    @classmethod
    def check_status(cls, model):
        if model.get_status() != STATUS_OPEN:
            raise WarehauserError(msg=f'{model._meta.verbose_name} status is not OPEN.', code=WarehauserErrorCodes.STATUS_ERROR, extra={'self': model, 'status': model.status})

    @classmethod
    def check_not_none(cls, instance, msg='', extra=None):
        if instance is None:
            raise WarehauserError(msg=msg, code=WarehauserErrorCodes.NONE_NOT_ALLOWED, extra=extra)

    # Override these clean_* methods as needed.
    # @classmethod
    # def clean_external_id(cls, model):
    #     pass

    # @classmethod
    # def clean_parent(cls, model):
    #     pass

    # @classmethod
    # def clean_options(cls, model):
    #     pass

    # @classmethod
    # def clean_status(cls, model):
    #     pass

    # @classmethod
    # def clean_barcode(cls, model):
    #     pass

    # @classmethod
    # def clean_descr(cls, model):
    #     pass


# Warehause callback
class WarehauseCallback(ModelCallback):
    @classmethod
    def check_has_capacity(cls, warehause, product):
        # Check measurements and check that the product will fit in this warehause.
        error = False
        usage_report = warehause.usage()
        measurements = product.measure()

        if warehause.max_weight and warehause.max_weight < usage_report['weight'] + measurements['weight']:
            usage_report['product_weight'] = measurements['weight']
            error = True
        else:
            del usage_report['weight']
        if warehause.max_height and warehause.max_height < usage_report['height'] + measurements['height']:
            usage_report['product_height'] = measurements['height']
            error = True
        else:
            del usage_report['height']
        if warehause.max_width and warehause.max_width < usage_report['width'] + measurements['width']:
            usage_report['product_width'] = measurements['width']
            error = True
        else:
            del usage_report['width']
        if warehause.max_length and warehause.max_length < usage_report['length'] + measurements['length']:
            usage_report['product_length'] = measurements['length']
            error = True
        else:
            del usage_report['length']
        if warehause.stock_max and warehause.stock_max < usage_report['quantity'] + product.quantity:
            usage_report['product_quantity'] = measurements['quantity']
            error = True
        else:
            del usage_report['quantity']

        if error:
            raise WarehauserError('warehause overload.', WarehauserErrorCodes.WAREHAUSE_OVERLOAD, extra={'overcap': usage_report})

    @classmethod
    def check_pre_receive_permissive(cls, warehause, product):
        # If warehause is not permissive and warehause stock is not None and product dfn is not equal to stock dfn
        # then this product is unacceptable
        if warehause.is_permissive is False:
            stock = warehause.get_stock(dfn=product.dfn)
            if stock is None and len(warehause.stock.all()) != 0:
                raise WarehauserError(msg=f'warehause is not permissive and is already occupied with a different product type', code=WarehauserErrorCodes.DFN_NOT_ALLOWED, extra={'warehause': warehause, 'product': product, 'stock': stock})

    @classmethod
    def check_pre_receive_compatible_product(cls, warehause, product):
        # If this warehause has mapped productdefs then the product must be in that list.
        allowed_productdefs = warehause.get_mapped_productdefs()
        is_mapped = len(allowed_productdefs) if allowed_productdefs else False

        if not is_mapped:
            # This warehause will only accept certain productdefs.
            if product.dfn not in allowed_productdefs:
                # The product is not allowed in this warehause
                raise WarehauserError(f'warehause cannot accept unmapped product {product} ProductDef {product.dfn}.', WarehauserErrorCodes.WAREHAUSE_PRODUCTDEF_NOT_MAPPED, extra={'productdefs': allowed_productdefs})

    @classmethod
    def check_pre_dispatch_quantity(cls, warehause, dfn, quantity, stock):
        if quantity <= float(0.0):
            raise WarehauserError(msg=f'quantity must be positive.', code=WarehauserErrorCodes.BAD_PARAMETER, extra={'self': warehause, 'quantity': quantity})
        if stock and stock.quantity < quantity:
            raise WarehauserError(msg=f'Not enough stock to forfill dispatch.', code=WarehauserErrorCodes.WAREHAUSE_STOCK_TOO_LOW, extra={'self': warehause, 'stock': stock, 'quantity': quantity})

    @classmethod
    def check_pre_dispatch_compatible_dfn(cls, warehause, dfn, quantity, stock):
        if not warehause.is_permissive:
            if dfn is None:
                raise WarehauserError(msg=f'warehause is permissive and dfn is None.', code=WarehauserErrorCodes.NONE_NOT_ALLOWED, extra={'self': warehause})
            found = None
            for s in warehause.stock.all():
                if s.dfn == dfn:
                    found = s
                    break
            if found is None:
                raise WarehauserError(msg=f'warehause does not contain any product of type dfn supplied.', code=WarehauserErrorCodes.WAREHAUSE_NOT_CONTAINS, extra={'self': warehause, 'dfn.id': dfn.id})

    @classmethod
    def check_pre_reserve_quantity(cls, warehause, dfn, quantity, product):
        if quantity <= float(0.0):
            raise WarehauserError(msg=f'quantity must be positive.', code=WarehauserErrorCodes.BAD_PARAMETER, extra={'self': warehause, 'quantity': quantity})

    @classmethod
    def pre_reserve(cls, warehause, dfn, quantity, product):
        cls.check_status(model=warehause)
        cls.check_not_none(instance=product, msg=f'warehause does not contain ProductDef instance.', extra={'dfn': dfn, 'self': warehause, 'quantity': quantity})
        cls.check_pre_reserve_quantity(warehause=warehause, dfn=dfn, quantity=quantity, product=product)

    @classmethod
    def post_reserve(cls, warehause, dfn, quantity, product):
        pass

    @classmethod
    def pre_unreserve(cls, warehause, dfn, quantity, product):
        cls.check_status(model=warehause)
        cls.check_not_none(instance=product, msg=f'warehause does not contain ProductDef instance.', extra={'dfn': dfn, 'self': warehause, 'quantity': quantity})

    @classmethod
    def post_unreserve(cls, warehause, dfn, quantity, product):
        pass

    @classmethod
    def pre_receive(cls, warehause, product):
        cls.check_status(model=warehause)
        cls.check_not_none(instance=product, msg=f'product is None.')
        cls.check_pre_receive_permissive(warehause=warehause, product=product)
        cls.check_pre_receive_compatible_product(warehause=warehause, product=product)
        cls.check_has_capacity(warehause=warehause, product=product)

    @classmethod
    def post_receive(cls, warehause, product, stock):
        pass

    @classmethod
    def pre_dispatch(cls, warehause, dfn, quantity, stock):
        cls.check_status(model=warehause)
        cls.check_pre_dispatch_quantity(warehause=warehause, dfn=dfn, quantity=quantity, stock=stock)
        cls.check_pre_dispatch_compatible_dfn(warehause=warehause, dfn=dfn, quantity=quantity, stock=stock)

    @classmethod
    def post_dispatch(cls, warehause, dfn, quantity, stock, product):
        pass

    @classmethod
    def pre_transfer(cls, to_warehause, dfn, quantity):
        cls.check_not_none(instance=to_warehause, msg=f'to_warehause is None.')

    @classmethod
    def post_transfer(cls, to_warehause, dfn, quantity, stock):
        pass


# Product callback
class ProductCallback(ModelCallback):
    @classmethod
    def check_status(cls, model):
        if model.status != STATUS_OPEN:
            raise WarehauserError(msg=f'{model.Meta.verbose_name} status is not OPEN.', code=WarehauserErrorCodes.STATUS_ERROR, extra={'self': model, 'status': model.status})

    @classmethod
    def pre_reserve(cls, model, quantity):
        cls.check_status(model=model)

        if quantity is None or quantity <= 0:
            raise WarehauserError(msg=f'quantity must be a positive value.', code=WarehauserErrorCodes.BAD_PARAMETER, extra={'self': model, 'quantity': quantity})
        if model.id is None:
            raise WarehauserError(msg=f'Product is not saved and therefor cannot reserve.', code=WarehauserErrorCodes.MODEL_NOT_SAVED, extra={'self': model, 'quantity': quantity})

    @classmethod
    def post_reserve(cls, model, quantity):
        pass

    @classmethod
    def pre_unreserve(cls, model, quantity):
        cls.check_status(model=model)

        if quantity is not None and quantity <= 0:
            raise WarehauserError(msg=f'quantity must be a positive value.', code=WarehauserErrorCodes.BAD_PARAMETER, extra={'self': model, 'quantity': quantity})
        if model.id is None:
            raise WarehauserError(msg=f'Product is not saved and therefor cannot reserve.', code=WarehauserErrorCodes.MODEL_NOT_SAVED, extra={'self': model, 'quantity': quantity})

    @classmethod
    def post_unreserve(cls, model, quantity):
        pass

    @classmethod
    def pre_join(cls, model, product):
        cls.check_status(model)

        if product is None:
            raise WarehauserError('product is None.', WarehauserErrorCodes.NONE_NOT_ALLOWED, {'self': model})

        # Make sure the ProductDefs of self and product are the same.
        if model.dfn != product.dfn:
            raise WarehauserError('self.dfn value does not match product.dfn.', WarehauserErrorCodes.DFN_MISMATCH, {'self.dfn': model.dfn, 'product.dfn': product.dfn})

        # If the stock expires before the self stock expires then log error and raise exception
        if model.expires != product.expires:
            msg = 'Not allowed to mix stock with mismatching expires.'
            data = {'self.expires': model.expires, 'product.expires': product.expires}

            model.log(level=logging.ERROR, msg=msg, extra=data)
            raise WarehauserError(msg, WarehauserErrorCodes.PRODUCT_EXPIRES_MISMATCH, data)

    @classmethod
    def post_join(cls, model, product):
        pass

    @classmethod
    def pre_split(cls, model, dfn, quantity):
        cls.check_status(model)
        cls.check_not_none(instance=model, msg=f'quantity is None.', extra={'self': model})

        if quantity > model.quantity:
            raise WarehauserError(msg=f'Not enough quantity in warehause to perform split.',
                                  code=WarehauserErrorCodes.WAREHAUSE_QUANTITY_LOW,
                                  extra={'self': model, 'quantity': quantity})

        if quantity <= float(0.0):
            raise WarehauserError(msg=f'quantity must be a positive float value.',
                                  code=WarehauserErrorCodes.BAD_PARAMETER,
                                  extra={'self': model, 'quantity': quantity})

        pass

    @classmethod
    def post_split(cls, model, dfn, quantity, result):
        pass


# Event callback
class EventCallback(ModelCallback):
    @classmethod
    def pre_process(cls, event):
        pass

    @classmethod
    def post_process(cls, event):
        pass
