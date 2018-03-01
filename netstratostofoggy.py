#!/usr/bin/python3

import requests
import json
import logging
from collections import OrderedDict

logging.basicConfig(level=logging.DEBUG)


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
                for lst in lists.values():
                    if lst == deviceId:
                        association = {deviceId:key}

                        return association


# A method to fetch the network resources from the NETSTRATOS
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


# A method to obtain the location of the device (latitude and longitude)
# Takes deviceId as parameter
def get_location(deviceId):

    """ 
    GET the location for the NetSTRATOS switches. 
    If the response operation is successful, it returns the portSpeed.
    """

    id = deviceId.replace(':','%3A')
    url = 'http://172.28.48.106:8181/onos/v1/devices/{0}'.format(id)
    authorization = ('onos', 'rocks')

    response = requests.get(url, auth = authorization)

    if response.status_code != 200:
        msg = "call to NetSTRATOS failed, status code {} {}".format(response.status_code, response.content.decode("utf-8"))
        logging.error(msg)
        response.raise_for_status()

    device_dict = response.json()
    location = '{},{}'.format(device_dict['annotations'].get('latitude'),device_dict['annotations'].get('longitude'))
    return location


# A method to map the NETSTRATOS data to FOGGY format
def create_relationships():

    """ 
    Takes the links and port information of the switch collected from the NETSTRATOS and 
    creates a JSON file that is suitable for the FOGGY API.
    """

    data_dict = get_links()
    relationshipsList =  []
    relationshipId = 1

    for link in data_dict['links']:

        sourceDeviceId = link.get('src',{}).get('device')
        destDeviceId = link.get('dst',{}).get('device')
        srcAssociation = get_region(sourceDeviceId)
        dstAssociation = get_region(destDeviceId)

        if (srcAssociation.get(sourceDeviceId) == dstAssociation.get(destDeviceId)):
            continue

        relationship = OrderedDict()
        relationship["id"] = "relationship" + str(relationshipId)
        relationship["endpoint_a"] = srcAssociation.get(sourceDeviceId)
        relationship["endpoint_b"] = dstAssociation.get(destDeviceId)
        relationship["bandwidth"] = link.get('annotations',{}).get('bandwidth')
        relationship["latency"] = link.get('annotations',{}).get('latency')
        relationship["status"] = link.get('state')

        relationshipsList.append(relationship)
        relationshipId = relationshipId + 1

    relationshipsDict = {'relationships' : relationshipsList}

    return json.dumps(relationshipsDict, indent=4)


# A method map NETSTRATOS switches to foggy regions
def create_regions():

    """
    It takes the regions configuration files and the relationships data created in create_relationships()
    to create a another json data that is coherent with foggy regions data.
    """

    configRegions = {}
    try:
        with open('configregions.json', 'r') as configFile:
            configRegions = json.load(configFile)
    except OSError as e:
        logging.error("Can not find configuration file {}".format(e))
        raise

    relationships = json.loads(create_relationships())
    regionList = []
    for region in configRegions['regions']:

        createRegion = OrderedDict()
        for k, v in region.items():
            createRegion['id'] = k

            location = get_location(v[0]['switch_id'])
            createRegion['location'] = location

            relationshipList = []
            for relationship in relationships['relationships']:
                if k == relationship.get('endpoint_a'):
                    relationshipList.append({'relationship_id':relationship.get('id')})
            createRegion['relationships'] = relationshipList

        regionList.append(createRegion)

    regionDict = {'regions' : regionList}

    return json.dumps(regionDict, indent=4)


# A method to send the data to the foggy API 
def push_relationships():

    """ 
    POST the  NETSTRATOS data and to the foggy API. 
    If the response operation is successful, a message displayed on the console 
    """

    relationships = json.loads(create_relationships())
    url = 'http://172.28.48.119:32768/sbrk03/foggy-inventory/1.0.0/relationships'

    for relationship in relationships['relationships']:

        response = requests.post(url, data = json.dumps(relationship, indent=4), headers={'Content-Type':'application/json'})
        if response.status_code != 200:
            msg = "Call to foggy api failed, status code {} {}".format(response.status_code, response.content.decode("utf-8"))
            logging.error(msg)
            response.raise_for_status()

        logging.debug('Created the Relationships data. ID: {}'.format(response.status_code))


# A method to send region data to the foggy
def push_regions():

    """ 
    Send the regions data created with create_region() to foggy regions. 
    If the response operation is successful, a message displayed on the console
    """

    regions = json.loads(create_regions())
    url = 'http://172.28.48.119:32768/sbrk03/foggy-inventory/1.0.0/regions'

    for region in regions['regions']:

        response = requests.post(url, data = json.dumps(region, indent=4), headers={'Content-Type':'application/json'})
        if response.status_code != 200:
            msg = "Call to foggy api failed, status code {} {}".format(response.status_code, response.content.decode("utf-8"))
            logging.error(msg)
            response.raise_for_status()

        logging.debug('Created the Regions data. ID: {}'.format(response.status_code))


def execute_tasks():

    push_relationships()

    push_regions()

if __name__=='__main__':

    execute_tasks()
