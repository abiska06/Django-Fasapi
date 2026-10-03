from django.db import models


class PredictionRecord(models.Model):
    """
    Stores every reading submitted through the portal along with the verdict
    returned by the FastAPI hazard-prediction microservice. This is the
    "prediction history" piece the Django side owns, per the pipeline's
    suggested integration (FastAPI stays stateless; Django keeps the record).
    """

    # --- Inputs sent to the ML microservice (all normalized 0-1) ---
    conductance_max = models.FloatField()
    conductance_min = models.FloatField()
    conductance_mean = models.FloatField()
    ph_max = models.FloatField()
    ph_min = models.FloatField()
    do_max = models.FloatField()
    do_mean = models.FloatField()
    temp_mean = models.FloatField()

    # --- Verdict returned by the microservice ---
    predicted_ph = models.FloatField()
    is_hazard = models.BooleanField()
    hazard_probability = models.FloatField()
    hazard_lower_bound = models.FloatField(null=True, blank=True)
    hazard_upper_bound = models.FloatField(null=True, blank=True)

    # --- Bookkeeping ---
    site_label = models.CharField(max_length=120, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        verdict = "HAZARD" if self.is_hazard else "safe"
        label = self.site_label or "Reading"
        return f"{label} @ {self.created_at:%Y-%m-%d %H:%M} — {verdict}"
