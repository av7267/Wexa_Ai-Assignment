from rest_framework.decorators import api_view
from rest_framework.response import Response

from detector.db import run_query

from detector.queries import (
    ACCOUNT_COUNT_QUERY,
    TRANSACTION_COUNT_QUERY,
    ACCOUNT_LIST_QUERY,
    ACCOUNT_DETAIL_QUERY,
    ACCOUNT_NEIGHBORHOOD_QUERY,
)

from detector.cycles import detect_cycles
from detector.fanout import detect_fanout
from detector.convergence import detect_convergence


def _serialize_account(row):
    created_at = row.get("created_at")

    return {
        "id": row["id"],
        "name": row["name"],
        "account_type": row["account_type"],
        "created_at": (
            created_at.to_native().isoformat()
            if created_at
            else None
        ),
    }


def _serialize_tx(entry):
    ts = entry.get("timestamp")

    return {
        "account_id": entry.get("account_id"),
        "account_name": entry.get("account_name"),
        "transaction_id": entry.get("transaction_id"),
        "amount": entry.get("amount"),
        "timestamp": (
            ts.to_native().isoformat()
            if ts
            else None
        ),
    }


@api_view(["GET"])
def health(request):
    try:
        run_query("RETURN 1")

        return Response({
            "status": "ok",
            "database": "connected",
        })

    except Exception:
        return Response(
            {
                "status": "error",
                "database": "unavailable",
            },
            status=503,
        )


@api_view(["GET"])
def account_list(request):
    try:
        rows = run_query(ACCOUNT_LIST_QUERY)

    except Exception:
        return Response(
            {"error": "database unavailable"},
            status=503,
        )

    return Response(
        [_serialize_account(row) for row in rows]
    )


@api_view(["GET"])
def account_detail(request, account_id):
    try:
        rows = run_query(
            ACCOUNT_DETAIL_QUERY,
            {"account_id": account_id},
        )

    except Exception:
        return Response(
            {"error": "database unavailable"},
            status=503,
        )

    if not rows:
        return Response(
            {"error": "account not found"},
            status=404,
        )

    return Response(_serialize_account(rows[0]))


@api_view(["GET"])
def account_transactions(request, account_id):
    try:
        exists = run_query(
            ACCOUNT_DETAIL_QUERY,
            {"account_id": account_id},
        )

        if not exists:
            return Response(
                {"error": "account not found"},
                status=404,
            )

        rows = run_query(
            ACCOUNT_NEIGHBORHOOD_QUERY,
            {"account_id": account_id},
        )

    except Exception:
        return Response(
            {"error": "database unavailable"},
            status=503,
        )

    if not rows:
        return Response({
            "account": {
                "id": account_id,
            },
            "outgoing": [],
            "incoming": [],
        })

    row = rows[0]

    outgoing = [
        _serialize_tx(entry)
        for entry in row["outgoing"]
        if entry.get("account_id")
    ]

    incoming = [
        _serialize_tx(entry)
        for entry in row["incoming"]
        if entry.get("account_id")
    ]

    return Response({
        "account": {
            "id": account_id,
        },
        "outgoing": outgoing,
        "incoming": incoming,
    })


@api_view(["GET"])
def transaction_count(request):
    try:
        rows = run_query(TRANSACTION_COUNT_QUERY)

    except Exception:
        return Response(
            {"error": "database unavailable"},
            status=503,
        )

    count = 0

    if rows:
        count = rows[0].get("transaction_count", 0)

    return Response({
        "transaction_count": count,
    })


@api_view(["GET"])
def detection_cycles(request):
    try:
        cycles = detect_cycles()

        return Response({
            "count": len(cycles),
            "cycles": cycles,
        })

    except Exception:
        return Response(
            {"error": "database unavailable"},
            status=503,
        )


@api_view(["GET"])
def detection_fanout(request):
    try:
        fanout_results = detect_fanout()
        convergence_results = detect_convergence()

        return Response({
            "fanout": {
                "count": len(fanout_results),
                "detections": fanout_results,
            },
            "convergence": {
                "count": len(convergence_results),
                "detections": convergence_results,
            },
        })

    except Exception:
        return Response(
            {"error": "database unavailable"},
            status=503,
        )
