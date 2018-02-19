MAPPING NETSTRATOS TO FOGGY

This python code maps the NETSTRATOS data to FOGGY data format. 

The HTTP REST library used in our code to fetch resources from the NETSTRATOS and to send the approprait JSON format to the FOGGY is requests (http://docs.python-requests.org/en/master/). To install this library use: 
#pip install requests

To do the mapping, first we create a configuration file in JSON format to allocate the switches in NETSTRATOS to a specific region in FOGGY. The configuration JSON file format looks like the following:

{

  "regions" : [
             {"reg1": [
                       {"switch_id":"of:0000000000000001"},
                       {"switch_id":"of:0000000000000002"}
                      ]},
             {"reg2": [
                       {"switch_id":"of:0000000000000003"},
                       {"switch_id":"of:0000000000000004"}
                      ]}
            ] 

}

We can add region or remove region from the configuration file. We can also add or remove switches from a particular region based on our requirement.

Then, it fetches the required resources (bandwidth, latency and link status) from the NETSTRATOS API. 

Based on the resources obtained from the NETSTRATOS and the configuration file, the code creates a JSON file in the following format:

{
    "relationships": [
        {
            "Id": "relationship1",
            "endpoint_a": "reg1",
            "endpoint_b": "reg2",
            "bandwidth": 10000,
            "latency": "1000000",
            "status": "ACTIVE"
        },
        {
            "Id": "relationship2",
            "endpoint_a": "reg1",
            "endpoint_b": "reg2",
            "bandwidth": 10000,
            "latency": "1000000",
            "status": "ACTIVE"
        }
    ]
}

Finaly, it sends the file to the FOGGY API.


# PYTHONREST
