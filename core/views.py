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

# views.py

from django.http import Http404
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import JSONField
from django.utils import timezone

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import BasePermission

from .filters import *
from .models import *
from .serializers import *

# Create your views here.

def home_view(request):
    return render(request, "core/index.html")

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # Read permissions are allowed to any authenticated user,
        # so we'll always allow GET, HEAD, or OPTIONS requests.
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user and request.user.is_authenticated
        # Write permissions are only allowed to superusers.
        return request.user and request.user.is_superuser

# Model view sets

class WarehauserModelViewSet(viewsets.ModelViewSet):
    search_fields = ['id', 'external_id', 'options__barcodes__contains', 'barcode',]

    def _protect_fields(self, data):
        # Prevent altering id, updated_at, or created_at fields
        disallowed_fields = ['id', 'updated_at', 'created_at']
        for field in disallowed_fields:
            if field in data:
                return Response(
                    {"error": f"Cannot update field '{field}'"},
                    status=status.HTTP_400_BAD_REQUEST
                )

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        # Check if the URL parameter is an ID
        obj_id = None
        if lookup_url_kwarg in self.kwargs:
            obj_id = int(self.kwargs[lookup_url_kwarg])
            obj = self.get_queryset().filter(id=obj_id).first()

            # If object found by ID, return it
            if obj:
                return obj

        # If not found by ID or ID not provided, assume it's a barcode
        barcode = self.kwargs[lookup_url_kwarg]
        obj = self.get_queryset().filter(barcode=barcode).first()

        # If object found by barcode, return it
        if obj:
            return obj

        # If object not found by ID or barcode, raise a 404
        raise Http404()

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data

        self._protect_fields(data=data)

        # Check for field changes
        has_changed = False
        for key, value in data.items():
            # Check if the instance's current 'key' attribute is a JSONField
            attr = getattr(instance, key, None)
            if isinstance(attr, JSONField):
                # Update the JSONField attribute
                json = getattr(instance, key, dict())
                json.update(value)
                setattr(instance, key, json)
                has_changed = True
            elif attr != value:
                # Update regular field
                setattr(instance, key, value)
                has_changed = True

        if has_changed:
            instance.updated_at = timezone.now()
            instance.save()

            return Response(
                {"message": f"[Update]: {instance.__class__.__name__} {instance.id} updated."},
                status=status.HTTP_200_OK
            )

        return Response(
            {"message": f"[Update]: {instance.__class__.__name__} {instance.id} no change."},
            status=status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.delete()
        except ObjectDoesNotExist as e:
            return Response(data={'message': e.detail}, status=e.code)
        return Response(status=status.HTTP_204_NO_CONTENT)

class WarehauserDefModelViewSet(WarehauserModelViewSet):
    permission_classes = (IsAdminOrReadOnly,)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ('do_spawn',):
            # Only allow authenticated users for this custom action
            permission_classes = [IsAuthenticated]
        else:
            # Use the default permission classes for other actions
            permission_classes = self.permission_classes

        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data

        self._protect_fields(data=data)

        data['created_at'] = timezone.now()

        # Create a serializer instance with the updated data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Perform creation
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        return super().partial_update(self, request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        return super().destroy(self, request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def do_spawn(self, request, *args, **kwargs):
        dfn = self.get_object()
        data = request.data

        model = dfn.create_instance(data)
        model.save()

        serializer = self.serializer_class(model)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class WarehauserInstModelViewSet(WarehauserModelViewSet):
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        return Response({"error": f"Not implemented. Did you mean '/api/{self.DFNNAME}s/<id:int>/do_spawn'?"}, status=status.HTTP_501_NOT_IMPLEMENTED)


# WAREHAUSE viewsets

class WarehauseDefViewSet(WarehauserDefModelViewSet):
    serializer_class = WarehauseDefSerializer
    renderer_classes = [JSONRenderer,]
    lookup_field = 'id'

    # API filtering
    filter_backends = [DjangoFilterBackend, SearchFilter,]
    filterset_class = WarehauseDefFilter

    def get_queryset(self):
        return WarehauseDef.objects.all().order_by('created_at',)

class WarehauseViewSet(WarehauserInstModelViewSet):
    DFNNAME = 'warehausedef'
    serializer_class = WarehauseSerializer
    renderer_classes = [JSONRenderer,]
    lookup_field = 'id'

    # API filtering
    filter_backends = [DjangoFilterBackend, SearchFilter,]
    filterset_class = WarehauseFilter

    def get_queryset(self):
        return Warehause.objects.all().order_by('created_at')


# PRODUCT viewsets

class ProductDefViewSet(WarehauserDefModelViewSet):
    serializer_class = ProductDefSerializer
    renderer_classes = [JSONRenderer,]
    lookup_field = 'id'

    # API filtering
    filter_backends = [DjangoFilterBackend, SearchFilter,]
    filterset_class = ProductDefFilter

    def get_queryset(self):
        return ProductDef.objects.all().order_by('created_at',)

    @action(detail=True, methods=['get'], url_path='warehauses')
    def get_warehauses(self, request, id=None):
        product_def = self.get_object()
        warehauses = product_def.get_warehauses()
        print(f'ProductDefViewSet.get_warehauses(self, request, id=None)')
        print(warehauses)
        serializer = WarehauseSerializer(warehauses, many=True)
        return Response(serializer.data)

class ProductViewSet(WarehauserInstModelViewSet):
    DFNNAME = 'productdef'
    serializer_class = ProductSerializer
    renderer_classes = [JSONRenderer,]
    lookup_field = 'id'

    # API filtering
    filter_backends = [DjangoFilterBackend, SearchFilter,]
    filterset_class = ProductFilter

    def get_queryset(self):
        return Product.objects.all().order_by('created_at',)


# EVENT viewsets

class EventDefViewSet(WarehauserDefModelViewSet):
    serializer_class = EventDefSerializer
    renderer_classes = [JSONRenderer,]
    lookup_field = 'id'

    # API filtering
    filter_backends = [DjangoFilterBackend, SearchFilter,]
    filterset_class = EventDefFilter

    def get_queryset(self):
        return EventDef.objects.all().order_by('created_at',)

    @action(detail=True, methods=['post'])
    def do_spawn(self, request, *args, **kwargs):
        data = request.data

        # register the user to this event
        try:
            del data['user']
        except KeyError:
            pass

        data['user_id'] = request.user.id

        # Create the event
        event = self.get_object().create_instance(data)

        if not event.is_batched:
            # process immediately
            event.process()
        else:
            event.save()

        return Response(EventSerializer(event).data)

class EventViewSet(WarehauserInstModelViewSet):
    DFNNAME = 'eventdef'
    serializer_class = EventSerializer
    renderer_classes = [JSONRenderer,]
    lookup_field = 'id'

    # API filtering
    filter_backends = [DjangoFilterBackend, SearchFilter,]
    filterset_class = EventFilter

    def get_queryset(self):
        return Event.objects.all().order_by('created_at',)
