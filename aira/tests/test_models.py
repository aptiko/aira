import datetime as dt
import os
import shutil
import tempfile

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.test import TestCase, override_settings

from freezegun import freeze_time
from model_mommy import mommy
from swb import KcStage

from aira import models
from aira.tests import RandomMediaRootMixin


class DayAndMonthTestCase(TestCase):
    def test_incorrect_type_for_day_does_not_validate(self):
        with self.assertRaises(ValidationError):
            models.DayAndMonth(1.0, 1)

    def test_incorrect_type_for_month_does_not_validate(self):
        with self.assertRaises(ValidationError):
            models.DayAndMonth(1, 1.0)

    def test_month_less_than_1_does_not_validate(self):
        with self.assertRaises(ValidationError):
            models.DayAndMonth(1, 0)

    def test_month_greater_than_12_does_not_validate(self):
        with self.assertRaises(ValidationError):
            models.DayAndMonth(1, 13)

    def test_day_less_than_1_does_not_validate(self):
        with self.assertRaises(ValidationError):
            models.DayAndMonth(0, 1)

    def test_day_greater_than_month_days_does_not_validate(self):
        with self.assertRaises(ValidationError):
            models.DayAndMonth(29, 2)

    def test_correct_input_validates(self):
        day_and_month = models.DayAndMonth(29, 4)
        self.assertEqual(day_and_month.day, 29)
        self.assertEqual(day_and_month.month, 4)

    def test_from_string_without_slash_does_not_validate(self):
        with self.assertRaises(ValidationError):
            models.DayAndMonth.from_string("hello")

    def test_from_string_without_more_than_one_slash_does_not_validate(self):
        with self.assertRaises(ValidationError):
            models.DayAndMonth.from_string("hello/my/world")

    def test_from_string_with_non_integers_does_not_validate(self):
        with self.assertRaises(ValidationError):
            models.DayAndMonth.from_string("29.0/4.0")

    def test_from_string_valid_string_validates(self):
        day_and_month = models.DayAndMonth.from_string("29/4")
        self.assertEqual(day_and_month.day, 29)
        self.assertEqual(day_and_month.month, 4)

    def test_str(self):
        day_and_month = models.DayAndMonth(29, 4)
        self.assertEqual(str(day_and_month), "29/04")


class DayAndMonthFieldTestCase(TestCase):
    def test_get_prep_value_none(self):
        self.assertEqual(models.DayAndMonthField().get_prep_value(None), "")

    def test_get_prep_value_empty(self):
        self.assertEqual(models.DayAndMonthField().get_prep_value(""), "")

    def test_get_prep_value_not_empty(self):
        value = models.DayAndMonth(29, 4)
        self.assertEqual(models.DayAndMonthField().get_prep_value(value), "29/04")

    def test_from_db_value_empty_string(self):
        self.assertIsNone(models.DayAndMonthField().from_db_value("", None, None))

    def test_from_db_value_nonempty_string(self):
        day_and_month = models.DayAndMonthField().from_db_value("29/04", None, None)
        self.assertEqual(day_and_month.day, 29)
        self.assertEqual(day_and_month.month, 4)

    def test_to_python_from_DayAndMonth_object(self):
        day_and_month = models.DayAndMonth(29, 4)
        result = models.DayAndMonthField().to_python(day_and_month)
        self.assertEqual(result.day, 29)
        self.assertEqual(result.month, 4)

    def test_to_python_from_none(self):
        self.assertIsNone(models.DayAndMonthField().to_python(None))

    def test_to_python_from_string(self):
        result = models.DayAndMonthField().to_python("29/4")
        self.assertEqual(result.day, 29)
        self.assertEqual(result.month, 4)


class UserTestCase(TestCase):
    def setUp(self):
        self.assertEqual(models.Profile.objects.count(), 0)
        self.user = User.objects.create_user(
            id=55, username="bob", password="topsecret"
        )

    def test_create_user_profile_receiver(self):
        self.assertEqual(hasattr(self.user, "profile"), True)

    def test_created_user_same_profile_FK(self):
        profile = models.Profile.objects.get(user_id=self.user.id)
        self.assertEqual(profile.user, self.user)

    def test_save_user_profile_receiver(self):
        self.user.profile.first_name = "Bruce"
        self.user.profile.last_name = "Wayne"
        self.user.profile.address = "Gotham City"
        self.user.save()
        profile = models.Profile.objects.get(user_id=self.user.id)
        self.assertEqual(profile.first_name, "Bruce")
        self.assertEqual(profile.last_name, "Wayne")
        self.assertEqual(profile.address, "Gotham City")


