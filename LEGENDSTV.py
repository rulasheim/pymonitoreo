import requests
import json

url = "https://legendstv.com.mx/21reseller/login"
response = requests.get(url)
payload = {
    "username": "Raúl",
    "password": "raul@ejemplo",
}

headers = {
    
}

response = requests.post(url, data=json.dumps(payload), headers=headers)

print(response.status_code)
print(response.json())
