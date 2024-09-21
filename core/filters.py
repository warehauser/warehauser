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

# filters.py

from django_filters import rest_framework as filters

from core.models import *

# Each model has a options field that is defined as a JSONField.
# Use these KEY_OPTIONS_* arrays to declare what fields you want in
# options to be searchable from the respective FilterSet.
# Format: ['key1', 'key2',...]
KEYS_OPTIONS_WAREHAUSEDEF  = ['values',]
KEYS_OPTIONS_WAREHAUSE     = ['values',]
KEYS_OPTIONS_PRODUCTDEF    = ['values',]
KEYS_OPTIONS_PRODUCT       = ['values',]
KEYS_OPTIONS_EVENTDEF      = ['values',]
KEYS_OPTIONS_EVENT         = ['values',]

FILTER_FIELDS_STANDARD     = {
    'id':          ['exact', 'lt', 'lte', 'gt', 'gte',],
    'external_id': ['exact', 'isnull',],
    'key':         ['iexact',],
    'created_at':  ['exact', 'lt', 'lte', 'gt', 'gte',],
    'updated_at':  ['exact', 'isnull', 'lt', 'lte', 'gt', 'gte',],
    'schema':      ['exact', 'isnull',],
    'options':     ['exact', 'isnull',],
    'is_virtual':  ['exact',],
}

FILTER_FIELDS_DEF_STANDARD = {
    **FILTER_FIELDS_STANDARD,
}

FILTER_FIELDS_INSTANCE_STANDARD = {
    **FILTER_FIELDS_STANDARD,
    'dfn': ['exact',],
    'value': ['exact',],
    'status': ['exact', 'lt', 'lte', 'gt', 'gte',],
    'parent': ['exact', 'isnull',],
}

def init_filters_help(fs, array):
    for key in array:
        fs.filters[f'options__{key}'] = filters.CharFilter(field_name=f'options__{key}', lookup_expr='icontains')
        fs.filters[f'options__{key}__exclude'] = filters.CharFilter(field_name=f'options__{key}', lookup_expr='icontains', exclude=True)
        fs.filters[f'options__{key}__isnull'] = filters.BooleanFilter(field_name=f'options__{key}', lookup_expr='isnull')
        fs.filters[f'options__{key}__isnotnull'] = filters.BooleanFilter(field_name=f'options__{key}', lookup_expr='isnull', exclude=True)
        fs.filters[f'options__{key}__lt'] = filters.NumberFilter(field_name=f'options__{key}', lookup_expr='lt')
        fs.filters[f'options__{key}__lte'] = filters.NumberFilter(field_name=f'options__{key}', lookup_expr='lte')
        fs.filters[f'options__{key}__gt'] = filters.NumberFilter(field_name=f'options__{key}', lookup_expr='gt')
        fs.filters[f'options__{key}__gte'] = filters.NumberFilter(field_name=f'options__{key}', lookup_expr='gte')

