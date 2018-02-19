#!/usr/bin/python3

import requests
import json
import logging
from collections import OrderedDict


# A method to obtain the region in which the device is located from the configuration file
# The configuration file should be JSON
# Takes deviceId as parameter
def get_region(deviceId):

    """ 
    Open the configuration file and find the region the device is located.
    It returns the region the device is located
    """
    configRegions = {}

    try:
        with open('configregions.json', 'r') as configFile:
            configRegions = json.load(configFile)
    except OSError as e:
        logging.error("Can not find configuration file {}".format(e))
        raise

    for regions in configRegions['regions']:
        for key, value in regions.items():
            for lists in value:
                for list in lists.values():
                    if list == deviceId:
                        association = {list:key}

                        return association


# A method fetches the network resources from the NETSTRATOS
def get_links():

    """ 
    GET the links data from the NETSTRATOS.
    If the response is a successful operation, it returns the JSON format of the response
    """

    url = 'http://172.28.48.106:8181/onos/v1/links'
    authorization = ('onos', 'rocks')

    response = requests.get(url, auth = authorization)

    if response.status_code != 200:
        msg = "call to NetSTRATOS failed, status code {} {}".format(response.status_code, response.content.decode("utf-8"))
        logging.error(msg)
        response.raise_for_status()

    return response.json()


# A method to obtain the port speed of the device
# Takes deviceId and switchPortId as parameters
def get_portSpeed(deviceId, switchPortId):

    """ 
    GET the ports for the NetSTRATOS switches and compute the port speed. 
    If the response operation is successful, it returns the portSpeed.
    """

    id = deviceId.replace(':','%3A')
    url = 'http://172.28.48.106:8181/onos/v1/devices/{0}/ports'.format(id)
    authorization = ('onos', 'rocks')

    response = requests.get(url, auth = authorization)

    if response.status_code != 200:
        msg = "call to NetSTRATOS failed, status code {} {}".format(response.status_code, response.content.decode("utf-8"))
        logging.error(msg)
        response.raise_for_status()

    ports_dict = response.json()
    portSpeeds = []

    for port in ports_dict['ports']:
        portId = port.get('port')

        if portId != switchPortId:
            continue
        else:
            portSpeed = port.get('portSpeed')
            return portSpeed


# A method to map the NETSTRATOS data to FOGGY format
def create_relationships():

    """ 
    Takes the links and port information of the switch collected from the NETSTRATOS and 
    creates a JSON file that is suitable for the FOGGY API.
    """

    data_dict = get_links()
    relationships_list =  []
    relationship_id = 1

    for link in data_dict['links']:

        sourceDeviceId = link.get('src',{}).get('device')
        destDeviceId = link.get('dst',{}).get('device')
        srcAssociation = get_region(sourceDeviceId)
        dstAssociation = get_region(destDeviceId)

        if (srcAssociation.get(sourceDeviceId) == dstAssociation.get(destDeviceId)):
            continue

        relationship = OrderedDict()
        relationship["Id"] = "relationship" + str(relationship_id)
        relationship["endpoint_a"] = srcAssociation.get(sourceDeviceId)
        relationship["endpoint_b"] = dstAssociation.get(destDeviceId)

        sourcePort = link.get('src', {}).get('port')
        destPort = link.get('dst', {}).get('port')
        srcPortSpeed = get_portSpeed(sourceDeviceId, sourcePort)
        dstPortSpeed = get_portSpeed(destDeviceId, destPort)

        relationship["bandwidth"] = min(srcPortSpeed, dstPortSpeed)
        relationship["latency"] = link.get('annotations',{}).get('latency')
        relationship["status"] = link.get('state')

        relationships_list.append(relationship)
        relationship_id = relationship_id + 1

    relationships_object = {'relationships' : relationships_list}

    print(json.dumps(relationships_object, indent=4))

    return json.dumps(relationships_object, indent=4)


# A method to send the data to the foggy API 
def push_relationships():

    """ 
    POST the  NETSTRATOS data and to the foggy API. 
    If the response operation is successful, a message is printed on the client screen. 
    """
    relationships = create_relationships()
    url = 'http://172.28.48.106:8181/onos/v1/relationships'
    authorization = ('onos', 'rocks')

    response = requests.post(url, auth = authorization, json = relationships)

    if response.status_code != 200:
        msg = "call to foggy inventory failed, status code {} {}".format(response.status_code, response.content.decode("utf-8"))
        logging.error(msg)
        response.raise_for_status()

    logging.info('Created task. ID: {}'.format(response.status_code))


push_relationships()
