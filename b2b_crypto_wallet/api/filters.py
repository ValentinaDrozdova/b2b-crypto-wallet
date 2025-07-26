import django_filters
from .models import Wallet, Transaction


class WalletFilter(django_filters.FilterSet):
    """FilterSet for the Wallet."""
    # Filter by label
    label = django_filters.CharFilter(
        field_name='label',
        lookup_expr='icontains',
        help_text="Filter by a part of the wallet label (case-insensitive)."
    )
    # Filters for balance ranges
    balance_gt = django_filters.NumberFilter(
        field_name='balance',
        lookup_expr='gt',
        help_text="Wallets with balance greater than the specified value."
    )
    balance_lt = django_filters.NumberFilter(
        field_name='balance',
        lookup_expr='lt',
        help_text="Wallets with balance less than the specified value."
    )
    balance_gte = django_filters.NumberFilter(
        field_name='balance',
        lookup_expr='gte',
        help_text="Wallets with balance greater than or equal to the specified value."
    )
    balance_lte = django_filters.NumberFilter(
        field_name='balance',
        lookup_expr='lte',
        help_text="Wallets with balance less than or equal to the specified value."
    )

    class Meta:
        model = Wallet
        fields = [
            'label',
            'balance_gt',
            'balance_lt',
            'balance_gte',
            'balance_lte',
        ]


class TransactionFilter(django_filters.FilterSet):
    """FilterSet for the Transaction."""
    # Filter by Wallet ID (exact match)
    wallet = django_filters.NumberFilter(  # use NumberFilter for ID lookup
        field_name='wallet__id',
        lookup_expr='exact',
        help_text="Filter by Wallet ID."
    )
    # Filter by transaction ID
    txid = django_filters.CharFilter(
        field_name='txid',
        lookup_expr='icontains',
        help_text="Filter by Transaction ID (partial, case-insensitive match)."
    )
    # Filters for amount ranges
    amount_gt = django_filters.NumberFilter(
        field_name='amount',
        lookup_expr='gt',
        help_text="Transactions with amount greater than the specified value."
    )
    amount_lt = django_filters.NumberFilter(
        field_name='amount',
        lookup_expr='lt',
        help_text="Transactions with amount less than the specified value."
    )
    amount_gte = django_filters.NumberFilter(
        field_name='amount',
        lookup_expr='gte',
        help_text="Transactions with amount greater than or equal to the specified value."
    )
    amount_lte = django_filters.NumberFilter(
        field_name='amount',
        lookup_expr='lte',
        help_text="Transactions with amount less than or equal to the specified value."
    )
    # Filters for timestamp ranges
    timestamp_gte = django_filters.DateTimeFilter(
        field_name='timestamp',
        lookup_expr='gte',
        help_text="Transactions created on or after the specified date/time (ISO 8601 format)."
    )
    timestamp_lte = django_filters.DateTimeFilter(
        field_name='timestamp',
        lookup_expr='lte',
        help_text="Transactions created on or before the specified date/time (ISO 8601 format)."
    )

    class Meta:
        model = Transaction
        fields = [
            'wallet',
            'txid',
            'amount_gt',
            'amount_lt',
            'amount_gte',
            'amount_lte',
            'timestamp_gte',
            'timestamp_lte',
        ]