class AgrifieldTestCaseBase(TestCase):
    def setUp(self):
        self.crop_type = mommy.make(
            models.CropType,
            name="Grass",
            root_depth_max=0.7,
            root_depth_min=1.2,
            max_allowed_depletion=0.5,
            fek_category=4,
            planting_date="15/03",
        )
        self.irrigation_type = mommy.make(
            models.IrrigationType, name="Surface irrigation", efficiency=0.60
        )
        self.user = User.objects.create_user(
            id=55, username="bob", password="topsecret"
        )
        self.agrifield = mommy.make(
            models.Agrifield,
            id=42,
            owner=self.user,
            name="A field",
            crop_type=self.crop_type,
            irrigation_type=self.irrigation_type,
            location=Point(18.0, 23.0),
            wetted_area=2000,
        )


class AgrifieldTestCase(AgrifieldTestCaseBase):
    def test_agrifield_creation(self):
        agrifield = models.Agrifield.objects.create(
            owner=self.user,
            name="A field",
            crop_type=self.crop_type,
            irrigation_type=self.irrigation_type,
            location=Point(18.0, 23.0),
            wetted_area=2000,
        )
        self.assertTrue(isinstance(agrifield, models.Agrifield))
        self.assertEqual(agrifield.__str__(), agrifield.name)

    def test_agrifield_update(self):
        self.agrifield.name = "This another field name"
        self.agrifield.save()
        self.assertEqual(self.agrifield.__str__(), "This another field name")

    def test_agrifield_delete(self):
        self.agrifield.delete()
        self.assertEqual(models.Agrifield.objects.all().count(), 0)

    def test_agrifield_irrigation_optimizer_default_value(self):
        self.assertEqual(self.agrifield.irrigation_optimizer, 0.5)

    def test_agrifield_use_custom_parameters_default_value(self):
        self.assertFalse(self.agrifield.use_custom_parameters)

    def test_wetted_area_must_be_larger_than_zero(self):
        with self.assertRaises(ValidationError):
            agrifield = models.Agrifield(
                owner=self.user,
                name="A field",
                crop_type=self.crop_type,
                irrigation_type=self.irrigation_type,
                location=Point(18.0, 23.0),
                wetted_area=0,
            )
            agrifield.full_clean()


class AgrifieldDeletesCachedPointTimeseriesOnSave(AgrifieldTestCaseBase):
    def setUp(self):
        super().setUp()
        self.tmpdir = tempfile.mkdtemp()
        self._create_test_files()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        super().tearDown()

    def _create_test_files(self):
        self.relevant_pathname = self._create_test_file("agrifield42-temperature.hts")
        self.irrelevant_pathname = self._create_test_file(
            "agrifield425-temperature.hts"
        )

    def _create_test_file(self, filename):
        path = os.path.join(self.tmpdir, filename)
        with open(path, "w") as f:
            f.write("hello world")
        return path

    def test_cached_point_timeseries_is_deleted_on_save(self):
        assert os.path.exists(self.relevant_pathname)
        with override_settings(AIRA_TIMESERIES_CACHE_DIR=self.tmpdir):
            self.agrifield.save()
        self.assertFalse(os.path.exists(self.relevant_pathname))

    def test_irrelevant_cached_point_timeseries_is_untouched(self):
        with override_settings(AIRA_TIMESERIES_CACHE_DIR=self.tmpdir):
            self.agrifield.save()
        self.assertTrue(os.path.exists(self.irrelevant_pathname))


class AgrifieldSoilAnalysisTestCase(TestCase, RandomMediaRootMixin):
    def setUp(self):
        self.override_media_root()
        self.agrifield = mommy.make(
            models.Agrifield, owner__username="bob", crop_type__planting_date="15/03"
        )
        self.agrifield.soil_analysis.save("somefile", ContentFile("hello world"))

    def tearDown(self):
        self.end_media_root_override()

    def test_file_data(self):
        with open(self.agrifield.soil_analysis.path, "r") as f:
            self.assertEqual(f.read(), "hello world")

    def test_file_url(self):
        self.assertEqual(
            self.agrifield.soil_analysis.url,
            "/bob/fields/{}/soil_analysis/".format(self.agrifield.id),
        )


class AgrifieldMostRecentPlantingDateTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.crop_type = mommy.make(
            models.CropType, planting_date=models.DayAndMonth(15, 3)
        )
        cls.agrifield = mommy.make(
            models.Agrifield,
            crop_type=cls.crop_type,
            custom_planting_date=models.DayAndMonth(5, 4),
            use_custom_parameters=False,
        )

    def setUp(self):
        self.agrifield.use_custom_parameters = False

    @freeze_time("2019-04-20 13:00:01")
    def test_result_when_it_has_appeared_this_year(self):
        self.assertEqual(self.agrifield.most_recent_planting_date, dt.date(2019, 3, 15))

    @freeze_time("2019-03-10 13:00:01")
    def test_result_when_it_has_not_appeared_this_year_yet(self):
        self.assertEqual(self.agrifield.most_recent_planting_date, dt.date(2018, 3, 15))

    @freeze_time("2019-04-20 13:00:01")
    def test_result_when_custom_parameters_and_has_appeared_this_year(self):
        self.agrifield.use_custom_parameters = True
        self.assertEqual(self.agrifield.most_recent_planting_date, dt.date(2019, 4, 5))

    @freeze_time("2019-03-10 13:00:01")
    def test_result_when_custom_parameters_and_has_not_appeared_this_year_yet(self):
        self.agrifield.use_custom_parameters = True
        self.assertEqual(self.agrifield.most_recent_planting_date, dt.date(2018, 4, 5))


class CropTypeKcStagesTestCase(TestCase):
    def setUp(self):
        self.crop_type = mommy.make(
            models.CropType,
            planting_date=models.DayAndMonth(21, 3),
            kc_offseason=0.3,
            kc_plantingdate=0.7,
        )
        for i, s in enumerate([(35, 0.7), (45, 1.05), (40, 1.05), (15, 0.95)], start=1):
            models.CropTypeKcStage.objects.create(
                crop_type=self.crop_type, order=i, ndays=s[0], kc_end=s[1]
            )

    def test_kc_stages(self):
        self.assertEqual(
            self.crop_type.kc_stages,
            [
                KcStage(35, 0.7),
                KcStage(45, 1.05),
                KcStage(40, 1.05),
                KcStage(15, 0.95),
            ],
        )

    def test_kc_stages_str(self):
        self.assertEqual(
            self.crop_type.kc_stages_str, "35\t0.7\n45\t1.05\n40\t1.05\n15\t0.95"
        )


class CropTypeCustomTestCase(TestCase):
    def _create_crop_type(self, name, custom):
        return models.CropType.objects.create(
            name=name,
            root_depth_max=5,
            root_depth_min=3,
            max_allowed_depletion=0.5,
            kc_plantingdate=0.7,
            kc_offseason=0.3,
            planting_date=models.DayAndMonth(21, 3),
            fek_category=5,
            custom=custom,
        )

    def test_cannot_create_second_custom_crop_type(self):
        self._create_crop_type(name="Pine trees", custom=True)
        with self.assertRaises(IntegrityError):
            self._create_crop_type(name="Cypresses", custom=True)

    def test_can_create_noncustom_crop_type_if_custom_exists(self):
        self._create_crop_type(name="Pine trees", custom=True)
        self._create_crop_type(name="Cypresses", custom=False)

    def test_cannot_change_noncustom_crop_type_to_custom_if_custom_exists(self):
        self._create_crop_type(name="Pine trees", custom=True)
        cypresses = self._create_crop_type(name="Cypresses", custom=False)
        with self.assertRaises(IntegrityError):
            cypresses.custom = True
            cypresses.save()

    def test_can_resave_existing_custom_crop_type(self):
        pines = self._create_crop_type(name="Pine trees", custom=True)
        pines.save()


