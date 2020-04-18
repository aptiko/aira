from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from captcha.fields import CaptchaField
from geowidgets import LatLonField
from registration.forms import RegistrationForm

from .models import Agrifield, AppliedIrrigation, Profile


class ProfileForm(forms.ModelForm):
    supervisor = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__supervision_question=True), required=False
    )

    class Meta:
        model = Profile
        exclude = ("user",)

        labels = {
            "first_name": _("Given name"),
            "last_name": _("Family name"),
            "address": _("Address"),
            "notification": _("Frequency of email notifications"),
            "email_language": _("Email notification language"),
            "supervisor": _("Supervisor"),
            "supervision_question": _("Consider me as supervisor for other accounts"),
        }


class AgrifieldForm(forms.ModelForm):
    location = LatLonField(
        label=_("Co-ordinates"),
        help_text=_("Longitude and latitude in decimal degrees"),
    )

    class Meta:
        model = Agrifield
        exclude = ("owner",)
        fields = [
            "name",
            "area",
            "location",
            "crop_type",
            "irrigation_type",
            "is_virtual",
            "use_custom_parameters",
            "custom_irrigation_optimizer",
            "custom_root_depth_max",
            "custom_root_depth_min",
            "custom_max_allowed_depletion",
            "custom_efficiency",
            "custom_field_capacity",
            "custom_thetaS",
            "custom_wilting_point",
            "soil_analysis",
        ]

        labels = {
            "name": _("Field name"),
            "is_virtual": _("Is this a virtual field?"),
            "location": _("Co-ordinates"),
            "crop_type": _("Crop type"),
            "irrigation_type": _("Irrigation type"),
            "area": _("Irrigated area (m²)"),
            "use_custom_parameters": _("Use custom parameters"),
            "custom_irrigation_optimizer": _("Irrigation optimizer"),
            "custom_root_depth_max": _("Estimated root depth (max)"),
            "custom_root_depth_min": _("Estimated root depth (min)"),
            "custom_max_allowed_depletion": _("Maximum allowed depletion"),
            "custom_efficiency": _("Irrigation efficiency"),
            "custom_field_capacity": _("Field capacity"),
            "custom_thetaS": _("Soil moisture at saturation"),
            "custom_wilting_point": _("Permanent wilting point"),
            "soil_analysis": _("Soil analysis document"),
        }

    def clean(self):
        cleaned_data = super(AgrifieldForm, self).clean()
        is_virtual = cleaned_data.get("is_virtual")

        if is_virtual is None:
            msg = _("You must select if field is virtual or not")
            self.add_error("is_virtual", msg)


class AppliedIrrigationForm(forms.ModelForm):
    class Meta:
        model = AppliedIrrigation
        exclude = ("agrifield",)
        labels = {
            "timestamp": _("Date and time (YYYY-MM-DD HH:mm:ss) "),
            "irrigation_type": _("Type of irrigation used"),
            "supplied_water_volume": _("Volume of applied irrigation water"),
            "supplied_duration": _("The duration of irrigation in minutes"),
            "supplied_flow_rate": _("Water flow during irrigation (m³/h)"),
            "hydrometer_reading_start": _("Hydrometer reading at the start"),
            "hydrometer_reading_end": _("Hydrometer reading at the end"),
            "hydrometer_water_percentage": _("Percentage of water passing through"),
        }

    def clean(self):
        cleaned_data = super().clean()
        irrigation_type = cleaned_data.get("irrigation_type")
        if irrigation_type == "VOLUME_OF_WATER":
            self._validate_required(["supplied_water_volume"])
        elif irrigation_type == "DURATION_OF_IRRIGATION":
            self._validate_required(["supplied_duration", "supplied_flow_rate"])
        elif irrigation_type == "HYDROMETER_READINGS":
            fields = [
                "hydrometer_reading_start",
                "hydrometer_reading_end",
                "hydrometer_water_percentage",
            ]
            self._validate_required(fields)
        return super().clean()

    def _validate_required(self, fields=[]):
        # Used to require fields dynamically (depending on other submitted values)
        for field in fields:
            if self.cleaned_data.get(field, None) is None:
                self.add_error(field, _("This field is required."))


class MyRegistrationForm(RegistrationForm):

    """
    Extension of the default registration form to include a captcha
    """

    captcha = CaptchaField(label=_("Are you human?"))
