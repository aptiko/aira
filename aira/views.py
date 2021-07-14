import csv
import datetime as dt
import os
from glob import glob

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import RedirectView, TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from . import forms, models


class CheckUsernameMixin:
    """Check that the username in the URL is correct.

    Many views have a URL of the form "/{username}/fields/{agrifield_id}/{remainder}".
    In these cases, the agrifield is fully specified with the {agrifield_id}; the
    {username} is not required. So we want to make sure you can't arrive at the field
    through a wrong username.
    """

    def get_object(self, *args, **kwargs):
        agrifield = self.get_agrifield()
        if getattr(self, "model", None) in (None, models.Agrifield):
            return agrifield
        result = super().get_object()
        if result.agrifield != agrifield:
            raise Http404
        return result

    def get_agrifield(self):
        agrifield_id = self.kwargs.get("agrifield_id") or self.kwargs.get("pk")
        return get_object_or_404(
            models.Agrifield, pk=agrifield_id, owner__username=self.kwargs["username"]
        )


class IrrigationPerformanceView(CheckUsernameMixin, DetailView):
    model = models.Agrifield
    template_name = "aira/performance_chart/main.html"

    def get_context_data(self, **kwargs):
        self.context = super().get_context_data(**kwargs)
        if not self.object.results:
            return self.context
        self._get_sum_applied_irrigation()
        self._get_percentage_diff()
        return self.context

    def _get_sum_applied_irrigation(self):
        results = self.object.results
        sum_applied_irrigation = results["timeseries"].assumed_total_irrigation.sum()
        self.context["sum_applied_irrigation"] = sum_applied_irrigation
        self.context["sum_applied_irrigation_cubic"] = (
            sum_applied_irrigation * self.object.wetted_area / 1000
        )

    def _get_percentage_diff(self):
        results = self.object.results
        sum_ifinal_theoretical = results["timeseries"].ifinal_theoretical.sum()
        sum_applied_irrigation = self.context["sum_applied_irrigation"]
        if sum_ifinal_theoretical >= 0.1:
            self.context["percentage_diff"] = round(
                (sum_applied_irrigation - sum_ifinal_theoretical)
                / sum_ifinal_theoretical
                * 100
            )
        else:
            self.context["percentage_diff"] = _("N/A")


class IrrigationPerformanceCsvView(CheckUsernameMixin, View):
    def get(self, *args, **kwargs):
        f = self.get_agrifield()
        response = HttpResponse(content_type="text/csv")
        response[
            "Content-Disposition"
        ] = 'attachment; filename="{}-performance.csv"'.format(f.id)
        writer = csv.writer(response)
        writer.writerow(
            [
                "Date",
                "Estimated Irrigation Water Amount",
                "Applied Irrigation Water Amount",
                "Effective precipitation",
            ]
        )
        writer.writerow(["", "amount (mm)", "amount (mm)", "amount (mm)"])
        for date, row in f.results["timeseries"].iterrows():
            if date > f.results["historical_end_date"]:
                break
            writer.writerow(
                [
                    date,
                    row.ifinal_theoretical,
                    row.applied_irrigation if row.applied_irrigation else 0,
                    row.effective_precipitation,
                ]
            )
        return response


