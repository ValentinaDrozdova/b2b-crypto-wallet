from typing import Type

from django.db import transaction as db_transaction
from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Transaction, Wallet


@receiver(post_save, sender=Transaction)  # type: ignore
def update_wallet_balance_on_transaction_save(
    sender: Type[Transaction], instance: Transaction, created: bool, **kwargs: dict
) -> None:
    """
    Signal receiver that incrementally updates the associated Wallet's balance
    after a Transaction is created.
    """
    if not created:
        return

    with db_transaction.atomic():
        (
            Wallet.objects.select_for_update()
            .filter(pk=instance.wallet.pk)
            .update(balance=F('balance') + instance.amount)
        )


@receiver(post_delete, sender=Transaction)  # type: ignore
def update_wallet_balance_on_transaction_delete(
    sender: Type[Transaction], instance: Transaction, **kwargs: dict
) -> None:
    """
    Signal receiver that incrementally updates the associated Wallet's balance
    after a Transaction is deleted.
    """
    with db_transaction.atomic():
        (
            Wallet.objects.select_for_update()
            .filter(pk=instance.wallet.pk)
            .update(balance=F('balance') - instance.amount)
        )
