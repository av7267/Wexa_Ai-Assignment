from django.urls import path

from detector.views import (
    health,
    account_list,
    account_detail,
    account_transactions,
    transaction_count,
    detection_cycles,
    detection_fanout,
)


urlpatterns = [
    path(
        "health",
        health,
        name="health",
    ),

    path(
        "accounts",
        account_list,
        name="account-list",
    ),

    path(
        "accounts/<str:account_id>",
        account_detail,
        name="account-detail",
    ),

    path(
        "accounts/<str:account_id>/transactions",
        account_transactions,
        name="account-transactions",
    ),

    path(
        "transactions",
        transaction_count,
        name="transaction-count",
    ),

    path(
        "detections/cycles",
        detection_cycles,
        name="detection-cycles",
    ),

    path(
        "detections/fanout",
        detection_fanout,
        name="detection-fanout",
    ),
]
