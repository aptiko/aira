from django.test import TestCase

from aira.forms import AppliedIrrigationForm


class TestRegistrationForm(TestCase):
    def test_registration_form_submission(self):
        post_data = {"usename": "bob", "password": "topsecret"}
        r = self.client.post("/accounts/register/", post_data)
        self.assertEqual(r.status_code, 200)

    def test_registation_form_fails_blank_submission(self):
        r = self.client.post("/accounts/register/", {})
        self.assertFormError(r, "form", "password1", "This field is required.")


class TestAppliedIrrigationForm(TestCase):
    def setUp(self):
        self.data = {
            "timestamp": "2020-02-02",
        }

    def test_required_fields_with_type_volume_of_water(self):
        form_data = {**self.data, "irrigation_type": "VOLUME_OF_WATER"}
        form = AppliedIrrigationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEquals(
            form.errors, {"supplied_water_volume": ["This field is required."]}
        )

    def test_required_fields_with_type_duration_of_irrigation(self):
        form_data = {**self.data, "irrigation_type": "DURATION_OF_IRRIGATION"}
        form = AppliedIrrigationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEquals(
            form.errors,
            {
                "supplied_duration": ["This field is required."],
                "supplied_flow_rate": ["This field is required."],
            },
        )

    def test_required_fields_with_type_hydrometer_readings(self):
        form_data = {**self.data, "irrigation_type": "HYDROMETER_READINGS"}
        form = AppliedIrrigationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEquals(
            form.errors,
            {
                "hydrometer_water_percentage": ["This field is required."],
                "hydrometer_reading_start": ["This field is required."],
                "hydrometer_reading_end": ["This field is required."],
            },
        )
