import httpx
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .forms import SensorReadingForm
from .models import PredictionRecord


@require_http_methods(["GET", "POST"])
async def predict_view(request):
    """
    GET  -> render the empty sensor-reading form.
    POST -> validate the form, call the FastAPI microservice asynchronously
            (the request thread is never blocked on inference), persist the
            verdict, and render the result on the same page.

    This is the boundary described in the report: Django never touches the
    model directly. It only ever talks to FastAPI over HTTP, and every
    payload is validated twice — once by this Django form, once again by
    the Pydantic schema on the FastAPI side.
    """
    result = None

    if request.method == "POST":
        form = SensorReadingForm(request.POST)
        if form.is_valid():
            payload = form.to_payload()
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{settings.HAZARD_SERVICE_URL}/predict",
                        json=payload,
                    )
                response.raise_for_status()
                result = response.json()
            except httpx.ConnectError:
                messages.error(
                    request,
                    "Could not reach the ML microservice. Make sure "
                    "fastapi_service.py is running (see README) before "
                    "submitting a reading.",
                )
            except httpx.HTTPStatusError as exc:
                messages.error(
                    request,
                    f"The prediction service rejected the request: "
                    f"{exc.response.text}",
                )
            else:
                bounds = result.get("hazard_bounds_normalized_pH") or {}
                lower = bounds.get("lower") if isinstance(bounds, dict) else None
                upper = bounds.get("upper") if isinstance(bounds, dict) else None
                if lower is None and isinstance(bounds, (list, tuple)) and len(bounds) == 2:
                    lower, upper = bounds

                await PredictionRecord.objects.acreate(
                    site_label=form.cleaned_data.get("site_label", ""),
                    **payload,
                    predicted_ph=result["predicted_ph"],
                    is_hazard=result["is_hazard"],
                    hazard_probability=result["hazard_probability"],
                    hazard_lower_bound=lower,
                    hazard_upper_bound=upper,
                )
    else:
        form = SensorReadingForm()

    return render(
        request,
        "monitor/predict_form.html",
        {"form": form, "result": result},
    )


async def history_view(request):
    """Read-only list of every prediction made through the portal so far."""
    records = [record async for record in PredictionRecord.objects.all()[:100]]
    return render(request, "monitor/history.html", {"records": records})
