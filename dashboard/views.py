from django.shortcuts import render

from .services.dispatch_service import get_dispatch_data
from .services.Local_dispatch import get_dispatch_data_L
from .services.total_dispatch import get_dispatch_data_tot
from dashboard.services.Fabric_Inventory.fabric_inventory_service import (
    get_fabric_inventory_kpis,
    get_fresh_data,
    get_fresh_grade_data,
    get_fresh_manager_data,
    get_fresh_aging_data
)


def home(request):
    data = {}

    # main card
    data.update(get_dispatch_data())

    # local card
    data.update(get_dispatch_data_L())
    
    #total card
    data.update(get_dispatch_data_tot())

    return render(request, "dashboard/home.html", data)



# def fabric(request):
#     data = {}
#     data.update(get_fabric_inventory_kpis())
#     return render(request, "dashboard/fabric_inventory/dashboard.html", data)



def fabric(request):
    data = {}

    # Top KPIs
    data.update(get_fabric_inventory_kpis())

    # FRESH Card
    data.update(get_fresh_data())
    data["fresh_grade_list"] = get_fresh_grade_data()
    data["fresh_manager_list"] = get_fresh_manager_data()
    data["fresh_aging_list"] = get_fresh_aging_data()

    return render(request, "dashboard/fabric_inventory/dashboard.html", data)