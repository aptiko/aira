from django.contrib import admin

from .models import Agrifield, AppliedIrrigation, CropType, IrrigationType, Profile


class ProfileAdmin(admin.ModelAdmin):
    exclude = ("user",)
    list_display = (
        "user",
        "first_name",
        "last_name",
        "notification",
        "supervisor",
        "supervision_question",
    )
    search_fields = ("first_name", "last_name", "notification")
    list_filter = ("supervision_question",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        obj.save()


class AgrifieldAdmin(admin.ModelAdmin):
    pass


class AppliedIrrigationAdmin(admin.ModelAdmin):
    pass


class CropTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "fek_category",
        "max_allowed_depletion",
        "kc_init",
        "kc_mid",
        "kc_end",
    )
    search_fields = ("name", "fek_category")
    list_filter = ("fek_category",)


class IrrigationTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "efficiency")
    search_fields = ("name", "efficiency")
    list_filter = ("efficiency",)


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Agrifield, AgrifieldAdmin)
admin.site.register(AppliedIrrigation, AppliedIrrigationAdmin)
admin.site.register(CropType, CropTypeAdmin)
admin.site.register(IrrigationType, IrrigationTypeAdmin)
