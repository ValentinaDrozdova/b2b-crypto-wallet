from rest_framework_json_api.views import ModelViewSet
from rest_framework import mixins
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction as db_transaction
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework.viewsets import GenericViewSet

from .models import Wallet, Transaction
from .serializers import WalletSerializer, TransactionSerializer
from .filters import WalletFilter, TransactionFilter


@extend_schema_view(
    # Customize schema for specific actions within WalletViewSet
    list=extend_schema(
        summary="List all wallets",
        description="Retrieves a paginated list of all cryptocurrency wallets.",
        tags=["Wallets"]
    ),
    retrieve=extend_schema(
        summary="Retrieve a single wallet",
        description="Retrieves details of a specific cryptocurrency wallet by its ID.",
        tags=["Wallets"]
    ),
    create=extend_schema(
        summary="Create a new wallet",
        description="Creates a new cryptocurrency wallet.",
        tags=["Wallets"],
    ),
    partial_update=extend_schema(
        summary="Partially update a wallet",
        description="Partially updates an existing cryptocurrency wallet's details.",
        tags=["Wallets"],
    ),
    destroy=extend_schema(
        summary="Delete a wallet",
        description="Deletes a cryptocurrency wallet by its ID. Note: Deleting a wallet will also delete all associated transactions.",  # noqa: E501
        tags=["Wallets"]
    ),
)
class WalletViewSet(ModelViewSet):
    """
    ViewSet for Wallet.
    Provides CRUD operations with JSON:API compliance, pagination, filtering, and sorting.
    """
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer

    filterset_class = WalletFilter
    search_fields = ('label',)
    ordering_fields = ('label', 'balance',)  # Fields available for sorting

    lookup_field = 'pk'

    def perform_create(self, serializer):
        """
        Custom create operation to ensure model validation and transactional integrity.
        All database operations for creating a new object are wrapped in an atomic transaction.
        """
        with db_transaction.atomic():
            try:
                serializer.save()
            except DjangoValidationError as e:
                raise serializers.ValidationError(e.message_dict)

    def perform_update(self, serializer):
        """
        Custom update operation with transactional integrity and error handling.
        """
        with db_transaction.atomic():
            try:
                serializer.save()
            except DjangoValidationError as e:
                raise serializers.ValidationError(e.message_dict)

    def perform_destroy(self, instance):
        """
        Custom delete operation with transactional integrity and error handling.
        Ensures that model's clean() method (which checks balance before deletion) is respected
        """
        with db_transaction.atomic():
            try:
                instance.delete()
            except DjangoValidationError as e:
                detail_message = e.message_dict if hasattr(e, 'message_dict') else e.message
                raise serializers.ValidationError(detail_message)


@extend_schema_view(
    # Customize schema for specific actions within TransactionViewSet
    list=extend_schema(
        summary="List all transactions",
        description="Retrieves a paginated list of all cryptocurrency transactions.",
        tags=["Transactions"]
    ),
    retrieve=extend_schema(
        summary="Retrieve a single transaction",
        description="Retrieves details of a specific cryptocurrency transaction by its ID.",
        tags=["Transactions"]
    ),
    create=extend_schema(
        summary="Create a new transaction",
        description="Creates a new cryptocurrency transaction. This operation includes validation to prevent negative wallet balances.",  # noqa: E501
        tags=["Transactions"],
    ),
    destroy=extend_schema(
        summary="Delete a transaction",
        description="Deletes a cryptocurrency transaction by its ID. This operation includes validation to prevent negative wallet balances after deletion.",  # noqa: E501
        tags=["Transactions"]
    ),
)
class TransactionViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    """
    ViewSet for Transaction.
    Provides create, list, retrieve, and destroy actions.
    Updates are intentionally disabled as transactions are treated as immutable records.
    """
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filterset_class = TransactionFilter
    search_fields = ('txid',)
    ordering_fields = ('txid', 'amount', 'timestamp',)

    def perform_create(self, serializer):
        with db_transaction.atomic():
            try:
                serializer.save()
            except DjangoValidationError as e:
                raise serializers.ValidationError(e.message_dict)

    http_method_names = ['get', 'post', 'delete', 'head', 'options']  # Exclude 'put', 'patch'

    def perform_destroy(self, instance):
        with db_transaction.atomic():
            try:
                instance.delete()
            except DjangoValidationError as e:
                detail_message = e.message_dict if hasattr(e, 'message_dict') else e.message
                raise serializers.ValidationError(detail_message)
