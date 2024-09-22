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

# tests.py

import os
import logging
import pprint

from django.forms.models import model_to_dict
from django.contrib.auth.models import Group, User
from django.test import TestCase

from .callbacks import WarehauseDefCallback, WarehauseCallback, ProductDefCallback, ProductCallback, EventDefCallback, EventCallback
from .models import WarehauseDef, Warehause, ProductDef, Product, EventDef, Event, Client
from .utils import WarehauserError

# Create your tests here.

class WarehauserTestCase(TestCase):
    def setUp(self):
        self.group:Group = Group.objects.create(name='demo')
        self.user:User = User.objects.create(username='demo', password='testpassword', email='test@email.com')
        self.user.groups.add(self.group)
        self.owner:Client = Client.objects.create(
            group = self.group,
        )

        # Create the Warehouse WarehauseDef
        data = {
            'key': 'Warehouse',
            'is_mobile': False,
            'is_storage': False,
            'owner': self.owner,
        }
        self.warehouse_dfn:WarehauseDef = WarehauseDef.objects.create(**data)

        # Create the Bin WarehauseDef
        self.loadingarea_dfn:WarehauseDef = WarehauseDef.objects.create(
            key = 'Loading Area',
            is_mobile = False,
            is_storage = False,
            owner = self.owner,
        )

        # Create the Bin WarehauseDef
        self.bin_dfn:WarehauseDef = WarehauseDef.objects.create(
            key = 'Bin',
            is_mobile = False,
            is_storage = True,
            is_permissive = False,
            owner = self.owner,
        )

        # Create the Bin WarehauseDef
        self.package_dfn:WarehauseDef = WarehauseDef.objects.create(
            key = 'Package',
            is_mobile = False,
            is_storage = True,
            is_permissive = True,
            owner = self.owner,
        )

        # Create the Bin WarehauseDef
        self.transport_dfn:WarehauseDef = WarehauseDef.objects.create(
            key = 'Transport',
            is_mobile = True,
            is_storage = False,
            owner = self.owner,
        )

        # Create a Chocolate Bar ProductDef
        self.chocolatebar_dfn:ProductDef = ProductDef.objects.create(
            key = 'Chocolate Bar',
            code_count = 1,
            atomic = None,
            is_fragile = True,
            is_up = False,
            is_expires = False,
            weight = 0.2,
            height = 0.025,
            width = 0.025,
            length = 0.1,
            owner = self.owner,
        )

        # Create a Virtual ProductDef
        self.virtual_product_dfn:ProductDef = ProductDef.objects.create(
            key = 'Virtual',
            code_count = 1,
            atomic = None,
            is_virtual = True,
            owner = self.owner,
        )

        # Create a purchase order EventDef
        data = {
            'key': 'PurchaseOrder',
            'is_batched': False,
            'proc_name': None,
            'owner': self.owner,
        }
        self.purchaseorder_dfn:EventDef = EventDef.objects.create(**data)

        # Create a customer order EventDef
        data['key'] = 'CustomerOrder'
        self.customerorder_dfn:EventDef = EventDef.objects.create(**data)

        # Create a inbound EventDef
        data['key'] = 'Inbound'
        data['proc_name'] = 'inbound'
        self.inbound_dfn:EventDef = EventDef.objects.create(**data)

        # Create a outbound EventDef
        data['key'] = 'Outbound'
        data['proc_name'] = 'outbound'
        self.outbound_dfn:EventDef = EventDef.objects.create(**data)

        # Create a transfer EventDef
        data['key'] = 'Transfer'
        data['proc_name'] = 'demo.tasks.transfer'
        self.transfer_dfn:EventDef = EventDef.objects.create(**data)

        # Create a Warehouse Warehause
        self.warehouse:Warehause = self.warehouse_dfn.create_instance(data={
            'value': '123 Moving Way, Sydney, NSW, Australia, 2000',
            'owner': self.owner,
        })

        # Create a Dock A Loading Area Warehause
        self.loadingarea:Warehause = self.loadingarea_dfn.create_instance(data={
            'value': 'Dock A',
            'parent': self.warehouse,
            'owner': self.owner,
        })

        # Create a Bin Warehause
        self.bin_A10_01_01:Warehause = self.bin_dfn.create_instance(data={
            'value': 'A01-01-01',
            'parent': self.warehouse,
            'owner': self.owner,
        })