class AgrifieldLatestAppliedIrrigationDefaultsTestCase(TestCase):
    def setUp(self):
        self.agrifield = mommy.make(models.Agrifield, crop_type__planting_date="15/03")

    def test_no_applied_irrigations_present(self):
        defaults = self.agrifield.get_applied_irrigation_defaults()
        self.assertEqual(defaults, {"irrigation_type": "VOLUME_OF_WATER"})

    def test_default_irrigation_type_and_all_values_present(self):
        latest = dt.datetime(2020, 3, 1, 0, 0, tzinfo=dt.timezone.utc)

        # To assert which instance is the value coming from, a simple 2 digits scheme
        # is followed, first digit is the field id, the second is a bit (T/F)
        mommy.make(
            models.AppliedIrrigation,
            agrifield=self.agrifield,
            irrigation_type="VOLUME_OF_WATER",
            timestamp=latest - dt.timedelta(days=1),
            supplied_water_volume=11,
            supplied_duration=20,
            supplied_flow_rate=30,
            flowmeter_reading_end=40,
            flowmeter_water_percentage=50,
            flowmeter_reading_start=60,
        )
        mommy.make(
            models.AppliedIrrigation,
            agrifield=self.agrifield,
            irrigation_type="FLOWMETER_READINGS",
            timestamp=latest,
            supplied_water_volume=10,
            supplied_duration=20,
            supplied_flow_rate=30,
            flowmeter_reading_end=41,
            flowmeter_water_percentage=51,
            flowmeter_reading_start=61,  # Won't be used anyway (end=start)
        )
        mommy.make(
            models.AppliedIrrigation,
            agrifield=self.agrifield,
            irrigation_type="DURATION_OF_IRRIGATION",
            timestamp=latest - dt.timedelta(days=5),
            supplied_water_volume=10,
            supplied_duration=21,
            supplied_flow_rate=31,
            flowmeter_reading_end=40,
            flowmeter_water_percentage=50,
            flowmeter_reading_start=60,
        )
        defaults = self.agrifield.get_applied_irrigation_defaults()
        expected_defaults = {
            "irrigation_type": "FLOWMETER_READINGS",
            "supplied_water_volume": 11.0,
            "supplied_duration": 21,
            "supplied_flow_rate": 31.0,
            "flowmeter_reading_start": 41.0,
            "flowmeter_water_percentage": 51,
        }
        self.assertEqual(defaults, expected_defaults)

    def test_only_water_volume_default_present(self):
        mommy.make(
            models.AppliedIrrigation,
            agrifield=self.agrifield,
            irrigation_type="VOLUME_OF_WATER",
            timestamp=dt.datetime(2020, 3, 1, 0, 0, tzinfo=dt.timezone.utc),
            supplied_water_volume=1337,
        )
        defaults = self.agrifield.get_applied_irrigation_defaults()
        expected_defaults = {
            "irrigation_type": "VOLUME_OF_WATER",
            "supplied_water_volume": 1337,
        }
        self.assertEqual(defaults, expected_defaults)


class AgrifieldCustomKcStagesTestCase(TestCase):
    def setUp(self):
        self.agrifield = mommy.make(models.Agrifield, crop_type__planting_date="15/03")
        csv = "15 0.9\n25 0.8"
        self.agrifield.set_custom_kc_stages(csv)

    def test_set_custom_kc_stages(self):
        kc_stages = models.AgrifieldCustomKcStage.objects.order_by("order")
        self.assertEqual(kc_stages[0].order, 1)
        self.assertEqual(kc_stages[0].ndays, 15)
        self.assertAlmostEqual(kc_stages[0].kc_end, 0.9)
        self.assertEqual(kc_stages[1].order, 2)
        self.assertEqual(kc_stages[1].ndays, 25)
        self.assertAlmostEqual(kc_stages[1].kc_end, 0.8)

    def test_kc_stages_str(self):
        self.assertEqual(self.agrifield.kc_stages_str, "15\t0.9\n25\t0.8")


