import os
from datetime import datetime, date
import responses
import numpy as np
from enum import Enum
import math
import requests
import random
import sklearn.cluster
import gmaps
from IPython import display
import json

gmaps_key = os.environ["GMAPS_API_KEY"]
gmaps.configure(api_key=gmaps_key)

cat_json = {}
with open("..\json\categories.json") as f:
    cat_json = json.load(f)

class Category:
    def __init__(self, name:str, categories_list:list, ignore:bool, start_time:int = None, end_time:int = None, duration:int = None):
        self.name = name
        self.ignore = ignore
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration
        self.categories_list = categories_list
        self.probability: int = None
    
    def set_probability(self, prob):
        self.probability = prob
        
accommodation = Category("accommodation", ["lodging", "rv_park", "campground"], True)
car_services = Category("car_services", cat_json["car_services"], True)
christianity = Category("christianity", cat_json["christianity"], True)
culture = Category("culture", cat_json["culture"], False, 9, 19, 2)
family_entertainment = Category("family_entertainment", cat_json["family_entertainment"], False, 8, 20, 3)
food_and_drink = Category("food_and_drink", cat_json["food_and_drink"], False, 7, 24, 2)
hinduism = Category("hinduism", cat_json["hinduism"], True)
islam = Category("islam", cat_json["islam"], True)
judaism = Category("judaism", cat_json["judaism"], True)
nightlife = Category("nightlife", cat_json["nightlife"], False, 21, 6, 2)
shopping = Category("shopping", cat_json["shopping"], True)
sports_and_fitness = Category("sports_and_fitness", cat_json["sports_and_fitness"], False, 8, 22, 3)
travel_services = Category("travel_services", cat_json["travel_services"], True)
wellness = Category("wellness", cat_json["wellness"], False, 8, 22, 2)

cheap_travel = cat_json["cheap_transport"]
expensive_travel = cat_json["expensive_transport"]

categories_list = [accommodation, car_services, christianity, culture, family_entertainment, food_and_drink, hinduism, islam, judaism, nightlife, shopping, sports_and_fitness, travel_services, wellness]

class TravelWith(Enum):
    alone = 1
    with_partner = 2
    with_family = 3
    
