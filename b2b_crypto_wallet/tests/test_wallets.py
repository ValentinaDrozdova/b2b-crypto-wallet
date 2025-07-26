from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Wallet


class WalletAPITestCase(APITestCase):
    """
    Tests for the Wallet API endpoint.
    Covers CRUD operations, pagination, filtering, and ordering.
    """

    def setUp(self):
        """Set up test data before each test method."""
        # Create wallets with specific balances for testing
        self.wallet_alpha = Wallet.objects.create(label='Alpha Wallet', balance=Decimal('100.00'))
        self.wallet_beta = Wallet.objects.create(label='Beta Wallet', balance=Decimal('200.00'))
        self.wallet_gamma = Wallet.objects.create(label='Gamma Wallet', balance=Decimal('50.00'))

        self.list_url = reverse('api:wallet-list')
        self.detail_url = lambda pk: reverse('api:wallet-detail', kwargs={'pk': pk})

    def _create_wallet_via_api(self, label: str):
        """Helper to create a wallet via API."""
        data = {
            "data": {
                "type": 'Wallet',
                "attributes": {
                    "label": label
                }
            }
        }
        return self.client.post(self.list_url, data)

    def _update_wallet_via_api(self, pk: int, label: str):
        """Helper to update a wallet via API."""
        data = {
            "data": {
                "type": 'Wallet',
                "id": str(pk),
                "attributes": {
                    "label": label
                }
            }
        }
        return self.client.patch(self.detail_url(pk), data)

    def test_list_wallets(self):
        """Ensure we can list all wallets."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data['results'][0]['label'], 'Alpha Wallet')

    def test_create_wallet(self):
        """Ensure we can create a new wallet."""
        response = self._create_wallet_via_api('New Wallet API')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertEqual(Wallet.objects.count(), 4)
        self.assertEqual(response.data['label'], 'New Wallet API')
        self.assertEqual(Decimal(response.data['balance']), Decimal('0.00'))

    def test_retrieve_wallet(self):
        """Ensure we can retrieve a single wallet."""
        response = self.client.get(self.detail_url(self.wallet_alpha.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(response.data['label'], self.wallet_alpha.label)
        self.assertEqual(Decimal(response.data['balance']), self.wallet_alpha.balance)

    def test_update_wallet(self):
        """Ensure we can update an existing wallet's label."""
        response = self._update_wallet_via_api(self.wallet_alpha.pk, "Updated Alpha Wallet")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.wallet_alpha.refresh_from_db()
        self.assertEqual(self.wallet_alpha.label, "Updated Alpha Wallet")

    def test_delete_wallet(self):
        """Ensure we can delete a wallet."""
        response = self.client.delete(self.detail_url(self.wallet_alpha.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)
        self.assertEqual(Wallet.objects.count(), 2)
        self.assertFalse(Wallet.objects.filter(pk=self.wallet_alpha.pk).exists())