class DemoView(TemplateView):
    INITIAL_AGRIFIELDS = [
        {
            "name": "Field outside covered area",
            "coordinates": (19.0, 38.0),
            "applied_irrigation": [],
        },
        {
            "name": "Field with irrigation log",
            "coordinates": (20.98, 39.15),
            "wetted_area": 10000.0,
            "applied_irrigation": [
                {"timestamp": "2015-02-15 00:00Z", "supplied_water_volume": 23.0}
            ],
        },
        {
            "name": "Field with no irrigation log",
            "coordinates": (20.92, 39.10),
            "applied_irrigation": [],
        },
        {
            "name": "Filed with log outside dataset",
            "coordinates": (20.94, 39.12),
            "applied_irrigation": [
                {"timestamp": "2014-02-15 00:00Z", "supplied_water_volume": 23.0}
            ],
        },
    ]

    def get(self, request):
        self._ensure_we_have_demo_user()
        self._ensure_we_have_agrifields()
        user = authenticate(username="demo", password="demo")
        login(request, user)
        return redirect("agrifield-list", user)

    def _ensure_we_have_demo_user(self):
        try:
            self.demo_user = get_object_or_404(User, username="demo")
        except Http404:
            self._create_demo_user()

    def _create_demo_user(self):
        self._create_user()
        self._create_profile()

    def _create_user(self):
        self.demo_user = User.objects.create_user(
            username="demo", email="demo@aira.com", password="demo", is_active=True
        )

    def _create_profile(self):
        self.demo_user.profile.first_name = "Aira Demo"
        self.demo_user.profile.last_name = "Aira Demo"
        self.demo_user.profile.address = "Aira"
        self.demo_user.save()

    def _ensure_we_have_agrifields(self):
        if not self.demo_user.agrifield_set.exists():
            self._create_agrifields()

    def _create_agrifields(self):
        crop_type = self._get_crop_type()
        irrigation_type = models.IrrigationType.objects.first()
        for item in self.INITIAL_AGRIFIELDS:
            self._create_agrifield(item, crop_type, irrigation_type)

    def _get_crop_type(self):
        crop_type = models.CropType.objects.filter(
            Q(name__contains="Χλοοτάπητας ψυχρόφιλος")
            | Q(name__contains="Turf grass - cool")
        ).first()
        if crop_type is None:
            crop_type = models.CropType.objects.first()
        return crop_type

    def _create_agrifield(self, item, crop_type, irrigation_type):
        f, created = models.Agrifield.objects.get_or_create(
            owner=self.demo_user,
            name=item["name"],
            location=Point(*item["coordinates"]),
            wetted_area=10000,
            crop_type=crop_type,
            irrigation_type=irrigation_type,
            use_custom_parameters=False,
        )
        f.save()
        for applied_irrigation in item["applied_irrigation"]:
            l, created = models.AppliedIrrigation.objects.get_or_create(
                agrifield=f,
                timestamp=applied_irrigation["timestamp"],
                supplied_water_volume=applied_irrigation["supplied_water_volume"],
            )
            l.save()


class ConversionToolsView(LoginRequiredMixin, TemplateView):
    template_name = "aira/tools/main.html"


class FrontPageView(TemplateView):
    template_name = "aira/frontpage/main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filenames = sorted(
            glob(os.path.join(settings.AIRA_DATA_HISTORICAL, "daily_rain-*.tif"))
        )
        try:
            context["start_date"] = self._get_date_from_filename(filenames[0])
            context["end_date"] = self._get_date_from_filename(filenames[-1])
        except IndexError:
            context["start_date"] = dt.date(2019, 1, 1)
            context["end_date"] = dt.date(2019, 1, 3)
        return context

    def _get_date_from_filename(self, filename):
        datestr = os.path.basename(filename).split(".")[0].partition("-")[2]
        y, m, d = (int(x) for x in datestr.split("-"))
        return dt.date(y, m, d)


class AgrifieldListView(LoginRequiredMixin, TemplateView):
    template_name = "aira/agrifield_list/main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Load data paths
        url_username = kwargs.get("username")
        context["url_username"] = kwargs.get("username")
        if kwargs.get("username") is None:
            url_username = self.request.user
            context["url_username"] = self.request.user
        # User is url_slug <username>
        user = User.objects.get(username=url_username)

        # Fetch models.Profile(User)
        try:
            context["profile"] = models.Profile.objects.get(user=self.request.user)
        except models.Profile.DoesNotExist:
            context["profile"] = None
        # Fetch models.Agrifield(User)
        try:
            agrifields = models.Agrifield.objects.filter(owner=user).all()
            context["agrifields"] = agrifields
            context["fields_count"] = len(agrifields)
        except models.Agrifield.DoesNotExist:
            context["agrifields"] = None
        return context


class MyFieldsView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return reverse(
                "agrifield-list", kwargs={"username": self.request.user.username}
            )
        else:
            raise Http404


class AgrifieldReportView(CheckUsernameMixin, LoginRequiredMixin, DetailView):
    model = models.Agrifield
    template_name = "aira/agrifield_report/main.html"