class User:
    def __init__(self, preferences:dict, destination:str, start_time:datetime, end_time:datetime, public_transport_accept:bool, bicycle_travel_accept:bool, car_travel_accept:bool, cost_rate:int, travel_with:TravelWith):
        self.preferences = preferences
        self.destination = destination
        self.start_time = start_time
        self.end_time = end_time
        self.public_transport_accept = public_transport_accept
        self.bicycle_travel_accept = bicycle_travel_accept
        self.car_travel_accept = car_travel_accept
        self.cost_rate = cost_rate
        self.travel_with = travel_with
        self.transport_mode = 'walking'
        self.available_days = []
        self.main_preferences = {}
        self.religion = {}
        self.sorted_categories = []
        self.num_of_places_for_main_categories = []
        self.num_of_places_for_main_categories_for_search = []
        self.found_places_lists =[]
        self.substitutes_places = []
        self.substitutes_places_names = []
        #################
        self.urls = []
        self.layers = []
        self.lists_of_places_for_each_day = []
        ###############
        self.prepare_available_days()
        self.get_main_preferences()
        self.get_religion()
        self.prepare_transport_mode()
        self.get_the_most_interesting_categories()
        self.get_sorted_cat_list()
        self.get_number_of_places_from_each_category_to_see()
        self.get_number_of_places_to_be_found()
        self.prepare_city_coordinates()
        self.prepare_search_radius()
        self.prepare_found_places_lists()
        self.reduce_places_number()
        self.count_available_hours_num()
        self.count_total_num_places_to_see()
        self.set_num_of_places_for_each_day()
        self.temporary_places_grouping()
        self.show_map_for_each_day()
        self.show_other_interesting_places()    

    def get_days_number(self):
        return len(self.available_days)
    
    def get_daily_places_list(self, i):
        return self.lists_of_places_for_each_day[i]
    
    def get_daily_url_link(self, i: int):
        return self.urls[i]
    
    def get_daily_interactive_map(self, i: int):
        return self.layers[i]
    
    def get_another_places_list(self):
        # substitutes_places_names = []
        # for pl in self.substitutes_places:
        #     place :Place = pl
        #     substitutes_places_names.append((place.get_place_name(), place.get_place_coordinates()))
        return self.substitutes_places_names
        

    def prepare_available_days(self):
        days_in_city = self.end_time.day - self.start_time.day + 1
        prob_values_mean =  np.mean(list(self.preferences.values()))
        prob_values_median =  np.median(list(self.preferences.values()))

        #Here we define time slots for city exploration taking into account user nightlife's preference
        if self.preferences["nightlife"] > 1.5 * prob_values_mean and self.preferences["nightlife"]>=prob_values_median:
            start_hour = 9
            end_hour = 24
        elif self.preferences["nightlife"] <= 1.5 * prob_values_mean and self.preferences["nightlife"] >= prob_values_mean or self.preferences["nightlife"] > 1.5 * prob_values_mean and self.preferences["nightlife"]<prob_values_median:
            start_hour = 8
            end_hour = 24
        else:
            start_hour = 7
            end_hour = 23
        
        for i in range (days_in_city):
            if i == 0:
                if self.start_time.hour > start_hour:
                    curr_day = CityDay(self.start_time.hour, end_hour)
                else: 
                    curr_day = CityDay(start_hour, end_hour)
            elif i == days_in_city - 1:
                if self.end_time.hour > end_hour:
                    curr_day = CityDay(start_hour, end_hour)
                else: 
                    curr_day = CityDay(start_hour, self.end_time.hour)
            else:
                curr_day = CityDay(start_hour, end_hour)
                    
            self.available_days.append(curr_day)

    def get_main_preferences(self):
        remove_keys = ['christianity', 'judaism', 'hinduism', 'islam', 'car_services', 'travel_sevices']
        self.main_preferences = {key: value for key, value in self.preferences.items() if key not in remove_keys}
            
    def get_religion(self):
        #if one has really bigger prob than others take the one which user is the most interested in, else check if probabilities are similiar to each other and relatively big, then propose some religion places to see, else if one is bigger and relatively big then propose one temple
        religion_keys = ['christianity', 'judaism', 'hinduism', 'islam']
        religions = {key: value for key, value in self.preferences.items() if key in religion_keys}
        sorted_list = sorted(religions.items(), key=lambda x: x[1], reverse=True)
        sorted_religion = {item[0]: item[1] for item in sorted_list}
        
        iter_ = iter(sorted_religion.items())
        first_item = next(iter_)
        second_item = next(iter_)
        third_item = next(iter_)
        fourth_item = next(iter_)
        
        if first_item[1] > 1.5 * second_item[1] and first_item[1] > 0.2:
            religion = first_item
            self.religion = {item[0]: item[1] for item in religion}
        elif second_item[1] > 1.5 * third_item[1] and second_item[1] > 0.2:
            religion = first_item, second_item
            self.religion = {item[0]: item[1] for item in religion}
        elif fourth_item[1] > 0.2:
            self.religion = sorted_religion
             
    def get_the_most_interesting_categories(self):
        self.sorted_preferences = sorted(self.main_preferences.items(), key=lambda x: x[1], reverse=True)
        if(self.available_days.count == 2):
            if("nightlife" in key for key,value in self.sorted_preferences[:3]):
                self.main_preferences = dict(self.sorted_preferences[:4])
            else:
                self.main_preferences = dict(self.sorted_preferences[:3])
        elif(self.available_days.count == 3):
            self.main_preferences = dict(self.sorted_preferences[:4])
        elif(self.available_days.count == 4):
            self.main_preferences = dict(self.sorted_preferences[:5])
        elif(self.available_days.count == 5 or self.available_days.count == 6):
            self.main_preferences = dict(self.sorted_preferences[:6])
        else:
            self.main_preferences = self.sorted_preferences
            
    def get_prob_sum(self):
        prob_sum = 0
        for key,value in self.main_preferences:
            prob_sum += value
        return prob_sum
    
    def get_sorted_cat_list(self):
        for key,value in self.main_preferences:
            for cat in categories_list:
                if(key == cat.name):
                    self.sorted_categories.append(cat)
    
    def get_number_of_places_from_each_category_to_see(self):
        available_hours_numbers = []
        number_of_places_to_see = []
        num_of_places = 0
        for key,value in self.main_preferences:
            for cat in categories_list:
                if(cat.ignore == False):
                    if(key == cat.name):
                        hours_num = 0
                        for day in self.available_days:
                            overlap_start = max(cat.start_time, day.start_hour)
                            overlap_end = min(cat.end_time, day.end_hour)
                            hours_num += (overlap_end-overlap_start)
                            
                        available_hours_numbers.append(hours_num)
                        number_of_places_to_see.append(hours_num/cat.duration)
                    
        num_of_places = (sum(number_of_places_to_see) / len(self.main_preferences)) 
        prob_sum = self.get_prob_sum()

        for key,value in self.main_preferences:
            #print((value/prob_sum) * num_of_places)
            self.num_of_places_for_main_categories.append(math.ceil(value/prob_sum * num_of_places))
            
            
    def get_number_of_places_to_be_found(self):
        for num in self.num_of_places_for_main_categories:
            self.num_of_places_for_main_categories_for_search.append(math.ceil(1.8 * num))
    
    def prepare_city_coordinates(self):
        endpoint = 'https://maps.googleapis.com/maps/api/geocode/json'
        response = requests.get(endpoint, params={'address': self.destination, 'key': gmaps_key})
        json_response = response.json()
        self.lat = json_response['results'][0]['geometry']['location']['lat']
        self.lng = json_response['results'][0]['geometry']['location']['lng']
    
    def prepare_search_radius(self):
        if self.bicycle_travel_accept is False and self.public_transport_accept is False and self.car_travel_accept is False:
            self.radius = 4000
        if self.public_transport_accept is True :
            self.radius = 8000
        if self.bicycle_travel_accept is True:
            self.radius = 14000
        if self.car_travel_accept is True:
            self.radius = 25000
    
    def prepare_found_places_lists(self):
        i = 0
        for cat in self.sorted_categories:
            curr_cat_places_list = []
            for tp in cat.categories_list:
                #searching req has to be changed, because parameter cost_rate is not correctly handle by GM Api
                search_req_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={self.lat}%2C{self.lng}&radius={self.radius}&type={tp}&key={gmaps_key}"
                payload={}
                headers = {}
                response = requests.request("GET", search_req_url, headers=headers, data=payload)
                json_response = response.json()
                results = json_response['results'][:3]
   
                temp_res = []
                avoid = ["Bank", "Bankomat", "Apartamenty", "Apartments", "Hotel", "House", "internetowe", "Med"]
                for res in results:
                    if not any(pl in res['name'] for pl in avoid):
                        temp_res.append(res)
                        
                curr_cat_places_list += temp_res

            if(len(curr_cat_places_list) < self.num_of_places_for_main_categories[i]):
                temp = self.num_of_places_for_main_categories[i]
                self.num_of_places_for_main_categories[i] = len(curr_cat_places_list)
                if(len(self.sorted_categories) > i+1):
                    self.num_of_places_for_main_categories[i+1] += (temp - len(curr_cat_places_list))
                    self.num_of_places_for_main_categories_for_search[i+1] += (temp - len(curr_cat_places_list))
                else:
                    cat_to_be_added = self.sorted_preferences[i+1][0]
                    for cat in categories_list:
                        if(cat.name == cat_to_be_added):
                            self.sorted_categories.append(cat)
                            self.num_of_places_for_main_categories.append(self.num_of_places_for_main_categories[i] - len(curr_cat_places_list))
                            self.num_of_places_for_main_categories_for_search.append(math.ceil((self.num_of_places_for_main_categories[i] - len(curr_cat_places_list))*1.8))
            i += 1
            
            curr_cat_places_list_without_duplicates = []
            [curr_cat_places_list_without_duplicates.append(x) for x in curr_cat_places_list if x not in curr_cat_places_list_without_duplicates]
            self.found_places_lists.append(curr_cat_places_list_without_duplicates)
        
        curr_found_places_list_without_duplicates = []
        [curr_found_places_list_without_duplicates.append(x) for x in self.found_places_lists if x not in curr_found_places_list_without_duplicates]
        
        self.found_places_lists = curr_found_places_list_without_duplicates
        
            #print(f"curr cat places list len {len(curr_cat_places_list)}")
            
            
    #take appropriate number of places from each category (at least expected number if search number is not possible) and then clusterize itd.
    def reduce_places_number(self):
        for i in range(len(self.found_places_lists)):
            for j in range(len(self.found_places_lists[i]) - self.num_of_places_for_main_categories[i]):
                if(len(self.found_places_lists[i])>1):
                    el_to_drop_idx = random.randrange(len(self.found_places_lists[i]))
                    taken_place = self.found_places_lists[i][el_to_drop_idx]
                    pl = Place(taken_place["place_id"], taken_place["name"])
                    self.substitutes_places.append(pl) 
                    self.substitutes_places_names.append(taken_place["name"]) #get_place_name() get_place_coordinates()
                    self.found_places_lists[i].pop(el_to_drop_idx) 
                
                
        temp = []
        for lst in self.found_places_lists:
            for el in lst:
                if el not in temp:
                    temp.append(el)    
        self.found_places_lists = temp
            
    def count_available_hours_num(self):
        sum = 0
        for day in self.available_days:
            sum += (day.end_hour - day.start_hour)
        self.available_hours = sum
        
    def count_total_num_places_to_see(self):
        self.total_num_places_to_see = len(self.found_places_lists)
    
    def set_num_of_places_for_each_day(self):
        for day in self.available_days:
            day.set_num_places_to_see(self.available_hours, self.total_num_places_to_see)
        
    def clusterization(self):
        print("Does not work currently")
        #sklearn.cluster.AgglomerativeClustering()
        
    def temporary_places_grouping(self):
        for day in self.available_days:
            for i in range(day.num_places_to_see):
                if(len(self.found_places_lists)>1):
                    random_place = self.found_places_lists.pop(random.randrange(len(self.found_places_lists)))
                    day.add_place((random_place["place_id"]), (random_place["name"]))
                elif (len(self.found_places_lists)==1):
                    day.add_place(((self.found_places_lists[0])["place_id"]), ((self.found_places_lists[0])["name"]))
                    
            day.set_travel_mode(self.transport_mode)
            self.lists_of_places_for_each_day.append(day.get_places_names_list())
            
    def prepare_transport_mode(self):
        if self.car_travel_accept:
            self.transport_mode = 'driving'
        elif self.public_transport_accept:
            self.transport_mode = 'transit'
        elif self.bicycle_travel_accept:
            self.transport_mode = 'bicycling'
        else:
            self.transport_mode = 'walking'
            
    def show_map_for_each_day(self):
        for day in self.available_days:
            url, layer = day.prepare_maps_and_links(self.transport_mode, [self.lat, self.lng])
            self.layers.append(layer) #get_googlemaps_layers
            self.urls.append(url) #get_googlemaps_link
            
    def show_other_interesting_places(self):
        print('\n')
        print("Other places, which can be interesting for you:")
        for pl in self.substitutes_places:
            print(f"{pl.name}, współrzędne: {pl.coordinates}")
            
   
