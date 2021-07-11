#! python3
# Prints the current weather for a location from the command line.

import json, requests, sys

APPID = 'YOUR_APPID_HERE'

# Compute location from command line arguments
if len(sys.argv) < 2:
    print('Usage: quickweather.py city_name, 2-letter_country_code')
    sys.exit()
location = ' '.join(sys.argv[1:])

# Download the JSON data from openweathermap.org's API
url ='http://api.openweathermap.org/data/2.5/forecast/daily?q=%s&cnt=3&APPID=%s' % (location, APPID)
response = requests.get(url)
response.raise_for_status()

# Load JSON data into Python variable.
weatherData = json.loads(response.text)

# Uncomment to see the raw JSON text:
#print(response.text)

w = weatherData['list']
print('Current weather in %s:' % (location))
print(w[0]['weather'][0]['main'], '-', w[0]['weather'][0]['description'])
print()
print('Tomorrow:')
print(w[1]['weather'][0]['main'], '-', w[1]['weather'][0]['description'])
print()
print('Day after tomorrow:')
print(w[2]['weather'][0]['main'], '-', w[2]['weather'][0]['description'])
