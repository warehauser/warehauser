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

# serializers.py

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers
from django.utils.translation import gettext as _

from .models import *

def to_related_representation(instance, representation, related_fields):
    for field_name in related_fields:
        related_instance = getattr(instance, field_name, None)
        if related_instance:
            representation[field_name] = {
                'id': related_instance.id,
                'key': related_instance.key
            }

    return representation

class RelatedFieldSerializer(serializers.PrimaryKeyRelatedField):
    def to_representation(self, value):
        if value is None:
            return None
        return super().to_representation(value)

owner_related_field_serializer        = RelatedFieldSerializer(queryset=Client.objects.all())
warehausedef_related_field_serializer = RelatedFieldSerializer(queryset=WarehauseDef.objects.all())
warehause_related_field_serializer    = RelatedFieldSerializer(queryset=Warehause.objects.all())

productdef_related_field_serializer   = RelatedFieldSerializer(queryset=ProductDef.objects.all())
product_related_field_serializer      = RelatedFieldSerializer(queryset=Product.objects.all())

eventdef_related_field_serializer     = RelatedFieldSerializer(queryset=EventDef.objects.all())
event_related_field_serializer        = RelatedFieldSerializer(queryset=Event.objects.all())

user_related_field_serializer         = RelatedFieldSerializer(queryset=get_user_model().objects.all())

# Warehause model serializers

class WarehauserSerializer(serializers.ModelSerializer):
    owner = owner_related_field_serializer

    def validate_owner(self, value):
        request = self.context.get('request')
        user = request.user

        if not user.is_staff and not user.is_superuser:
            # Ensure the owner is a Client that is referenced by the user's group
            client_groups = Client.objects.filter(group__in=user.groups.all())
            if value not in client_groups:
                raise serializers.ValidationError("You do not have access to this client.")

        return value

class WarehauseDefSerializer(WarehauserSerializer):
    class Meta:
        model = WarehauseDef
        fields = '__all__'
        extra_kwargs = {'parent': {'allow_null': True, 'required': False,},}
        depth = 1

class WarehauseSerializer(WarehauserSerializer):
    dfn    = warehausedef_related_field_serializer
    user   = user_related_field_serializer

    def create(self, validated_data):
        raise NotImplementedError('WarehauseSerializer.create(self,validated_data)')

    def to_representation(self, instance):
        if instance is None:
            return None

        representation = super().to_representation(instance)

        if instance.user:
            representation['user'] = {
                'id': instance.user.id,
                'username': instance.user.username
            }

        related_fields = ['parent', 'dfn']  # Add other related field names here as needed
        return to_related_representation(instance, representation, related_fields)

    class Meta:
        model = Warehause
        fields = '__all__'
        depth = 1
        extra_kwargs = {'parent': { 'allow_null': True, 'required': False,},}


# Product model serializers

class ProductDefSerializer(WarehauserSerializer):
    class Meta:
        model = ProductDef
        fields = '__all__'
        depth = 1
        extra_kwargs = {'parent': { 'allow_null': True, 'required': False,},}

class ProductSerializer(WarehauserSerializer):
    dfn       = productdef_related_field_serializer
    parent    = product_related_field_serializer
    warehause = warehause_related_field_serializer

    def create(self, validated_data):
        raise NotImplementedError('ProductSerializer.create(self,validated_data)')

    def to_representation(self, instance):
        if instance is None:
            return None

        representation = super().to_representation(instance)

        related_fields = ['parent', 'dfn', 'warehause']  # Add other related field names here as needed
        return to_related_representation(instance, representation, related_fields)

    class Meta:
        model = Product
        fields = '__all__'
        depth = 1
        extra_kwargs = {'parent': {'allow_null': True, 'required': False,},}


# Event model serializers

class EventDefSerializer(WarehauserSerializer):
    class Meta:
        model = EventDef
        fields = '__all__'
        depth = 1
        extra_kwargs = {'parent': {'allow_null': True, 'required': False,},}

class EventSerializer(WarehauserSerializer):
    dfn       = eventdef_related_field_serializer
    parent    = event_related_field_serializer
    warehause = warehause_related_field_serializer
    user      = user_related_field_serializer

    def create(self, validated_data):
        raise NotImplementedError('EventSerializer.create(self,validated_data)')

    def to_representation(self, instance):

        if instance is None:
            return None

        representation = super().to_representation(instance)

        if instance.user:
            representation['user'] = {
                'id': instance.user.id,
                'username': instance.user.username
            }

        related_fields = ['parent', 'dfn', 'warehause']  # Add other related field names here as needed
        return to_related_representation(instance, representation, related_fields)

    class Meta:
        model = Event
        fields = '__all__'
        depth = 1
        extra_kwargs = {'parent': { 'allow_null': True, 'required': False,},}

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'
