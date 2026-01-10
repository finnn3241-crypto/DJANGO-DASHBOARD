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
from .services.Production.warping import (
    get_warping_data
)

from .services.Production.dyeing import (
    get_dyeing_data 
)

from .services.Production.weaving import (
    get_weaving_data
)

from .services.Order_In_Hand.oih_export import (
    get_export_dispatch_kpis

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

def orderInHand(request):
    data = {}
    data.update( get_export_dispatch_kpis() )
    return render(request, "dashboard/order_in_hand/home.html", data)

def production(request):
    data = {}
    # Combine data from both services
    data.update(get_warping_data(request)) 
    data.update(get_dyeing_data(request))
    data.update(get_weaving_data(request))

    return render(request, "dashboard/production/warping.html", data)