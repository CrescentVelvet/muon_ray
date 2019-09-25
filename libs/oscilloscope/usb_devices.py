import visa
import sys
from ..utils.error import Error

def find_instrument():
    resource_manager = visa.ResourceManager()
    resource_list = resource_manager.list_resources()

#Only one valid input by default
    for resource in resource_list:
        try:
            device = resource_manager.open_resource(resource)
            #TODO: Specific Exceptions
        except:
            Error("find_instrument", sys.exec_info()[0])
        else:
            return device


