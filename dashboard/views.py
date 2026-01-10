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
from dashboard.services.sample.sample_first import sample_first 
from dashboard.services.sample.sample_unit import unit_dashboard_data 
from dashboard.services.sample.top20_service import top20_data 

from dashboard.services.order_in_hand.order_in_hand_exp import order_in_hand_exp
from dashboard.services.order_in_hand.order_in_hand_loc import order_in_hand_local
from dashboard.services.order_in_hand.order_in_hand_total import order_in_hand_total





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

def sample(request):
    context = sample_first()
    context["units"] = unit_dashboard_data()
    context["top20"] = top20_data()
    return render(request, "dashboard/sample/samplefirst.html", context)





def oih(request):
    context = {
        "export": order_in_hand_exp(),
        "local": order_in_hand_local(),
        "total": order_in_hand_total()
    }
    return render(request, "dashboard/OIH/order_in_hand.html", context)


