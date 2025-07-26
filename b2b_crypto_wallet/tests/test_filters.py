from decimal import Decimal
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Wallet, Transaction


class FilterAPITests(APITestCase):
    """
    Tests for the filtering functionality of the Wallet and Transaction endpoints.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Creates test data once for the entire test class.
        This is more efficient than setUp, as the data does not change.
        """
        # --- Wallets ---
        cls.wallet_alpha = Wallet.objects.create(label="Alpha Wallet", balance=Decimal('100.00'))
        cls.wallet_beta = Wallet.objects.create(label="Beta Wallet", balance=Decimal('200.00'))
        cls.wallet_gamma = Wallet.objects.create(label="Gamma Special", balance=Decimal('300.00'))

        # --- Transactions ---
        now = timezone.now()
        cls.tx1 = Transaction.objects.create(
            wallet=cls.wallet_alpha, txid="TXID_ALPHA_01", amount=Decimal('100.00')
        )
        # Set timestamps manually for predictable filtering
        cls.tx1.timestamp = now - timedelta(days=2)
        cls.tx1.save()

        cls.tx2 = Transaction.objects.create(
            wallet=cls.wallet_beta, txid="TXID_BETA_01", amount=Decimal('-50.00')
        )
        cls.tx2.timestamp = now - timedelta(days=1)
        cls.tx2.save()

        cls.tx3 = Transaction.objects.create(
            wallet=cls.wallet_beta, txid="TXID_BETA_02_SPECIAL", amount=Decimal('250.00')
        )
        cls.tx3.timestamp = now
        cls.tx3.save()

    # --- Tests for WalletFilter ---

    def test_filter_wallet_by_label_icontains(self):
        """Test: filter wallets by partial match on label."""
        url = f"{reverse('api:wallet-list')}?filter[label]=wallet"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)

        url = f"{reverse('api:wallet-list')}?filter[label]=special"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 1)
        self.assertEqual(response.json()['data'][0]['attributes']['label'], "Gamma Special")

    def test_filter_wallet_by_balance_range(self):
        """Test: filter wallets by balance range."""
        # Balance > 150
        url = f"{reverse('api:wallet-list')}?filter[balance_gt]=150"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 3)

        # Balance < 250
        url = f"{reverse('api:wallet-list')}?filter[balance_lt]=250"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 1)

        # Balance >= 200
        url = f"{reverse('api:wallet-list')}?filter[balance_gte]=200"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 3)

        # Balance <= 200
        url = f"{reverse('api:wallet-list')}?filter[balance_lte]=200"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 1)

    # --- Tests for TransactionFilter ---

    def test_filter_transaction_by_wallet_id(self):
        """Test: filter transactions by exact wallet ID."""
        url = f"{reverse('api:transaction-list')}?filter[wallet]={self.wallet_beta.pk}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 2)
        txids = {item['attributes']['txid'] for item in data}
        self.assertIn("TXID_BETA_01", txids)
        self.assertIn("TXID_BETA_02_SPECIAL", txids)

    def test_filter_transaction_by_txid_icontains(self):
        """Test: filter transactions by partial match on txid."""
        url = f"{reverse('api:transaction-list')}?filter[txid]=beta"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)

    def test_filter_transaction_by_amount_range(self):
        """Test: filter transactions by amount range."""
        # Amount > 0
        url = f"{reverse('api:transaction-list')}?filter[amount_gt]=0"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)

        # Amount < 0
        url = f"{reverse('api:transaction-list')}?filter[amount_lt]=0"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 1)
        self.assertEqual(response.json()['data'][0]['attributes']['txid'], "TXID_BETA_01")

    def test_combined_filters(self):
        """Test: combining multiple filters for a precise query."""
        url = f"{reverse('api:transaction-list')}?filter[wallet]={self.wallet_beta.pk}&filter[amount_gt]=0"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['attributes']['txid'], "TXID_BETA_02_SPECIAL")
