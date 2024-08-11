import bpy

def add_driver(target_obj, driven_prop_str, driver_obj, driver_prop_str):

    fcurve = target_obj.driver_add(driven_prop_str)
    driver = fcurve.driver

    var = driver.variables.new()
    var.type = 'SINGLE_PROP'
    var.name = "param"

    # variables have one or two targets 
    target = var.targets[0]
    target.id = driver_obj.id_data
    target.data_path = driver_prop_str
    driver.expression = "param"
