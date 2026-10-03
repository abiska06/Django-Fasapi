from django import forms


class SensorReadingForm(forms.Form):
    """
    Mirrors the `SensorReading` Pydantic model in fastapi_service.py exactly —
    same field names, same 0-1 normalized range — so the dict this form
    produces can be sent to the microservice unmodified.
    """

    site_label = forms.CharField(
        label="Site / sample label",
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g. Site 14 — Chattahoochee"}),
    )

    conductance_max = forms.FloatField(
        label="Conductance (max)", min_value=0, max_value=1,
        help_text="Normalized specific conductance, daily maximum",
    )
    conductance_min = forms.FloatField(
        label="Conductance (min)", min_value=0, max_value=1,
        help_text="Normalized specific conductance, daily minimum",
    )
    conductance_mean = forms.FloatField(
        label="Conductance (mean)", min_value=0, max_value=1,
        help_text="Normalized specific conductance, daily mean",
    )
    ph_max = forms.FloatField(
        label="pH (max)", min_value=0, max_value=1,
        help_text="Normalized pH, daily maximum",
    )
    ph_min = forms.FloatField(
        label="pH (min)", min_value=0, max_value=1,
        help_text="Normalized pH, daily minimum",
    )
    do_max = forms.FloatField(
        label="Dissolved oxygen (max)", min_value=0, max_value=1,
        help_text="Normalized dissolved oxygen, daily maximum",
    )
    do_mean = forms.FloatField(
        label="Dissolved oxygen (mean)", min_value=0, max_value=1,
        help_text="Normalized dissolved oxygen, daily mean",
    )
    temp_mean = forms.FloatField(
        label="Water temperature (mean)", min_value=0, max_value=1,
        help_text="Normalized water temperature, daily mean",
    )

    def to_payload(self) -> dict:
        """Return exactly the dict the FastAPI /predict endpoint expects."""
        data = self.cleaned_data
        return {
            "conductance_max": data["conductance_max"],
            "conductance_min": data["conductance_min"],
            "conductance_mean": data["conductance_mean"],
            "ph_max": data["ph_max"],
            "ph_min": data["ph_min"],
            "do_max": data["do_max"],
            "do_mean": data["do_mean"],
            "temp_mean": data["temp_mean"],
        }
