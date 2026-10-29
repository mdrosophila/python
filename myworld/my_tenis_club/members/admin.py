from django.contrib import admin
from .models import Member

# Register your models here.
class MemberAdmin(admin.ModelAdmin):
  list_display = ("first_name", "last_name", "join_date",)
admin.site.register(Member, MemberAdmin)
