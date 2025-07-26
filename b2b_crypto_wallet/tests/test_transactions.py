from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Wallet, Transaction


class TransactionAPITests(APITestCase):
    """
    Tests for the Transaction API endpoint.
    Covers create, list, retrieve, destroy operations, and balance integrity.
    """

    def setUp(self):
        """Set up test data before each test method."""
        self.wallet = Wallet.objects.create(label='Test Wallet', balance=Decimal('100.00'))
        self.list_url = reverse('api:transaction-list')
        self.detail_url = lambda pk: reverse('api:transaction-detail', kwargs={'pk': pk})

    def _create_transaction_via_api(self, txid: str, amount: Decimal, wallet_id: int):
        """
        Helper function to create a transaction via API.
        """
        data = {
            'data': {
                'type': 'Transaction',
                'attributes': {'txid': txid, 'amount': str(amount)},
                'relationships': {
                    'wallet': {'data': {'type': 'Wallet', 'id': str(wallet_id)}}
                }
            }
        }
        return self.client.post(self.list_url, data)

    def test_create_deposit_transaction_updates_balance(self):
        """
        Positive case: Creating a deposit transaction correctly updates the balance.
        """
        response = self._create_transaction_via_api('deposit-tx-1', Decimal('50.0'), self.wallet.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('150.00'))
        self.assertEqual(Transaction.objects.count(), 1)

    def test_create_withdrawal_transaction_updates_balance(self):
        """
        Positive case: Creating a withdrawal transaction correctly updates the balance.
        """
        response = self._create_transaction_via_api('withdrawal-tx-1', Decimal('-25.0'), self.wallet.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('75.00'))

    def test_create_transaction_fails_with_negative_balance(self):
        """
        Negative case: Attempting to create a transaction that would result in a negative balance.
        """
        response = self._create_transaction_via_api('overdraft-tx-1', Decimal('-101.0'), self.wallet.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('100.00'))
        self.assertEqual(Transaction.objects.count(), 0)  # No transaction should be created

        error = response.json()['errors']
        self.assertIn('amount', error)
        self.assertIn('negative wallet balance', error['amount'][0])

    def test_create_transaction_duplicate_txid_fails(self):
        """
        Negative case: Attempting to create a transaction with an already existing 'txid'.
        """
        self._create_transaction_via_api('unique-txid', Decimal('10.0'), self.wallet.id)

        response = self._create_transaction_via_api('unique-txid', Decimal('20.0'), self.wallet.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

        error = response.json()['errors']

        self.assertIn('txid', error)
        self.assertIn('txid already exists', error['txid'][0])

    def test_create_transaction_for_nonexistent_wallet_fails(self):
        """
        Negative case: Attempting to create a transaction for a non-existent wallet.
        """
        non_existent_wallet_id = self.wallet.id + 999
        response = self._create_transaction_via_api('tx-for-ghost-wallet', Decimal('10.0'), non_existent_wallet_id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

        error = response.json()['errors']
        self.assertIn('wallet', error)
        self.assertIn('does not exist', error['wallet'][0])

    def test_delete_transaction_reverts_balance(self):
        """
        Positive case: Deleting a transaction correctly reverts the balance.
        """
        create_response = self._create_transaction_via_api('tx-to-delete', Decimal('50.0'), self.wallet.id)
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED, create_response.content)
        tx_id = create_response.json()['data']['id']
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('150.00'))

        url = reverse('api:transaction-detail', kwargs={'pk': tx_id})
        delete_response = self.client.delete(url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT, delete_response.content)

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('100.00'))
        self.assertEqual(Transaction.objects.count(), 0)

    def test_delete_deposit_transaction_fails_if_balance_goes_negative(self):
        """
        Negative case: Attempting to delete a deposit transaction if it would lead to a negative balance.
        """
        # Start with a wallet with a specific balance
        wallet_test = Wallet.objects.create(label="Test Wallet For Delete", balance=Decimal('50.00'))
        # Create a deposit transaction
        create_response = self._create_transaction_via_api('deposit-to-delete', Decimal('100.00'), wallet_test.id)
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED, create_response.content)
        deposit_tx_id = create_response.json()['data']['id']
        wallet_test.refresh_from_db()
        self.assertEqual(wallet_test.balance, Decimal('150.00'))

        # Create a withdrawal transaction that brings balance down, but still positive
        self._create_transaction_via_api('withdrawal-after-deposit', Decimal('-140.00'), wallet_test.id)
        wallet_test.refresh_from_db()
        self.assertEqual(wallet_test.balance, Decimal('10.00'))

        url = reverse('api:transaction-detail', kwargs={'pk': deposit_tx_id})
        delete_response = self.client.delete(url)

        self.assertEqual(delete_response.status_code, status.HTTP_400_BAD_REQUEST, delete_response.content)
        wallet_test.refresh_from_db()
        self.assertEqual(wallet_test.balance, Decimal('10.00'))
        self.assertEqual(Transaction.objects.filter(wallet=wallet_test).count(), 2)

        error = delete_response.json()['errors']
        self.assertIn('non_field_errors', error)
        self.assertIn('negative wallet balance', error['non_field_errors'][0])

    def test_transaction_amount_precision(self):
        """Ensure transaction amount precision is handled correctly."""
        amount_precise = Decimal('12345.123456789012345678')
        response = self._create_transaction_via_api('txn-precise-006', amount_precise, self.wallet.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        new_tx = Transaction.objects.get(txid="txn-precise-006")
        self.assertEqual(new_tx.amount, amount_precise)

        amount_too_precise = Decimal('0.1234567890123456789')
        url = reverse('api:transaction-list')
        data = {
            'data': {
                'type': 'Transaction',
                'attributes': {'txid': 'txn-too-precise-007', 'amount': str(amount_too_precise)},
                'relationships': {
                    'wallet': {'data': {'type': 'Wallet', 'id': str(self.wallet.id)}}
                }
            }
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)
        error = response.json()['errors']
        self.assertIn('amount', error)
        self.assertIn('more than 18 decimal places', error['amount'][0])
