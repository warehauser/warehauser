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

from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'password',]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = self.Meta.model.objects.create_user(**validated_data)
        return user

def to_related_representation(instance, representation, related_fields):
    for field_name in related_fields:
        related_instance = getattr(instance, field_name, None)
        if related_instance:
            representation[field_name] = {
                'id': related_instance.id,
                'decr': related_instance.descr
            }

    return representation

class RelatedFieldSerializer(serializers.PrimaryKeyRelatedField):
    def to_representation(self, value):
        if value is None:
            return None
        return super().to_representation(value)

warehausedef_related_field_serializer = RelatedFieldSerializer(queryset=WarehauseDef.objects.all())
warehause_related_field_serializer    = RelatedFieldSerializer(queryset=Warehause.objects.all())

productdef_related_field_serializer   = RelatedFieldSerializer(queryset=ProductDef.objects.all())
product_related_field_serializer      = RelatedFieldSerializer(queryset=Product.objects.all())

eventdef_related_field_serializer     = RelatedFieldSerializer(queryset=EventDef.objects.all())
event_related_field_serializer        = RelatedFieldSerializer(queryset=Event.objects.all())

user_related_field_serializer         = RelatedFieldSerializer(queryset=get_user_model().objects.all())

class AbstractSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        for key in validated_data:
            if key == 'updated_at':
                continue
            else:
                instance.__dict__[key] = validated_data.get(key, instance.__dict__[key])
        instance.updated_at = timezone.now()
        instance.save()
        return instance

class AbstractDefSerializer(AbstractSerializer):
    def to_representation(self, instance):
        if instance is None:
            return None

        return to_related_representation(instance, super().to_representation(instance), ['parent'])
        # representation = super().to_representation(instance)
        # related_fields = ['parent']  # Add other related field names here as needed

        # for field_name in related_fields:
        #     related_instance = getattr(instance, field_name, None)
        #     if related_instance:
        #         representation[field_name] = {
        #             'id': related_instance.id,
        #             'decr': related_instance.descr
        #         }

        # return representation

class AbstractInstSerializer(AbstractSerializer):
    pass


# Warehause model serializers

class WarehauseDefSerializer(AbstractDefSerializer):
    parent = warehausedef_related_field_serializer

    class Meta:
        model = WarehauseDef
        fields = '__all__'
        depth = 1

class WarehauseSerializer(AbstractInstSerializer):
    dfn    = warehausedef_related_field_serializer
    parent = warehause_related_field_serializer
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


# Product model serializers

class ProductDefSerializer(AbstractDefSerializer):
    parent = productdef_related_field_serializer

    class Meta:
        model = ProductDef
        fields = '__all__'
        depth = 1

class ProductSerializer(AbstractInstSerializer):
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


# Event model serializers

class EventDefSerializer(AbstractDefSerializer):
    parent = eventdef_related_field_serializer

    class Meta:
        model = EventDef
        fields = '__all__'
        depth = 1

class EventSerializer(AbstractInstSerializer):
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
