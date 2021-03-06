#!/usr/bin/python
"""
mqtt-wunderground.py
Simple MQTT publisher of weather data using the WeatherUnderground API.
Publishes the current temperature, relative humidity, precipitation, pressure,
windspeed and winddirection from a given Personal Weather Station

Original script by Simon Vanderveldt
https://github.com/simonvanderveldt/mqtt-wunderground
Modified to read config from file, export json and follow the mqtt-smarthome architecture
"""

# IMPORTS
import urllib2
import json
import paho.mqtt.client as paho
import time
#import os
import logging


# Log to STDOUT
logger = logging.getLogger("mqtt-wunderground")
logger.setLevel(logging.INFO)
consoleHandler = logging.StreamHandler()
logger.addHandler(consoleHandler)


# Component config
config = {}
config['deviceid'] = "wunderground"
config['publish_topic'] = "wunderground/status"
config['config_topic'] = "wunderground/config"
config['updaterate'] = 900  # in seconds
config['wu_api_key'] = ""
config['country'] = ""
config['city'] = ""
config['broker_address'] = "localhost"
config['broker_port'] = 1883
config['json'] = 0


# Create the callbacks for Mosquitto
def on_connect(self, mosq, obj, rc):
    if rc == 0:
        logger.info("Connected to broker " + str(config['broker_address'] + ":" + str(config['broker_port'])))

        # Subscribe to device config
        logger.info("Subscribing to device config at " + config['config_topic'] + "/#")
        mqttclient.subscribe(config['config_topic'] + "/#")
        # Publish connected status
        mqttclient.publish(config['publish_topic'] +"/connected",2,qos=2,retain=True)


def on_subscribe(mosq, obj, mid, granted_qos):
    logger.info("Subscribed with message ID " + str(mid) + " and QOS " + str(granted_qos) + " acknowledged by broker")


def on_message(mosq, obj, msg):
    logger.info("Received message: " + msg.topic + ":" + msg.payload)
    if msg.topic.startswith(config['config_topic']):
        configitem = msg.topic.split('/')[-1]
        if configitem in config:
            # TODO unset when value set to ""
            logger.info("Setting configuration " + configitem + " to " + msg.payload)
            config[configitem] = msg.payload
        else:
            logger.info("Ignoring unknown configuration item " + configitem)


def on_publish(mosq, obj, mid):
    # logger.info("Published message with message ID: "+str(mid))
    pass


def wunderground_get_weather():
    if not config['wu_api_key'] or not config['country'] or not config['city'] or not config['publish_topic']:
        logger.info("Required configuration items not set, skipping the Weather Underground update")
        return

    # Parse the WeatherUnderground json response
    wu_url = "http://api.wunderground.com/api/" + config['wu_api_key'] + "/conditions/q/" + config['country'] + "/" + config['city'] + ".json"
    logger.info("Getting Weather Underground data from " + wu_url)

    try: 
        resonse = urllib2.urlopen(wu_url)
    except urllib2.URLError as e:
        logger.error('URLError: ' + str(wu_url) + ': ' + str(e.reason))
        return None
    except Exception:
        import traceback
        logger.error('Exception: ' + traceback.format_exc())
        return None

    parsed_json = json.load(resonse)
    resonse.close()

    temperature = str(parsed_json['current_observation']['temp_c'])

    # Strip off the last character of the relative humidity because we want an int
    # but we get a % as return from the weatherunderground API
    humidity = str(parsed_json['current_observation']['relative_humidity'][:-1])

    # TODO fix return value for precip from WU API of t/T for trace of rain to 0
    # or sth like 0.1
    try:
        precipitation = str(int(parsed_json['current_observation']['precip_1hr_metric']))
    except ValueError:
        logger.info("Precipitation returned a wrong value '" + str(parsed_json['current_observation']['precip_1hr_metric'][:-1]) +"', replacing with '0'")
        precipitation = str(0)

    pressure = str(parsed_json['current_observation']['pressure_mb'])
    windspeed = str(parsed_json['current_observation']['wind_kph'])
    winddirection = str(parsed_json['current_observation']['wind_degrees'])

