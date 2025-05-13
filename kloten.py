

import json


with open('/home/burgh512/Python_files/Agentic-AI/CW-Repeated-Calls/data/scenarios/scenario_specifications_test.json', 'r') as file:
    pay_load = json.load(file)




print(len(pay_load[0]['scenario_details']['recommended_system_response']))
print(type(pay_load[0]['scenario_details']['recommended_system_response']))
print((pay_load[0]['scenario_details']['recommended_system_response'])[0])


