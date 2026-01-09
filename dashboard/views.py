from django.shortcuts import render

from .services.dispatch_service import get_dispatch_data
from .services.Local_dispatch import get_dispatch_data_L
from .services.total_dispatch import get_dispatch_data_tot

def home(request):
    data = {}

    # main card
    data.update(get_dispatch_data())

    # local card
    data.update(get_dispatch_data_L())

    data.update(get_dispatch_data_tot())

    return render(request, "dashboard/home.html", data)
