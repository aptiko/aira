from django.test import TestCase


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
        # Create a single agrifiled
        pass

    def test_required_fields_with_type_volume_of_water(self):
        pass

    def test_required_fields_with_type_duration_of_irrigation(self):
        pass

    def test_required_fields_with_type_hydrometer_readings(self):
        pass
