from rest_framework_json_api.serializers import HyperlinkedModelSerializer
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework import serializers
from .models import Wallet, Transaction
from decimal import Decimal


class WalletSerializer(HyperlinkedModelSerializer):
    """
    Serializer for the Wallet.
    Handles serialization/deserialization of Wallet objects following JSON:API specification.
    """
    id = serializers.CharField(read_only=True)

    class Meta:
        model = Wallet
        fields = ('id', 'label', 'balance')
        read_only_fields = ('balance',)  # Balance is automatically managed


class TransactionSerializer(HyperlinkedModelSerializer):
    """
    Serializer for the Transaction model.
    Handles serialization/deserialization of Transaction objects following JSON:API specification.
    Includes validation for amount and ensures wallet balance constraints.
    """
    id = serializers.CharField(read_only=True)

    # Define wallet as a JSON:API relationship field
    wallet = ResourceRelatedField(
        queryset=Wallet.objects.all(),
        related_link_url_kwarg='pk',  # The URL keyword argument for the detail view's primary key.
        read_only=False,  # Allows setting the wallet during creation/update
        required=True,  # Wallet is a required field for a transaction
        help_text="The wallet to which this transaction belongs. (JSON:API relationship)"
    )

    class Meta:
        model = Transaction
        fields = ('id', 'wallet', 'txid', 'amount', 'timestamp')
        read_only_fields = ('timestamp',)

    def validate_amount(self, value: Decimal) -> Decimal:
        """
        Validates that the amount has no more than 18 decimal places.
        This is a pre-check before model's clean method handles balance constraints.
        """
        if not isinstance(value, Decimal):
            try:  # type: ignore
                value = Decimal(str(value))
            except Exception:
                raise serializers.ValidationError("Invalid amount format.")

        if value.as_tuple().exponent < -18:  # type: ignore
            raise serializers.ValidationError("Amount cannot have more than 18 decimal places.")
        return value

    def validate_txid(self, value: str) -> str:
        """
        Validates that the txid is unique when creating a new transaction.
        For updates, it only checks uniqueness if the txid is being changed.
        """
        # Get the instance being updated, if any
        instance = getattr(self, 'instance', None)

        # Check for uniqueness only if creating or if txid is changed during update
        if instance is None or instance.txid != value:
            if Transaction.objects.filter(txid=value).exists():
                raise serializers.ValidationError("Transaction with this txid already exists.")
        return value

    def create(self, validated_data):
        """
        Custom create method to handle the wallet relationship correctly.
        Crucially, it calls full_clean() on the instance to trigger model-level validation,
        including the negative balance check.
        """
        wallet_instance = validated_data.pop('wallet')

        # Create the Transaction instance without saving yet
        transaction_instance = Transaction(wallet=wallet_instance, **validated_data)

        # Call full_clean() to run all model validation, including the clean() method
        # which contains the critical negative balance check and select_for_update.
        transaction_instance.full_clean()

        # Save the instance after successful validation
        transaction_instance.save()  # type: ignore
        return transaction_instance

    def update(self, instance, validated_data):
        """
        Custom update method to handle the wallet relationship correctly.
        This also calls full_clean() to ensure model-level validation is applied.
        """
        # Handle wallet relationship update if provided
        if 'wallet' in validated_data:
            instance.wallet = validated_data.pop('wallet')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Call full_clean() to run all model validation before saving
        instance.full_clean()
        instance.save()  # Call save to trigger model's clean()
        return instance
