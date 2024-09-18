from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from .forms import *


# Register your models here.
class UserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'role', 'is_blocked')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
    readonly_fields = ['password']
    list_display = ('username', 'email', 'role', 'is_blocked', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('username',)


admin.site.register(User, UserAdmin)


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ['id', 'specialist', 'date', 'start_time', 'end_time', 'duration']
    list_display_links = ['specialist']
    exclude = ('duration',)


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['slot', 'client', 'is_canceled', 'status']
    list_display_links = ['slot']