class TestCase00001(WarehauserTestCase):
    def setUp(self):
        super().setUp()

        # Create a Chocolate Bar Product
        self.product = self.chocolatebar_dfn.create_instance(data={
            'value': 'Chocolate Bar',
            'quantity': 10.0,
            'warehause': self.bin_A10_01_01,
            'owner': self.owner,
        })

    def test_0001(self):
        """
        Test: split reduces quantity and creates a new product with the split quantity.
        """
        original_quantity = self.product.quantity
        split_quantity = 3.0
        new_quantity = original_quantity - split_quantity

        # Check initial quantity
        self.assertEqual(self.product.quantity, original_quantity)

        # Split three (3) items from product
        reserved = self.product.split(quantity=split_quantity)

        # Check reserved is not saved (no primary key)
        self.assertIsNone(reserved.id)

        # Check reserved parent is self.product
        self.assertEqual(reserved.parent, self.product)

        # Check reserved warehause is self.product.warehause
        self.assertEqual(reserved.warehause, self.product.warehause)

        # Check product has reduced the quantity
        self.assertEqual(self.product.quantity, new_quantity)

        # Check reserved quantity is split_quantity
        self.assertEqual(reserved.quantity, split_quantity)

    def test_0002(self):
        """Test that splitting with an invalid quantity raises an Exception."""
        with self.assertRaises(Exception):
            # Try splitting a quantity greater than the current product quantity
            self.product.split(quantity=15.0)

        with self.assertRaises(Exception):
            # Try splitting a non-positive quantity
            self.product.split(quantity=-5.0)

        with self.assertRaises(Exception):
            # Try splitting a zero quantity
            self.product.split(quantity=0.0)

class TestCase00002(WarehauserTestCase):
    def setUp(self):
        super().setUp()

        # Create a Chocolate Bar Product
        self.product:Product = self.chocolatebar_dfn.create_instance(data={
            'value': 'Chocolate Bar',
            'quantity': 10.0,
            'warehause': self.bin_A10_01_01,
            'owner': self.owner,
        })

    def test_0001(self):
        """
        Test: Get stock tests.
        """
        pqty = self.product.quantity
        rqty = 1.0
        stock:Product = self.bin_A10_01_01.get_stock(dfn=self.product.dfn)

        self.assertIsNone(stock.parent, 'Stock parent is None')
        self.assertEqual(stock.quantity, pqty, f'Stock quantity is {pqty}')

        with stock.mutex():
            reserved = self.bin_A10_01_01.reserve(dfn=self.chocolatebar_dfn, quantity=rqty)

            self.assertEqual(stock.id, reserved.parent.id, 'Reserved parent and stock IDs are equal')

            stock = self.bin_A10_01_01.get_stock(dfn=self.product.dfn)

        self.assertEqual(stock, reserved.parent, 'Reserved parent is stock')
        self.assertEqual(reserved.dfn, stock.dfn, 'Stock and reserved are the same ProductDef')
        self.assertEqual(reserved.quantity, rqty, msg=f'Reserved product quantity is {rqty}')
        self.assertEqual(stock.quantity, pqty - rqty, f'Stock quantity is {pqty-rqty}')

        with stock.mutex():
            reserved.warehause.unreserve(product=reserved)

            stock = self.bin_A10_01_01.get_stock(dfn=self.product.dfn)

        self.assertEqual(stock.quantity, pqty, 'Reserved has been unreserved and quantity added back to stock.')

class TestCase00003(WarehauserTestCase):
    def setUp(self):
        """
        Test: Create a package warehause with chocolate bars and widgets and test get_stock function
        """
        super().setUp()

        self.package:Warehause = self.package_dfn.create_instance(data={
            'value': 'package 001',
            'parent': self.warehouse,
            'owner': self.owner,
        })

        self.chocolatebar_001:Product = self.chocolatebar_dfn.create_instance(data={
            'value': 'Chocolate Bar',
            'quantity': 10.0,
            'warehause': self.package,
            'owner': self.owner,
        })

        self.widget_001:Product = self.virtual_product_dfn.create_instance(data={
            'value': 'Widget',
            'quantity': 1.0,
            'warehause': self.package,
            'owner': self.owner,
        })

    def test_0002(self):
        stock = self.package.get_stock(dfn=None)
        self.assertEqual(stock.count(), 2)

        reserved = self.package.reserve(dfn=self.virtual_product_dfn, quantity=1.0)

        stock = self.package.get_stock(dfn=None,seed_only=False)
        self.assertEqual(stock.count(), 3)

        stock = self.package.get_stock(dfn=None,seed_only=True)
        for s in stock:
            self.assertIsNone(s.parent)

        stock = self.package.get_stock(dfn=self.virtual_product_dfn,seed_only=False)
        self.assertEqual(stock.count(), 2)
        for s in stock:
            self.assertEqual(s.dfn, self.virtual_product_dfn)

