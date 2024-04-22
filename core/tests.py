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

import os
import logging

from django.test import TestCase
from .models import WarehauseDef, Warehause, ProductDef, Product, EventDef, Event
from .utils import WarehauserError, WarehauserErrorCodes

from .scripts.db.lib import search_for_data_and_upload

# Create your tests here.

# Tests:

# Warehause mapped, not permissive, no stock
# Warehause mapped, not permissive, stock
# Warehause mapped, permissive, no stock
# Warehause mapped, permissive, single stock
# Warehause mapped, permissive, stock chain
# Warehause not mapped, not permissive, no stock
# Warehause not mapped, not permissive, stock
# Warehause not mapped, permissive, no stock
# Warehause not mapped, permissive, single stock
# Warehause not mapped, permissive, stock chain

# receive product None
# receive product chain matched expires
# receive product mapped matched expires
# receive product not mapped matched expires
# receive product chain mismatched expires
# receive product mapped mismatched expires
# receive product not mapped mismatched expires

# -------------------------------------------------

# dispatch mapped
# dispatch not mapped

class WarehauseTestCase(TestCase):
    warehause: Warehause     = None
    inbound_area: Warehause  = None
    outbound_area: Warehause = None
    storage_area: Warehause  = None
    no_mapped_products_area: Warehause = None

    bins = list()
    unmapped_bins = list()
    product_chains = list()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        logging.disable(logging.CRITICAL)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, 'scripts/db/data/test')

        search_for_data_and_upload(data_dir=data_dir,archive=False)

        # Product chain 1: 10 'Candy Bar'
        dfn = ProductDef.objects.get(descr="Candy Bar")
        child = dfn.create_instance({"quantity": 10})
        child.save()

        cls.product_chains.append(child)

        # Product chain 2: 1 'Candy Bar', 4 'Grapes, Red'
        dfn = ProductDef.objects.get(descr="Candy Bar")
        parent = dfn.create_instance({"quantity": 1})
        parent.save()

        dfn = ProductDef.objects.get(descr="Grapes, Red")
        child = dfn.create_instance({"quantity": 4, "parent": parent})
        child.save()

        cls.product_chains.append(child)

        # Product chain 3: 1 'Banana, Cavendish', 2 'Candy Bar', 2 'Milk, Full Cream, 1L'
        dfn = ProductDef.objects.get(descr="Banana, Cavendish")
        parent = dfn.create_instance({"quantity": 1})
        parent.save()

        dfn = ProductDef.objects.get(descr="Candy Bar")
        child = dfn.create_instance({"quantity": 2, "parent": parent})
        child.save()
        parent = child

        dfn = ProductDef.objects.get(descr="Milk, Full Cream, 1L")
        child = dfn.create_instance({"quantity": 2, "parent": parent})
        child.save()

        cls.product_chains.append(child)

        # Product chain 4: 2 'Milk, Full Cream, 1L' (to be pre received at an unmapped_bin)
        dfn = ProductDef.objects.get(descr="Milk, Full Cream, 1L")
        child = dfn.create_instance({"quantity": 4, "parent": None})
        child.save()

        cls.product_chains.append(child)

        # Product chain 5: 2 'Grapes, Red'
        dfn = ProductDef.objects.get(descr="Grapes, Red")
        child = dfn.create_instance({"quantity": 2, "parent": None})
        child.save()

        cls.product_chains.append(child)

        dfn = WarehauseDef.objects.get(id=1)
        cls.warehouse : Warehause = dfn.create_instance()
        cls.warehouse.save()

        dfn = WarehauseDef.objects.get(id=2)
        cls.inbound_area : Warehause = dfn.create_instance({"parent": cls.warehouse})
        cls.inbound_area.save()

        dfn = WarehauseDef.objects.get(id=3)
        cls.outbound_area : Warehause = dfn.create_instance({"parent": cls.warehouse})
        cls.outbound_area.save()

        dfn = WarehauseDef.objects.get(id=4)
        cls.storage_area : Warehause = dfn.create_instance({"parent": cls.warehouse})
        cls.storage_area.save()

        dfn = WarehauseDef.objects.get(id=4)
        cls.no_mapped_products_area : Warehause = dfn.create_instance({"parent": cls.warehouse})
        cls.no_mapped_products_area.save()

        dfn = WarehauseDef.objects.get(id=5)
        bin : Warehause = dfn.create_instance({"parent": cls.storage_area, "barcode": "A01-01-01-01-01"})
        bin.save()
        cls.bins.append(bin)

        bin : Warehause = dfn.create_instance({"parent": cls.storage_area, "barcode": "A01-01-01-01-02"})
        bin.save()
        cls.bins.append(bin)

        bin : Warehause = dfn.create_instance({"parent": cls.storage_area, "barcode": "A01-01-01-01-03"})
        bin.save()
        cls.bins.append(bin)

        bin : Warehause = dfn.create_instance({"parent": cls.storage_area, "barcode": "A01-01-01-01-04"})
        bin.save()
        cls.bins.append(bin)

        bin : Warehause = dfn.create_instance({"parent": cls.storage_area, "barcode": "A01-01-02-01-01"})
        bin.save()
        cls.bins.append(bin)

        bin : Warehause = dfn.create_instance({"parent": cls.storage_area, "barcode": "A01-01-02-01-02"})
        bin.save()
        cls.bins.append(bin)

        bin : Warehause = dfn.create_instance({"parent": cls.storage_area, "barcode": "A01-01-02-01-03"})
        bin.save()
        cls.bins.append(bin)

        bin : Warehause = dfn.create_instance({"parent": cls.storage_area, "barcode": "A01-01-02-01-04"})
        bin.save()
        cls.bins.append(bin)

        bin : Warehause = dfn.create_instance({"parent": cls.no_mapped_products_area, "barcode": "A02-01-01-01-01"})
        bin.save()
        cls.unmapped_bins.append(bin)

        bin : Warehause = dfn.create_instance({"parent": cls.no_mapped_products_area, "barcode": "A02-01-01-01-02"})
        bin.save()
        cls.unmapped_bins.append(bin)

        bin : Warehause = dfn.create_instance({"parent": cls.no_mapped_products_area, "barcode": "A02-01-01-01-03", "stock": cls.product_chains[1]})
        bin.save()
        cls.unmapped_bins.append(bin)

        bin : Warehause = dfn.create_instance({"parent": cls.no_mapped_products_area, "barcode": "A02-01-01-01-04", "stock": cls.product_chains[3]})
        bin.save()
        cls.unmapped_bins.append(bin)

        dfn = ProductDef.objects.get(descr="Banana, Cavendish")
        dfn.map.add(cls.storage_area)
        dfn.save()

        dfn = ProductDef.objects.get(descr="Milk, Full Cream, 1L")
        dfn.map.add(cls.bins[0])
        dfn.map.add(cls.bins[1])
        dfn.save()

        dfn = ProductDef.objects.get(descr="Candy Bar")
        dfn.map.add(cls.bins[2])
        dfn.save()

    def setUp(self):
        pass

    def test_001_receive_none_product(self):
        # Assert that the warehause's receive raises error with None as the product.
        with self.assertRaises(WarehauserError) as cm:
            # Call the receive method with None as the product
            self.bins[0].receive(None)

        self.assertEqual(cm.exception.code, WarehauserErrorCodes.NONE_NOT_ALLOWED)

    def test_002_receive_product_chain(self):
        with self.assertRaises(WarehauserError) as cm:
            self.bins[0].receive(self.product_chains[1])

        self.assertEqual(cm.exception.code, WarehauserErrorCodes.WAREHAUSE_RECEIVE_CHAIN_NOT_ALLOWED)

    def test_003_receive_product_to_unmapped_warehause(self):
        self.unmapped_bins[0].receive(self.product_chains[0])
        self.assertEqual(self.unmapped_bins[0].stock, self.product_chains[0])

    def test_004_receive_to_non_empty_bin_success(self):
        product = self.product_chains[4]
        warehause = self.unmapped_bins[2]
        stock = warehause.find_stock(product.dfn)

        self.assertEqual(warehause.is_permissive, False)
        self.assertIsNotNone(stock)

        product_before = product.quantity

        stock_before = warehause.stock.quantity
        result = warehause.receive(product)
        stock_after = result.quantity

        self.assertEqual(stock_after-stock_before,product_before)
        self.assertEqual(warehause.stock.dfn.id, product.dfn.id)

    def test_005_receive_to_empty_non_permissive_bin_success(self):
        self.bins[0].receive(self.product_chains[0])
        self.assertEquals(self.bins[0].is_permissive, False)
        self.assertEqual(self.bins[0].stock, self.product_chains[0])

    def test_006_dispatch_permissive_success(self):
        dfn: ProductDef = ProductDef.objects.get(descr="Milk, Full Cream, 1L")
        warehause: Warehause = self.unmapped_bins[-1]
        get_quantity = float(1.0)
        stock: Product = warehause.get_stock(dfn=dfn)

        before_quantity = stock.quantity
        warehause.reserve(quantity=get_quantity)
        self.assertEqual(stock.reserved,get_quantity)

        product: Product = warehause.dispatch(dfn=dfn, quantity=get_quantity)

        self.assertEqual(stock.reserved, float(0.0))
        self.assertEqual(stock.quantity, before_quantity-get_quantity)
        self.assertEqual(product.quantity, get_quantity)

    def tearDown(self):
        return super().tearDown()
    