class AppliedIrrigationTestCase(TestCase):
    def setUp(self):
        # Populate the rest to assure that the correct value is the one
        # being used for calculation according to 'irrigation_type'
        self.defaults = {
            "supplied_water_volume": 100,
            "supplied_duration": 100,
            "supplied_flow_rate": 100,
            "flowmeter_reading_start": 100,
            "flowmeter_reading_end": 100,
            "flowmeter_water_percentage": 100,
            "agrifield__crop_type__planting_date": "15/03",
        }

    def test_calculated_volume_supplied_water_volume(self):
        kwargs = {
            **self.defaults,
            "supplied_water_volume": 1337,
        }
        irrigation = mommy.make(
            models.AppliedIrrigation, irrigation_type="VOLUME_OF_WATER", **kwargs
        )
        self.assertEqual(irrigation.volume, 1337)

    def test_calculated_volume_supplied_duration(self):
        kwargs = {
            **self.defaults,
            "supplied_duration": 1337 * 60 * 2,
            "supplied_flow_rate": 0.5,
        }
        irrigation = mommy.make(
            models.AppliedIrrigation, irrigation_type="DURATION_OF_IRRIGATION", **kwargs
        )
        self.assertEqual(irrigation.volume, 1337)

    def test_calculated_volume_supplied_flowmeter_readings(self):
        kwargs = {
            **self.defaults,
            "flowmeter_reading_start": 1000,
            "flowmeter_reading_end": 1000 + 1337,
            "flowmeter_water_percentage": 50,
        }
        irrigation = mommy.make(
            models.AppliedIrrigation, irrigation_type="FLOWMETER_READINGS", **kwargs
        )
        self.assertEqual(irrigation.volume, 1337 * 2)  # Double; since percentage is 50%

    def test_calculated_volume_with_no_values_recorded(self):
        types = ["VOLUME_OF_WATER", "DURATION_OF_IRRIGATION", "FLOWMETER_READINGS"]
        for ir_type in types:
            irrigation = mommy.make(
                models.AppliedIrrigation,
                irrigation_type="DURATION_OF_IRRIGATION",
                agrifield__crop_type__planting_date="15/03",
            )
            self.assertIsNone(irrigation.volume)


class AppliedIrrigationUniqueTogetherConstraintTestCase(TestCase):
    def test_duplicate_point_raises(self):
        time = dt.datetime(2020, 10, 10, 0, 0, tzinfo=dt.timezone.utc)
        agrifield = mommy.make(models.Agrifield, crop_type__planting_date="15/03")
        self.assertEqual(models.AppliedIrrigation.objects.count(), 0)
        mommy.make(
            models.AppliedIrrigation,
            agrifield=agrifield,
            is_automatically_reported=True,
            irrigation_type="VOLUME_OF_WATER",
            supplied_water_volume=1337,
            timestamp=time,
        )
        with self.assertRaises(IntegrityError):
            mommy.make(
                models.AppliedIrrigation,
                agrifield=agrifield,
                is_automatically_reported=True,
                irrigation_type="VOLUME_OF_WATER",
                supplied_water_volume=1337,
                timestamp=time,
            )

    def test_different_agrifield_same_volume_and_time(self):
        time = dt.datetime(2020, 10, 10, 0, 0, tzinfo=dt.timezone.utc)
        self.assertEqual(models.AppliedIrrigation.objects.count(), 0)
        mommy.make(
            models.AppliedIrrigation,
            is_automatically_reported=True,
            irrigation_type="VOLUME_OF_WATER",
            supplied_water_volume=1337,
            timestamp=time,
            agrifield__crop_type__planting_date="15/03",
        )
        mommy.make(
            models.AppliedIrrigation,
            is_automatically_reported=True,
            irrigation_type="VOLUME_OF_WATER",
            supplied_water_volume=1337,
            timestamp=time,
            agrifield__crop_type__planting_date="15/03",
        )
        self.assertEqual(models.AppliedIrrigation.objects.count(), 2)

    def test_same_agrifield_diff_volume_same_time(self):
        time = dt.datetime(2020, 10, 10, 0, 0, tzinfo=dt.timezone.utc)
        agrifield = mommy.make(models.Agrifield, crop_type__planting_date="15/03")
        self.assertEqual(models.AppliedIrrigation.objects.count(), 0)
        mommy.make(
            models.AppliedIrrigation,
            agrifield=agrifield,
            is_automatically_reported=True,
            irrigation_type="VOLUME_OF_WATER",
            supplied_water_volume=1337,
            timestamp=time,
        )
        mommy.make(
            models.AppliedIrrigation,
            agrifield=agrifield,
            is_automatically_reported=True,
            irrigation_type="VOLUME_OF_WATER",
            supplied_water_volume=1337 + 1,
            timestamp=time,
        )
        self.assertEqual(models.AppliedIrrigation.objects.count(), 2)

    def test_same_agrifield_same_volume_diff_time(self):
        agrifield = mommy.make(models.Agrifield, crop_type__planting_date="15/03")
        self.assertEqual(models.AppliedIrrigation.objects.count(), 0)
        mommy.make(
            models.AppliedIrrigation,
            agrifield=agrifield,
            is_automatically_reported=True,
            irrigation_type="VOLUME_OF_WATER",
            supplied_water_volume=1337,
        )
        mommy.make(
            models.AppliedIrrigation,
            agrifield=agrifield,
            is_automatically_reported=True,
            irrigation_type="VOLUME_OF_WATER",
            supplied_water_volume=1337,
        )
        self.assertEqual(models.AppliedIrrigation.objects.count(), 2)


