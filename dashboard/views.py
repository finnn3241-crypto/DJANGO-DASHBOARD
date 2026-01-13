from django.shortcuts import render

from .services.dispatch.dispatch_service import get_dispatch_data
from .services.dispatch.Local_dispatch import get_dispatch_data_L
from .services.dispatch.total_dispatch import get_dispatch_data_tot
from dashboard.services.Fabric_Inventory.fabric_inventory_service import (
    get_fabric_inventory_kpis,
    get_fresh_data,
    get_fresh_grade_data,
    get_fresh_manager_data,
    get_fresh_aging_data,
    get_stock_data,
    get_stock_grade_data,
    get_stock_manager_data,
    get_stock_aging_data,
    get_sample_data,
    get_sample_grade_data,
    get_sample_manager_data,
    get_sample_aging_data,
    get_sales_return_data,
    get_sales_return_grade_data,
    get_sales_return_manager_data,
    get_sales_return_aging_data
)
from dashboard.services.sample.sample_first import sample_first 
from dashboard.services.sample.sample_unit import unit_dashboard_data 
from dashboard.services.sample.top20_service import top20_data 

from dashboard.services.order_in_hand.order_in_hand_exp import order_in_hand_exp
from dashboard.services.order_in_hand.order_in_hand_loc import order_in_hand_local
from dashboard.services.order_in_hand.order_in_hand_total import order_in_hand_total

from dashboard.services.Production.production import ( 
    warping_dashboard,
    dyeing_dashboard, 
    weaving_dashboard, 
    finishing_dashboard,
    washing_dashboard,
    mercerize_dashboard,
    stenter_dashboard,
    sanfor_dashboard,
    inspection_dashboard
)

from dashboard.services.Yarn_Inventory.yarn_inventory import ( 
    get_yarn_inventory_kpis,
    get_fresh_inventory_data,
    get_aging_6_12_data,
    get_aging_1_2_data,
    get_aging_2_data
    )



def index(request):
    data = {}
    return render(request, "dashboard/mainPage/index.html", data)

def home(request):
    data = {}

    # main card
    data.update(get_dispatch_data())

    # local card
    data.update(get_dispatch_data_L())
    
    #total card
    data.update(get_dispatch_data_tot())

    return render(request, "dashboard/dispatch/home.html", data)



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

    # STOCK Card
    data.update(get_stock_data())
    data["stock_grade_list"] = get_stock_grade_data()
    data["stock_manager_list"] = get_stock_manager_data()
    data["stock_aging_list"] = get_stock_aging_data()

    # SAMPLE Card
    data.update(get_sample_data())
    data["sample_grade_list"] = get_sample_grade_data()
    data["sample_manager_list"] = get_sample_manager_data()
    data["sample_aging_list"] = get_sample_aging_data()

    # SALES RETURN Card
    data.update(get_sales_return_data())
    data["sales_return_grade_list"] = get_sales_return_grade_data()
    data["sales_return_manager_list"] = get_sales_return_manager_data()
    data["sales_return_aging_list"] = get_sales_return_aging_data()


    return render(request, "dashboard/fabric_inventory/fabric_kpis.html", data)

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


def prod(request):
    context = {
        "warp": warping_dashboard(),
        "dye": dyeing_dashboard(),
        "weav": weaving_dashboard(),
        "sing": finishing_dashboard(),
        "wash": washing_dashboard(),
        "mercerz": mercerize_dashboard(),
        "stent": stenter_dashboard(),
        "sanfor": sanfor_dashboard(),
        "inspec":  inspection_dashboard()
    }
    return render(request, "dashboard/Production/Production.html", context)


def yarn(request):
    context = {
        "kpis": get_yarn_inventory_kpis(),
        "aging": get_fresh_inventory_data(),   
        "aging_6_12": get_aging_6_12_data(),
        "aging_1_2": get_aging_1_2_data(),
        "aging_2": get_aging_2_data(),
    }
    return render(request, "dashboard/yarn_inventory/yarn_kpis.html", context)



