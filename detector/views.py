from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from detector.cycles import detect_cycles
from detector.fanout import detect_fanout


@api_view(["GET"])
def health(request):
    return Response(
        {
            "status": "ok",
            "service": "wexa-ai",
        }
    )


@api_view(["GET"])
def cycles(request):
    try:
        results = detect_cycles()

        return Response(
            {
                "count": len(results),
                "cycles": results,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as exc:
        return Response(
            {
                "error": "Failed to detect cycles",
                "detail": str(exc),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def fanout(request):
    try:
        results = detect_fanout()

        return Response(
            {
                "count": len(results),
                "detections": results,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as exc:
        return Response(
            {
                "error": "Failed to detect fan-out patterns",
                "detail": str(exc),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
