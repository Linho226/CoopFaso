from django.contrib import admin
from django.shortcuts import redirect


class CoopFasoAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        return redirect('accounts:dashboard')


def configure_admin_site():
    if not isinstance(admin.site, CoopFasoAdminSite):
        admin.site.__class__ = CoopFasoAdminSite
    admin.site.site_header = 'Administration CoopFaso'
    admin.site.site_title = 'CoopFaso Admin'
    admin.site.index_title = 'Gestion de la plateforme'
