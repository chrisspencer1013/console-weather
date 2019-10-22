import os
import requests
import json
from pprint import pprint as pp
import time
import threading
import enum
from secrets import owm_api_key

shared_qp = "&q=Ann%20Arbor&units=imperial&cnt=10"
base_url = "http://api.openweathermap.org/data/2.5"
CURRENT_WEATHER_URL = f"{base_url}/weather?APPID={owm_api_key}{shared_qp}"
FORECAST_URL = f"{base_url}/forecast?APPID={owm_api_key}{shared_qp}"

pprint_api_error = lambda code: print(f"API error: {code}")

pp_time_format = "%I:%M %p"
date_format = "%Y-%m-%d"
current_time = lambda: time.strftime(pp_time_format)
current_date = lambda: time.strftime(date_format)
epoch_to_time = lambda epoch: time.strftime(pp_time_format, time.localtime(epoch))
epoch_to_date = lambda epoch: time.strftime(date_format, time.localtime(epoch))

lock = threading.RLock()


def check_response(response):
    if response:
        if str(response["cod"]).startswith("4") or str(response["cod"]).startswith("5"):
            pprint_api_error(response["cod"])
    else:
        pprint_api_error("oof")


class ThreadTypes(enum.Enum):
    WEATHER_CURRENT = enum.auto()
    WEATHER_FORECAST = enum.auto()
    TIME = enum.auto()


class WeatherForecastThread(threading.Thread):
    def __init__(self, thread_type, wdd):
        threading.Thread.__init__(self)
        self.wdd = wdd
        self.thread_type = thread_type

    def update_weather_current(self):
        response = requests.get(CURRENT_WEATHER_URL).json()
        check_response(response)
        lock.acquire()
        try:
            self.wdd.update(
                {
                    "temp": f"{response['main']['temp']}°f ({response['main']['temp_min']} to {response['main']['temp_max']})",
                    "sunrise": f"{epoch_to_time(response['sys']['sunrise'])}",
                    "sunset": f"{epoch_to_time(response['sys']['sunset'])}",
                    "weather": f"{response['weather'][0]['main']} - {response['weather'][0]['description']} {' and windy' if int(response['wind']['speed']) > 13 else ''}",
                    "humidity": f"{response['main']['humidity']}%",
                }
            )
        finally:
            lock.release()

    def update_weather_forecast(self):
        response = requests.get(FORECAST_URL).json()
        check_response(response)
        for forecast in response["list"]:
            if epoch_to_date(forecast["dt"]) == current_date():
                if "rain" in str(forecast["weather"]).lower():
                    lock.acquire()
                    self.wdd.update({"rain": forecast["weather"][0]["description"] + " for today"})
                    lock.release()
                    return
                else:
                    lock.acquire()
                    self.wdd.update({"rain": "no rain forcasted for today"})
                    lock.release()

        # pp(response)

    def update_time(self):
        lock.acquire()
        self.wdd.update({"time": current_time()})
        lock.release()

    def display_weather(self):
        lock.acquire()
        os.system("clear")
        for k, v in self.wdd.items():
            if isinstance(self.wdd[k], str):
                while "  " in self.wdd[k] or "\n" in self.wdd[k]:
                    self.wdd[k] = self.wdd[k].replace("  ", " ").replace("\n", " ")
            print(f"{k}: {self.wdd[k]}")
        lock.release()

    def run(self):
        while True:
            if self.thread_type == ThreadTypes.WEATHER_CURRENT:
                self.update_weather_current()
            elif self.thread_type == ThreadTypes.WEATHER_FORECAST:
                self.update_weather_forecast()
            elif self.thread_type == ThreadTypes.TIME:
                self.update_time()

            self.display_weather()

            if self.thread_type in (ThreadTypes.WEATHER_CURRENT, ThreadTypes.WEATHER_FORECAST):
                time.sleep(300)
            else:
                time.sleep(5)


def create_and_start_threads():
    wdd = {}  # shared weather display dictionary
    currentThread = WeatherForecastThread(ThreadTypes.WEATHER_CURRENT, wdd)
    forecastThread = WeatherForecastThread(ThreadTypes.WEATHER_FORECAST, wdd)
    timeThread = WeatherForecastThread(ThreadTypes.TIME, wdd)
    currentThread.start()
    forecastThread.start()
    timeThread.start()
    while True:
        pass


def example_responses():
    print("Current weather request:")
    pp(requests.get(CURRENT_WEATHER_URL).json())

    print("\n\nForecast weather request:")
    pp(requests.get(FORECAST_URL).json())


if __name__ == "__main__":
    create_and_start_threads()
    # example_responses()

