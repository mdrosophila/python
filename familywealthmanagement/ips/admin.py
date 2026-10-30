from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Investor, InvestmentPolicyStatement


class InvestorInline(admin.StackedInline):
    model = Investor
    can_delete = False


class InvestorUserAdmin(UserAdmin):
    """The standard user admin, with each user's investor details alongside."""
    inlines = [InvestorInline]
    list_display = ['username', 'email', 'investor_name', 'investor_phone', 'is_staff', 'date_joined']
    list_select_related = ['investor']
    search_fields = ['username', 'email', 'investor__name', 'investor__phone']

    @admin.display(description='Name')
    def investor_name(self, user):
        return getattr(user, 'investor', None) and user.investor.name

    @admin.display(description='Phone')
    def investor_phone(self, user):
        return getattr(user, 'investor', None) and user.investor.phone


admin.site.unregister(User)
admin.site.register(User, InvestorUserAdmin)


@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'user', 'created_at']
    search_fields = ['name', 'email', 'phone']


@admin.register(InvestmentPolicyStatement)
class IPSAdmin(admin.ModelAdmin):
    list_display = ['investor', 'risk_tolerance', 'required_return_pct', 'time_horizon_years', 'created_at']
