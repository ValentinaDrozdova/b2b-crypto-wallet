from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from decimal import Decimal


class Wallet(models.Model):
    """
    The balance is a summary of all associated transaction amounts.
    """
    label = models.CharField(max_length=255, unique=True, help_text="A unique label for the wallet.")
    balance = models.DecimalField(
        max_digits=30,
        decimal_places=18,
        default=Decimal('0.00'),
        help_text="Current balance of the wallet, sum of all transactions. Cannot be negative."
    )

    class Meta:
        indexes = [models.Index(fields=['label']), ]
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"
        ordering = ['label']

    def __str__(self):
        return f"{self.label} (Balance: {self.balance})"

    def clean(self):
        """
        Custom validation for the Wallet model itself.
        Ensures that the balance cannot be set to a negative value directly.
        """
        super().clean()
        if self.balance < 0:
            raise ValidationError({'balance': 'Wallet balance cannot be negative.'})


class Transaction(models.Model):
    """
    Represents a transaction associated with a wallet.
    Transaction amounts can be positive (deposit) or negative (withdrawal).
    """
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,  # If a wallet is deleted, all its transactions are also deleted
        related_name='transactions',
        help_text="The wallet associated with this transaction."
    )
    txid = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,  # Add database index for faster unique checks and lookups
        help_text="Unique external transaction identifier."
    )
    amount = models.DecimalField(
        max_digits=30,
        decimal_places=18,
        help_text="The amount of the transaction. Can be positive (deposit) or negative (withdrawal)."
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp of the transaction."
    )

    class Meta:
        indexes = [models.Index(fields=['wallet']), ]
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['wallet', '-timestamp']

    def clean(self):
        """
        Custom validation for the Transaction model.
        Ensures that the wallet balance does not become negative after the transaction.
        This uses `select_for_update` to prevent race conditions during balance check and update.
        """
        super().clean()
        print(f"DEBUG: Transaction.clean() called for TXID: {self.txid}, Amount: {self.amount}")

        try:
            # Get the wallet using select_for_update() which locks the row
            wallet_instance = Wallet.objects.select_for_update().get(pk=self.wallet.pk)
            print(
                f"DEBUG: Wallet {wallet_instance.label} (ID: {wallet_instance.pk}) current balance: {wallet_instance.balance}")  # noqa: E501
        except Wallet.DoesNotExist:
            raise ValidationError({'wallet': 'The specified wallet does not exist.'})

        # Calculate the prospective balance based on whether it's a new or existing transaction
        if not self.pk:
            prospective_balance = wallet_instance.balance + self.amount
            print(f"DEBUG: New transaction. Prospective balance: {prospective_balance}")
        else:
            try:
                # Get the old amount of the transaction from the database
                old_transaction = Transaction.objects.get(pk=self.pk)
                amount_difference = self.amount - old_transaction.amount
                prospective_balance = wallet_instance.balance + amount_difference
                print(
                    f"DEBUG: Updating transaction. Old amount: {old_transaction.amount}, New amount: {self.amount}, Diff: {amount_difference}, Prospective balance: {prospective_balance}")  # noqa: E501
            except Transaction.DoesNotExist:
                raise ValidationError('Transaction for update not found.')

        # Check if the prospective balance would be negative
        if prospective_balance < 0:
            print(f"DEBUG: Prospective balance is negative: {prospective_balance}. Raising ValidationError.")
            raise ValidationError({'amount': 'Transaction would lead to a negative wallet balance.'})

    def save(self, *args, **kwargs):
        """
        Overrides the save method to ensure full validation is performed
        before the transaction is saved to the database.
        """
        print(f"DEBUG: Transaction.save() called for TXID: {self.txid}. Calling full_clean().")
        self.full_clean()  # This calls the clean() method defined above
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Overrides the delete method to ensure that deleting a transaction
        does not lead to a negative wallet balance.
        """
        with db_transaction.atomic():
            # Get the wallet instance with a lock before deletion
            wallet_instance = Wallet.objects.select_for_update().get(pk=self.wallet.pk)

            # Calculate the prospective balance after deleting this transaction
            prospective_balance = wallet_instance.balance - self.amount
            if prospective_balance < 0:
                raise ValidationError(
                    {'non_field_errors': 'Deleting this transaction would lead to a negative wallet balance.'})

            super().delete(*args, **kwargs)

    def __str__(self):
        return f"TXID: {self.txid} | Amount: {self.amount} | Wallet: {self.wallet.label}"