#   Building message info as JSON package
    send_msg = {
        'temperature': temperature,
        'humidity': humidity,
        'precipitation': precipitation,
        'pressure': pressure,
        'windspeed': windspeed,
        'winddirection': winddirection
    }

#  Publish data json or single
    if config['json'] == 1 :
        mqttclient.publish(config['publish_topic'] + "/json", payload=json.dumps(send_msg), qos=2, retain=True)
        logger.info("Published weather json data to " + str(config['publish_topic']))
    else :
        mqttclient.publish(config['publish_topic'] + "/temperature", temperature, retain=True)
        mqttclient.publish(config['publish_topic'] + "/humidity", humidity, retain=True)
        mqttclient.publish(config['publish_topic'] + "/precipitation", precipitation, retain=True)
        mqttclient.publish(config['publish_topic'] + "/pressure", pressure, retain=True)
        mqttclient.publish(config['publish_topic'] + "/windspeed", windspeed, retain=True)
        mqttclient.publish(config['publish_topic'] + "/winddirection", winddirection, retain=True)
        logger.info("Published " + str(config['deviceid']) + " data to " + str(config['publish_topic']))

    

def wunderground_get_suncalc():
    if not config['wu_api_key'] or not config['country'] or not config['city'] or not config['publish_topic']:
        logger.info("Required configuration items not set, skipping the Weather Underground update")
        return

    # Parse the WeatherUnderground json response
    wu_url = "http://api.wunderground.com/api/" + config['wu_api_key'] + "/astronomy/q/" + config['country'] + "/" + config['city'] + ".json"
    logger.info("Getting sunrise and sunset data from " + wu_url)

    try:
        response = urllib2.urlopen(wu_url)
    except urllib2.URLError as e:
        logger.error('URLError: ' + str(wu_url) + ': ' + str(e.reason))
        return None
    except Exception:
        import traceback
        logger.error('Exception: ' + traceback.format_exc())
        return None

    parsed_json = json.load(response)
    response.close()

    sunrise = str(parsed_json['moon_phase']['sunrise']['hour'].zfill(2) + ":" + parsed_json['moon_phase']['sunrise']['minute'].zfill(2))
    sunset = str(parsed_json['moon_phase']['sunset']['hour'].zfill(2) + ":" + parsed_json['moon_phase']['sunrise']['minute'].zfill(2))

#   Publish the values we parsed from the feed to the broker

#   Building message info as JSON package
    send_msg = {
        'sunrise': sunrise,
        'sunset': sunset
    }

    if config['json'] == 1 :
        mqttclient.publish(config['publish_topic'] + "/json", payload=json.dumps(send_msg), qos=2, retain=True)
        logger.info("Published sunrise and sunset json data to " + str(config['publish_topic']))
    else :
        mqttclient.publish(config['publish_topic'] + "/sunrise", sunrise, retain=True)
        mqttclient.publish(config['publish_topic'] + "/sunset", sunset, retain=True)
        logger.info("Published sunrise and sunsat data data to " + str(config['publish_topic']))



# Create the Mosquitto client
mqttclient = paho.Client()

# Bind the Mosquitte events to our event handlers
mqttclient.on_connect = on_connect
mqttclient.on_subscribe = on_subscribe
mqttclient.on_message = on_message
mqttclient.on_publish = on_publish


# Set the last will, connect to broker, publish connected
logger.info("Connecting to broker " + config['broker_address'] + ":" + str(config['broker_port']))
mqttclient.will_set(config['publish_topic'] +"/connected",0,qos=2,retain=True)
mqttclient.connect(config['broker_address'], config['broker_port'], 60)
mqttclient.publish(config['publish_topic'] +"/connected",1,qos=1,retain=True)
# Start the Mosquitto loop in a non-blocking way (uses threading)
mqttclient.loop_start()

time.sleep(5)

rc = 0
while rc == 0:
    wunderground_get_weather()
    wunderground_get_suncalc()
    time.sleep(config['updaterate'])
    pass
