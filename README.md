# MQTT-Wunderground

Original script https://github.com/simonvanderveldt/mqtt-wunderground
Discord Web Hook test

Simple MQTT publisher of weather data using the WeatherUnderground API.
Publishes the current temperature, relative humidity, precipitation, pressure, windspeed, winddirection as well as sunrise and sunset times from a location.



mqtt-wunderground reads its config from the MQTT topic passed in the `config_topic` or from variables set within the file itself. 
- deviceid: The name to use for this instance of MQTT-Wunderground. For example `weather-home`
- publish_topic: The parent topic that all measurements will be published to
- config_topic: The topic config parameters can be published too
- updaterate: Time in seconds between updates
- wu_api_key: Wunderground API Key
- country: Two digit country code
- city: Your local zipcode
- broker_address: MQTT server address. Defaults to localhost
- broker_port: MQTT server port. Defaults to 1883
- json: Publish data as json to topic wunderground/status/json. 0 = off , 1 = on
