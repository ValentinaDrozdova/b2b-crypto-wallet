from rest_framework.routers import DefaultRouter
from django.urls import include, path

from .views import WalletViewSet, TransactionViewSet
app_name = 'api'

router = DefaultRouter()

router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]