class CreateAgrifieldView(LoginRequiredMixin, CreateView):
    model = models.Agrifield
    form_class = forms.AgrifieldForm
    template_name = "aira/agrifield_edit/main.html"

    def form_valid(self, form):
        user = User.objects.get(username=self.kwargs["username"])
        form.instance.owner = user
        return super().form_valid(form)

    def get_success_url(self):
        try:
            custom_crop_type_id = models.CropType.objects.get(custom=True).id
            if self.object.crop_type.id == custom_crop_type_id:
                return reverse(
                    "agrifield-update",
                    kwargs={"username": self.kwargs["username"], "pk": self.object.id},
                )
        except models.CropType.DoesNotExist:
            pass
        return reverse("agrifield-list", kwargs={"username": self.kwargs["username"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            url_username = self.kwargs["username"]
            user = User.objects.get(username=url_username)
            context["agrifields"] = models.Agrifield.objects.filter(owner=user).all()
            context["agrifield_owner"] = user
        except models.Agrifield.DoesNotExist:
            context["agrifields"] = None
        try:
            context["custom_crop_type_id"] = models.CropType.objects.get(custom=True).id
        except models.CropType.DoesNotExist:
            context["custom_crop_type_id"] = 0
        return context


class UpdateAgrifieldView(CheckUsernameMixin, LoginRequiredMixin, UpdateView):
    model = models.Agrifield
    form_class = forms.AgrifieldForm
    template_name = "aira/agrifield_edit/main.html"

    def get_success_url(self):
        field = models.Agrifield.objects.get(pk=self.kwargs["pk"])
        return reverse("agrifield-list", kwargs={"username": field.owner})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["agrifield_owner"] = self.object.owner
        try:
            context["custom_crop_type_id"] = models.CropType.objects.get(custom=True).id
        except models.CropType.DoesNotExist:
            context["custom_crop_type_id"] = 0
        return context


class DeleteAgrifieldView(CheckUsernameMixin, LoginRequiredMixin, DeleteView):
    model = models.Agrifield
    form_class = forms.AgrifieldForm
    template_name = "aira/agrifield_delete/confirm.html"

    def get_success_url(self):
        field = models.Agrifield.objects.get(pk=self.kwargs["pk"])
        return reverse("agrifield-list", kwargs={"username": field.owner})


class TelemetricFlowmeterViewMixin:
    def set_telemetric_flowmeter_context(self, context):
        context["telemetric_flowmeter_types"] = []
        for flowmeter_type in models.TelemetricFlowmeter.TYPES:
            form = self._get_telemetry_form(flowmeter_type)
            context["telemetric_flowmeter_types"].append(
                {"name": flowmeter_type, "form": form, "selected": False}
            )
        self._set_selected_flowmeter_type(context)

    def _get_telemetry_form(self, flowmeter_type):
        form_class = getattr(forms, f"{flowmeter_type}FlowmeterForm")
        model = getattr(models, f"{flowmeter_type}Flowmeter")
        instance = model.objects.filter(agrifield=self.agrifield).first()
        if self._is_flowmeter_submitted_on_post(flowmeter_type):
            self.selected_flowmeter_type = flowmeter_type
            return form_class(
                self.request.POST, instance=instance, prefix=flowmeter_type
            )
        else:
            result = form_class(
                initial={"agrifield": self.agrifield},
                instance=instance,
                prefix=flowmeter_type,
            )
            if not hasattr(self, "selected_flowmeter_type") and result.instance.id:
                self.selected_flowmeter_type = flowmeter_type
            return result

    def _is_flowmeter_submitted_on_post(self, flowmeter_type):
        return (
            self.request.method == "POST"
            and self.request.POST.get("flowmeter_type") == flowmeter_type
        )

    def _set_selected_flowmeter_type(self, context):
        for flowmeter_type in context["telemetric_flowmeter_types"]:
            if flowmeter_type["name"] == getattr(self, "selected_flowmeter_type", None):
                flowmeter_type["selected"] = True
                return

    def _post_process_telemetry(self):
        flowmeter_type = self.request.POST.get("flowmeter_type")
        if not flowmeter_type:
            models.TelemetricFlowmeter.delete_all(self.agrifield)
            return HttpResponseRedirect(self.get_success_url())
        telemetry_form = self._get_telemetry_form(flowmeter_type)
        if telemetry_form.is_valid():
            if not telemetry_form.instance.id:
                models.TelemetricFlowmeter.delete_all(self.agrifield)
            telemetry_form.save()
            return HttpResponseRedirect(self.get_success_url())
        return self.get(self.request)


class AppliedIrrigationsView(
    CheckUsernameMixin, LoginRequiredMixin, TemplateView, TelemetricFlowmeterViewMixin
):
    template_name = "aira/appliedirrigation/main.html"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.agrifield = self.get_object(*args, **kwargs)

    def post(self, *args, **kwargs):
        if "irrigation_type" in self.request.POST:
            return self._post_add_irrigation()
        else:
            return self._post_process_telemetry()

    def _post_add_irrigation(self):
        self.applied_irrigation_form = forms.AppliedIrrigationForm(self.request.POST)
        if self.applied_irrigation_form.is_valid():
            self.applied_irrigation_form.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.get(self.request)

    def get_success_url(self):
        return reverse(
            "applied-irrigations",
            kwargs={
                "username": self.agrifield.owner,
                "agrifield_id": self.agrifield.id,
            },
        )

    def _get_applied_irrigation_form(self):
        try:
            return self.applied_irrigation_form
        except AttributeError:
            return forms.AppliedIrrigationForm(
                initial={
                    "agrifield": self.agrifield,
                    **self.agrifield.get_applied_irrigation_defaults(),
                },
            )

    def form_valid(self, form):
        form.instance.agrifield = models.Agrifield.objects.get(
            pk=self.kwargs["agrifield_id"]
        )
        form.instance.is_automatically_reported = False
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        self.agrifield = self.get_agrifield()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["agrifield"] = self.agrifield
        context["add_irrigation_form"] = self._get_applied_irrigation_form()
        self.set_telemetric_flowmeter_context(context)
        return context


class AppliedIrrigationViewMixin:
    model = models.AppliedIrrigation
    form_class = forms.AppliedIrrigationForm

    def form_valid(self, form):
        form.instance.is_automatically_reported = False
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "applied-irrigations",
            kwargs={
                "username": self.object.agrifield.owner,
                "agrifield_id": self.object.agrifield.id,
            },
        )


class UpdateAppliedIrrigationView(
    CheckUsernameMixin, LoginRequiredMixin, AppliedIrrigationViewMixin, UpdateView
):
    template_name_suffix = "/update"


class DeleteAppliedIrrigationView(
    CheckUsernameMixin, LoginRequiredMixin, AppliedIrrigationViewMixin, DeleteView
):
    template_name_suffix = "/confirm_delete"


def remove_supervisee_from_user_list(request, username):
    if request.method != "POST" or username != request.user.username:
        raise Http404
    try:
        supervisee_profile = models.Profile.objects.get(
            user_id=int(request.POST.get("supervisee_id")),
            supervisor=request.user,
        )
    except (TypeError, ValueError, models.Profile.DoesNotExist):
        raise Http404
    supervisee_profile.supervisor = None
    supervisee_profile.save()
    return HttpResponseRedirect(
        reverse("supervisees", kwargs={"username": request.user.username})
    )


class SuperviseesView(LoginRequiredMixin, ListView):
    model = models.Profile
    template_name = "aira/supervisees/main.html"

    def get_queryset(self):
        qs = super().get_queryset().filter(supervisor=self.request.user)
        qs = qs.order_by("first_name", "last_name")
        return qs


class AgrifieldTimeseriesView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        agrifield = get_object_or_404(models.Agrifield, pk=kwargs.get("agrifield_id"))
        if agrifield.owner.username != self.kwargs["username"]:
            raise Http404
        variable = kwargs.get("variable")
        filename = agrifield.get_point_timeseries(variable)
        return FileResponse(
            open(filename, "rb"), as_attachment=True, content_type="text_csv"
        )


class DownloadSoilAnalysisView(CheckUsernameMixin, LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        agrifield = self.get_agrifield()
        if not agrifield.soil_analysis:
            raise Http404
        return FileResponse(agrifield.soil_analysis, as_attachment=True)