class CityDay:
    def __init__(self, start_hour:int, end_hour:int):
        self.start_hour = start_hour
        self.end_hour = end_hour
        self.places_list = []
        self.layer = None
        self.url = None
        self.places_names_list = []
    
    #To be changed
    def set_num_places_to_see(self, available_hours: int, num_of_places: int):
        self.num_places_to_see = round((self.end_hour - self.start_hour) / available_hours * num_of_places)
        
    def add_place(self, place_id, place_name):
        self.places_list.append(Place(place_id, place_name))
        
        
    def prepare_lists_places_places_ids(self):
        self.list_of_places = []
        self.list_of_places_ids = []
        
        for pl in self.places_list:
            self.list_of_places.append(pl.place_name)
            self.list_of_places_ids.append(pl.place_id)
            
    def set_travel_mode(self, travel_mode):
        self.travel_mode = travel_mode
        
    def prepare_maps_and_links(self, transport_mode, city_coordinates):
        places_num = len(self.places_list)
        if(places_num == 1):
            start_coordinates = (self.places_list[0].coordinates)
            self.layer = gmaps.directions.Directions(center = city_coordinates)
        elif(places_num == 2):
            start_coordinates = (self.places_list[0].coordinates)
            finish_coordinates = (self.places_list[-1].coordinates)
            self.layer = gmaps.directions.Directions(start_coordinates, finish_coordinates,mode=transport_mode, center = city_coordinates)
        elif(places_num > 2):
            waypoints = []
            start_coordinates = (self.places_list[0].coordinates)
            finish_coordinates = (self.places_list[-1].coordinates)
            for i, place in enumerate(self.places_list):
                if 0 < i < places_num:
                    waypoints.append(place.coordinates)
            self.layer = gmaps.directions.Directions(start_coordinates, finish_coordinates, waypoints=waypoints,mode=transport_mode, center = city_coordinates, optimize_waypoints = True)
            
        if(places_num > 0):
            fig = gmaps.figure()
            fig.add_layer(self.layer)
            display.display(fig)
            
            print("For this day we prepare for you such a places to see:")
            for pl in self.places_list:
                print(pl.name)
                self.places_names_list.append(pl.name)
            
            print("\n")
            print("Here is link to google maps for your daily trip:")
            self.prepare_lists_places_places_ids()
            self.url = self.generate_google_maps_url(self.list_of_places, self.list_of_places_ids, self.travel_mode)
            
        return self.url, self.layer
    
    def generate_google_maps_url(self, places, places_ids, travel_mode):
        base_url = "https://www.google.com/maps/dir/?api=1"
        travel_mode_part = "travelmode".join(f"{travel_mode}")
        
        temp_pl = []
        for pl in places:
            temp_pl.append(pl.replace(" ", ""))
        places = temp_pl
        
        origin = f"origin={places[0]}"
        origin_place_id = f"origin_place_id={places_ids[0]}"
        destination = f"destination={places[-1]}"
        destination_place_id = f"destination_place_id={places_ids[len(places_ids) - 1]}"
        
        if(len(places) > 2):
            waypoints = "waypoints="
            waypoints_ids = "waypoint_place_ids="
            
            waypoints_list = []
            waypoints_ids_list = []
            
            for i in range(1, len(places) - 1):
                if(i == 1):
                    waypoints_list.append(f"{places[1]}")
                    waypoints_ids_list.append(f"{places_ids[1]}")
                    
                elif(i > 1 and i < len(places) - 1):
                    waypoints_list.append(f"{places[i]}")
                    waypoints_ids_list.append(f"{places_ids[i]}")

            waypoints = waypoints + "%7C".join(waypoints_list)
            waypoints_ids = waypoints_ids + "%7C".join(waypoints_ids_list)

            int_url = "&" + origin + "&" + origin_place_id + "&" + destination + "&" + destination_place_id + "&" + waypoints + "&" + waypoints_ids
        else:
            int_url = "&" + origin + "&" + origin_place_id + "&" + destination + "&" + destination_place_id
            
        self.url = base_url + int_url + "&" + travel_mode_part
        print(self.url)
        return self.url
    
    def get_places_names_list(self):
        return self.places_names_list
    
    def get_googlemaps_link(self):
        return self.url
        
    def get_googlemaps_layer(self):
        return self.layer
    
class Place:
    def __init__(self, place_id, place_name):
        self.place_id = place_id
        self.place_name = place_name
        self.prepare_place_name_and_coordinates()
        
    def prepare_place_name_and_coordinates(self):
        url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={self.place_id}&Atmosphere=reviews&key={gmaps_key}"
        payload={}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        json_response = response.json()
        self.name = json_response['result']['name']
        coordinates = json_response['result']['geometry']['location']
        self.coordinates = (coordinates['lat'], coordinates['lng'])
        
    def get_place_name(self):
        return str(self.place_name)
    
    def get_place_coordinates(self):
        return str(self.coordinates)