class TestCase00003(WarehauserTestCase):
    def setUp(self):
        """
        Test: create and run an Purchase Order event
        """
        super().setUp()

    def test_0001(self):

        data = {
            'value': '01 Purchase Order',
            'options': {
                'supplier': 'Chocolates R Us',
                'items': [{
                    'external_id': 'SKU001',
                    'dfn': str(self.chocolatebar_dfn.id),
                    'quantity': 1.0,
                },],
            },
            'parent': None,
        }

        purchase_order_event = self.purchaseorder_dfn.create_instance(data=data)
        self.assertTrue(isinstance(purchase_order_event, Event))
        self.assertIsNotNone(purchase_order_event.id)
        self.assertIsNotNone(purchase_order_event.options)

        options = purchase_order_event.options
        self.assertTrue('supplier' in options)
        self.assertEqual(options['supplier'], 'Chocolates R Us')

        self.assertTrue('items' in options)
        items = options['items']
        self.assertTrue(isinstance(items, list))

        for i in items:
            self.assertTrue('dfn' in i)
            self.assertTrue('quantity' in i)

        data = {
            'value': '02 Transport 001 Arrival',
            'options': {
                'dfn': str(self.transport_dfn.id),
                'data': {
                    'value': 'ABC-123',
                    'parent': str(self.loadingarea.id),
                },
            },
            'parent': purchase_order_event,
        }

        inbound_event_transport_001 = self.inbound_dfn.create_instance(data=data)
        self.assertIsNotNone(inbound_event_transport_001.options['result'])
        self.assertTrue('result' in inbound_event_transport_001.options)
        self.assertTrue('id' in inbound_event_transport_001.options['result'])

        transport_001 = Warehause.objects.get(id=inbound_event_transport_001.options['result']['id'])

        data = {
            'value': '03 Pallet 001 Inbound',
            'options': {
                'dfn': str(self.package_dfn.id),
                'data': {
                    'value': 'pallet_001',
                    'parent': str(self.loadingarea.id),
                    'options': {
                        'origin': str(transport_001.id),
                        'nonbound': True,
                    },
                },
            },
            'parent': inbound_event_transport_001,
        }

        inbound_event_pallet_001 = self.inbound_dfn.create_instance(data=data)

        pallet_001 = Warehause.objects.get(id=inbound_event_pallet_001.options['result']['id'])

        self.assertEqual(pallet_001.options['origin'], str(transport_001.id))

        # Transport 001 (truck) leaves...
        data = {
            'value': '04 Transport 001 Departure',
            'warehause': self.loadingarea,
            'options': {
                'warehause': str(transport_001.id),
            },
            'parent': inbound_event_transport_001,
        }

        outbound_event_transport_001 = self.outbound_dfn.create_instance(data=data)

        with self.assertRaises(Warehause.DoesNotExist):
            transport_001 = Warehause.objects.get(id=transport_001.id)

        print('transport departed.')

        data = {
            'value': '05 Package 002 Inbound',
            'options': {
                'dfn': str(self.package_dfn.id),
                'data': {
                    'value': 'package_002',
                    'parent': str(self.loadingarea.id),
                    'options': {
                        'origin': str(self.loadingarea.id),
                    },
                },
            },
            'parent': purchase_order_event,
        }

        inbound_event_package_002 = self.inbound_dfn.create_instance(data=data)
        package_002 = Warehause.objects.get(id=inbound_event_package_002.options['result']['id'])

        data = {
            'value': '06 Product 0001 Transfer 0001 from Pallet 001 to Package 002',
            'options': {
                'dfn': str(self.chocolatebar_dfn.id),
                'from_warehause': str(pallet_001.id),
                'to_warehause': str(package_002.id),
                'quantity': 1.0,
            },
            'parent': purchase_order_event,
        }

        transfer_event_product_0001 = self.transfer_dfn.create_instance(data=data)
        package_002 = Warehause.objects.get(id=transfer_event_product_0001.options['result']['warehause'])

        self.assertEqual(package_002.get_stock(dfn=self.chocolatebar_dfn,seed_only=False).quantity, 1.0)

        data = {
            'value': '07 Pallet 001 Departure',
            'warehause': self.loadingarea,
            'options': {
                'warehause': str(pallet_001.id),
            },
            'parent': inbound_event_pallet_001,
        }

        outbound_event_pallet_001 = self.outbound_dfn.create_instance(data=data)

        data = {
            'value': '08 Product 0001 Transfer from Package 002 to Bin A01-01-01',
            'options': {
                'dfn': str(self.chocolatebar_dfn.id),
                'from_warehause': str(package_002.id),
                'to_warehause': str(self.bin_A10_01_01.id),
                'quantity': 1.0,
            },
            'parent': purchase_order_event,
        }

        transfer_event_product_0002 = self.transfer_dfn.create_instance(data=data)
        bin = Warehause.objects.get(id=transfer_event_product_0002.options['result']['warehause'])

        self.assertEqual(bin.get_stock(dfn=self.chocolatebar_dfn,seed_only=False).quantity, 1.0)
        self.assertEqual(package_002.get_stock(dfn=self.chocolatebar_dfn,seed_only=False).quantity, 0.0)

        # A Customer orders a chocolate bar
        data = {
            'value': '09 John Smith, 1 Sunny Street, Sydney, NSW, 2000, Australia',
            'options': {
                'items': [{
                    'dfn': str(self.chocolatebar_dfn.id),
                    'quantity': 1.0,
                },],
            },
        }

        customer_order_event = self.customerorder_dfn.create_instance(data=data)

        data = {
            'value': '10 Product 0001 Transfer 0003 from Bin A01-01-01 to Package 002',
            'options': {
                'dfn': str(self.chocolatebar_dfn.id),
                'from_warehause': str(self.bin_A10_01_01.id),
                'to_warehause': str(package_002.id),
                'quantity': 1.0,
            },
            'parent': customer_order_event,
        }

        transfer_event_product_0003 = self.transfer_dfn.create_instance(data=data)
        bin = Warehause.objects.get(id=transfer_event_product_0003.options['result']['warehause'])

        data = {
            'value': '11 Transport 002 Arrival',
            'options': {
                'dfn': str(self.transport_dfn.id),
                'data': {
                    'value': 'XYZ-098',
                    'parent': str(self.loadingarea.id),
                },
            },
            'parent': customer_order_event,
        }

        inbound_event_transport_002 = self.inbound_dfn.create_instance(data=data)
        self.assertIsNotNone(inbound_event_transport_002.options['result'])
        self.assertTrue('result' in inbound_event_transport_002.options)
        self.assertTrue('id' in inbound_event_transport_002.options['result'])

        transport_002 = Warehause.objects.get(id=inbound_event_transport_002.options['result']['id'])

        # Transfer the package to transport_002
        data = {
            'value': '12 Package 0002 transfer 0004 Package 002 to Transport 002',
            'options': {
                'from_warehause': str(package_002.id),
                'to_warehause': str(transport_002.id),
            },
            'parent': customer_order_event,
        }

        transfer_event_product_0004 = self.transfer_dfn.create_instance(data=data)

        # Transport 002 departure
        data = {
            'value': '13 Transport 002 Departure',
            'warehause': self.loadingarea,
            'options': {
                'warehause': str(transport_002.id),
            },
            'parent': inbound_event_transport_002,
        }

        outbound_event_transport_002 = self.outbound_dfn.create_instance(data=data)

        with self.assertRaises(Warehause.DoesNotExist):
            transport_002 = Warehause.objects.get(id=transport_002.id)

        with self.assertRaises(Warehause.DoesNotExist):
            package_002 = Warehause.objects.get(id=package_002.id)

        print('Warehause objects:')
        for w in Warehause.objects.all():
            pprint.pprint(w)

        print('Product objects:')
        for p in Product.objects.all():
            print(p.warehause.value)
            pprint.pprint(p)

        print('Event objects:')
        for e in Event.objects.all():
            pprint.pprint(e)