class TelemetricFlowmeterDeleteAllTestCase(TestCase):
    def setUp(self):
        self.flowmeter1 = mommy.make(
            models.LoRA_ARTAFlowmeter,
            agrifield__id=1,
            agrifield__crop_type__planting_date="15/03",
        )
        self.flowmeter2 = mommy.make(
            models.LoRA_ARTAFlowmeter,
            agrifield__id=2,
            agrifield__crop_type__planting_date="15/03",
        )
        models.TelemetricFlowmeter.delete_all(agrifield=self.flowmeter1.agrifield)

    def test_flowmeter_of_agrifield1_have_been_deleted(self):
        self.assertFalse(
            models.LoRA_ARTAFlowmeter.objects.filter(agrifield__id=1).exists()
        )

    def test_flowmeter_of_agrifield2_have_not_been_deleted(self):
        self.assertTrue(
            models.LoRA_ARTAFlowmeter.objects.filter(agrifield__id=2).exists()
        )


class LoRA_ARTAFlowmeterTestCase(TestCase):
    def setUp(self):
        self.flowmeter = mommy.make(
            models.LoRA_ARTAFlowmeter,
            device_id="1337",
            flowmeter_water_percentage=50,
            report_frequency_in_minutes=15,
            agrifield__crop_type__planting_date="15/03",
        )

    def test_calculate_water_volume(self):
        """
        Supplied sensor frequency as 10, thus 50% of the total value:
        15(report freq) x 10(sensor freq) / 6.8(def. conversion)
            = 22.058
        """
        water_volume = self.flowmeter._calculate_water_volume(10.0)
        self.assertAlmostEqual(float(water_volume), 22.058 / 2, delta=0.01)

    def test_points_created_as_automated_reporting(self):
        data_points = [
            {"sensor_frequency": 10, "timestamp": "2020-10-12T00:00:00.000000000Z"}
        ]
        self.assertEqual(self.flowmeter.agrifield.appliedirrigation_set.count(), 0)
        self.flowmeter.create_irrigations_in_bulk(data_points)
        self.assertEqual(self.flowmeter.agrifield.appliedirrigation_set.count(), 1)

        irrigation = self.flowmeter.agrifield.appliedirrigation_set.latest()
        expected_volume = float(self.flowmeter._calculate_water_volume(10))

        self.assertTrue(irrigation.is_automatically_reported)
        self.assertEqual(irrigation.irrigation_type, "VOLUME_OF_WATER")
        self.assertAlmostEqual(
            irrigation.supplied_water_volume, expected_volume, delta=0.01
        )
        self.assertEqual(
            irrigation.timestamp,
            dt.datetime(2020, 10, 12, 0, 0, tzinfo=dt.timezone.utc),
        )

    def test_duplicate_points_are_skipped(self):
        # Ensure that if time is the same, but the volume is different, it will pass.
        data_points = [
            {"sensor_frequency": 10, "timestamp": "2020-10-10T00:00:00.000000000Z"},
            {"sensor_frequency": 12, "timestamp": "2020-10-10T00:15:00.000000000Z"},
            {"sensor_frequency": 15, "timestamp": "2020-10-10T00:30:00.000000000Z"},
            {"sensor_frequency": 15, "timestamp": "2020-10-10T00:30:00.000000000Z"},
            {"sensor_frequency": 16, "timestamp": "2020-10-10T00:30:00.000000000Z"},
        ]

        self.assertEqual(self.flowmeter.agrifield.appliedirrigation_set.count(), 0)
        self.flowmeter.create_irrigations_in_bulk(data_points)
        self.assertEqual(self.flowmeter.agrifield.appliedirrigation_set.count(), 4)
        # Ensure that the removed duplicate was the duplicated volume indeed
        volumes = self.flowmeter.agrifield.appliedirrigation_set.values_list(
            "supplied_water_volume"
        )
        self.assertEqual(len(set(volumes)), 4)