class WarehauserFilterSet(filters.FilterSet):
    class Meta:
        filter_overrides = {
            models.JSONField: {
                'filter_class': filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


# WAREHAUSE filters

FILTER_FIELDS_WAREHAUSE_COMMON = {
    'is_storage': ['exact',],
    'is_mobile': ['exact',],
    'is_permissive': ['exact',],
    'max_weight': ['exact', 'lt', 'lte', 'gt', 'gte',],
    'max_height': ['exact', 'lt', 'lte', 'gt', 'gte',],
    'max_width': ['exact', 'lt', 'lte', 'gt', 'gte',],
    'tare_length': ['exact', 'lt', 'lte', 'gt', 'gte',],
    'tare_weight': ['exact', 'lt', 'lte', 'gt', 'gte',],
    'tare_height': ['exact', 'lt', 'lte', 'gt', 'gte',],
    'tare_width': ['exact', 'lt', 'lte', 'gt', 'gte',],
    'tare_length': ['exact', 'lt', 'lte', 'gt', 'gte',],
}

class WarehauseDefFilter(WarehauserFilterSet):
    class Meta(WarehauserFilterSet.Meta):
        model = WarehauseDef
        fields = {
            **FILTER_FIELDS_DEF_STANDARD,
            **FILTER_FIELDS_WAREHAUSE_COMMON,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        init_filters_help(self, KEYS_OPTIONS_WAREHAUSEDEF)

class WarehauseFilter(WarehauserFilterSet):
    class Meta(WarehauserFilterSet.Meta):
        model = Warehause
        fields = {
            **FILTER_FIELDS_INSTANCE_STANDARD,
            **FILTER_FIELDS_WAREHAUSE_COMMON,
            'user': ['exact', 'isnull',],
            'stock': ['exact', 'isnull',],
            'stock_min': ['exact', 'lt', 'lte', 'gt', 'gte', 'isnull',],
            'stock_max': ['exact', 'lt', 'lte', 'gt', 'gte', 'isnull',],
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        init_filters_help(self, KEYS_OPTIONS_WAREHAUSE)


# PRODUCT filters

FILTER_FIELDS_PRODUCT_COMMON = {
    'code_count': ['exact', 'lt', 'lte', 'gt', 'gte',],
    'is_fragile': ['exact',],
    'is_up': ['exact',],
    'is_expires': ['exact',],
    'weight': ['exact', 'isnull', 'lt', 'lte', 'gt', 'gte',],
    'height': ['exact', 'isnull', 'lt', 'lte', 'gt', 'gte',],
    'width': ['exact', 'isnull', 'lt', 'lte', 'gt', 'gte',],
    'length': ['exact', 'isnull', 'lt', 'lte', 'gt', 'gte',],
}

class ProductDefFilter(WarehauserFilterSet):
    class Meta(WarehauserFilterSet.Meta):
        model = ProductDef
        fields = {
            **FILTER_FIELDS_DEF_STANDARD,
            **FILTER_FIELDS_PRODUCT_COMMON,
            'atomic': ['exact', 'lt', 'lte', 'gt', 'gte',],
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        init_filters_help(self, KEYS_OPTIONS_PRODUCTDEF)

class ProductFilter(WarehauserFilterSet):
    class Meta(WarehauserFilterSet.Meta):
        model = Product
        fields = {
            **FILTER_FIELDS_INSTANCE_STANDARD,
            **FILTER_FIELDS_PRODUCT_COMMON,
            'quantity': ['exact', 'isnull', 'lt', 'lte', 'gt', 'gte',],
            # 'reserved': ['exact', 'lt', 'lte', 'gt', 'gte', 'isnull',],
            'expires': ['exact', 'isnull', 'lt', 'lte', 'gt', 'gte',],
            'is_damaged': ['exact',],
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        init_filters_help(self, KEYS_OPTIONS_PRODUCT)


# EVENT filters

FILTER_FIELDS_EVENT_COMMON = {
    'is_batched': ['exact',],
    'proc_name': ['exact', 'isnull',]
}

class EventDefFilter(WarehauserFilterSet):
    class Meta(WarehauserFilterSet.Meta):
        model = EventDef
        fields = {
            **FILTER_FIELDS_DEF_STANDARD,
            **FILTER_FIELDS_EVENT_COMMON,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        init_filters_help(self, KEYS_OPTIONS_EVENTDEF)

class EventFilter(WarehauserFilterSet):
    class Meta(WarehauserFilterSet.Meta):
        model = Event
        fields = {
            **FILTER_FIELDS_INSTANCE_STANDARD,
            **FILTER_FIELDS_EVENT_COMMON,
            'warehause': ['exact',],
            'user': ['exact', 'isnull',],
            'proc_start': ['exact', 'isnull', 'lt', 'lte', 'gt', 'gte',],
            'proc_end': ['exact', 'isnull', 'lt', 'lte', 'gt', 'gte',],
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        init_filters_help(self, KEYS_OPTIONS_EVENT)
