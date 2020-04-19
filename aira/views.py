import csv
import datetime as dt
import os
from glob import glob

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import FileResponse, Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

import pandas as pd

from .forms import AgrifieldForm, AppliedIrrigationForm, ProfileForm
from .models import Agrifield, AppliedIrrigation, Profile


class IrrigationPerformanceView(DetailView):
    model = Agrifield
    template_name = "aira/performance_chart/main.html"

    def get_context_data(self, **kwargs):
        self.object.can_edit(self.request.user)
        self.context = super().get_context_data(**kwargs)
        if not self.object.results:
            return self.context
        self._get_sum_applied_irrigation()
        self._get_percentage_diff()
        return self.context

    def _get_sum_applied_irrigation(self):
        results = self.object.results
        sum_applied_irrigation = results["timeseries"].applied_irrigation
        sum_applied_irrigation = pd.to_numeric(sum_applied_irrigation)
        sum_applied_irrigation[sum_applied_irrigation.isna()] = 0
        sum_applied_irrigation = sum_applied_irrigation.sum()
        self.context["sum_applied_irrigation"] = sum_applied_irrigation

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


def performance_csv(request, pk):
    f = Agrifield.objects.get(pk=pk)
    response = HttpResponse(content_type="text/csv")
    response[
        "Content-Disposition"
    ] = 'attachment; filename="{}-performance.csv"'.format(f.id)
    f.can_edit(request.user)
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
    def get(self, request):
        user = authenticate(username="demo", password="demo")
        login(request, user)
        return redirect("home", user)


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
    template_name = "aira/home/main.html"

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
            context["profile"] = Profile.objects.get(user=self.request.user)
        except Profile.DoesNotExist:
            context["profile"] = None
        # Fetch models.Agrifield(User)
        try:
            agrifields = Agrifield.objects.filter(owner=user).all()
            for f in agrifields:
                # Check if user is allowed or 404
                f.can_edit(self.request.user)
            # For Profile section
            # Select self.request.user user that set him supervisor
            if Profile.objects.filter(supervisor=self.request.user).exists():
                supervising_users = User.objects.filter(
                    profile__supervisor=self.request.user
                )
                context["supervising_users"] = supervising_users

            context["agrifields"] = agrifields
            context["fields_count"] = len(agrifields)
        except Agrifield.DoesNotExist:
            context["agrifields"] = None
        return context


class RecommendationView(LoginRequiredMixin, DetailView):
    model = Agrifield
    template_name = "aira/recommendation/main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.object.can_edit(self.request.user)
        return context


class UpdateProfileView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    success_url = "/home"
    template_name_suffix = "/form"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user in form.fields["supervisor"].queryset:
            form.fields["supervisor"].queryset = form.fields[
                "supervisor"
            ].queryset.exclude(pk=self.request.user.id)
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = Profile.objects.get(pk=self.kwargs["pk"])
        if not self.request.user == profile.user:
            raise Http404
        return context


class DeleteUserView(LoginRequiredMixin, DeleteView):
    model = User
    template_name_suffix = "/confirm_delete"

    def get_success_url(self):
        return reverse("welcome")


class CreateAgrifieldView(LoginRequiredMixin, CreateView):
    model = Agrifield
    form_class = AgrifieldForm
    template_name = "aira/agrifield_edit/main.html"

    def form_valid(self, form):
        user = User.objects.get(username=self.kwargs["username"])
        form.instance.owner = user
        return super().form_valid(form)

    def get_success_url(self):
        url_username = self.kwargs["username"]
        return reverse("home", kwargs={"username": url_username})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            url_username = self.kwargs["username"]
            user = User.objects.get(username=url_username)
            context["agrifields"] = Agrifield.objects.filter(owner=user).all()
            context["agrifield_owner"] = user

        except Agrifield.DoesNotExist:
            context["agrifields"] = None
        return context


class UpdateAgrifieldView(LoginRequiredMixin, UpdateView):
    model = Agrifield
    form_class = AgrifieldForm
    template_name = "aira/agrifield_edit/main.html"

    def get_success_url(self):
        field = Agrifield.objects.get(pk=self.kwargs["pk"])
        return reverse("home", kwargs={"username": field.owner})

    def get_context_data(self, **kwargs):
        self.object.can_edit(self.request.user)
        context = super().get_context_data(**kwargs)
        context["agrifield_owner"] = self.object.owner
        return context


class DeleteAgrifieldView(LoginRequiredMixin, DeleteView):
    model = Agrifield
    form_class = AgrifieldForm
    template_name = "aira/agrifield_delete/confirm.html"

    def get_success_url(self):
        field = Agrifield.objects.get(pk=self.kwargs["pk"])
        return reverse("home", kwargs={"username": field.owner})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        afieldobj = Agrifield.objects.get(pk=self.kwargs["pk"])
        afieldobj.can_edit(self.request.user)
        return context


class CreateAppliedIrrigationView(LoginRequiredMixin, CreateView):
    model = AppliedIrrigation
    form_class = AppliedIrrigationForm
    success_url = "/home"
    template_name_suffix = "/create"

    def get_success_url(self):
        field = Agrifield.objects.get(pk=self.kwargs["pk"])
        return reverse("home", kwargs={"username": field.owner})

    def form_valid(self, form):
        form.instance.agrifield = Agrifield.objects.get(pk=self.kwargs["pk"])
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        self.agrifield = get_object_or_404(Agrifield, pk=self.kwargs["pk"])
        self.agrifield.can_edit(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["agrifield"] = self.agrifield
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        initial_values = self.agrifield.get_latest_applied_irrigation_defaults()
        kwargs["initial"] = {**kwargs["initial"], **initial_values}
        return kwargs


class UpdateAppliedIrrigationView(LoginRequiredMixin, UpdateView):
    model = AppliedIrrigation
    form_class = AppliedIrrigationForm
    template_name_suffix = "/update"

    def get_success_url(self):
        return reverse("home", kwargs={"username": self.object.agrifield.owner})

    def get_object(self):
        applied_irrigation = super().get_object()
        applied_irrigation.agrifield.can_edit(self.request.user)
        return applied_irrigation


class DeleteAppliedIrrigationView(LoginRequiredMixin, DeleteView):
    model = AppliedIrrigation
    form_class = AppliedIrrigationForm
    template_name_suffix = "/confirm_delete"

    def get_object(self):
        applied_irrigation = super().get_object()
        applied_irrigation.agrifield.can_edit(self.request.user)
        return applied_irrigation

    def get_success_url(self):
        return reverse("home", kwargs={"username": self.object.agrifield.owner})


def remove_supervised_user_from_user_list(request):
    if request.method == "POST":
        try:
            supervised_profile = Profile.objects.get(
                user_id=int(request.POST.get("supervised_user_id")),
                supervisor=request.user,
            )
        except (TypeError, ValueError, Profile.DoesNotExist):
            raise Http404
        supervised_profile.supervisor = None
        supervised_profile.save()
        return HttpResponseRedirect(reverse("home"))
    else:
        raise Http404


class AgrifieldTimeseriesView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        agrifield = get_object_or_404(Agrifield, pk=kwargs.get("agrifield_id"))
        variable = kwargs.get("variable")
        filename = agrifield.get_point_timeseries(variable)
        return FileResponse(
            open(filename, "rb"), as_attachment=True, content_type="text_csv"
        )


class DownloadSoilAnalysisView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        agrifield = get_object_or_404(Agrifield, pk=kwargs.get("agrifield_id"))
        agrifield.can_edit(self.request.user)
        if not agrifield.soil_analysis:
            raise Http404
        return FileResponse(agrifield.soil_analysis, as_attachment=True)
