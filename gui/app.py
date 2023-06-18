#!/usr/bin/python
# -*- coding: utf-8 -*-
import tkinter
import customtkinter
from tkinter import filedialog
from tkcalendar import Calendar
from datetime import datetime
from my_nlp_module.user_handler import TravelWith
import os
import sys
module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)
from my_nlp_module.user_preferences import UserPreferences
from my_nlp_module.similarities_calculation import SentenceTransformerSimilarity
from sentence_transformers import SentenceTransformer
import json

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")


class MyFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.dir_path = ""
        self.start_date = (2023, 1, 1, 0)
        self.end_date = (2023, 1, 1, 0)
        self.public_transport_accept = False
        self.bicycle_travel_accept = False
        self.car_travel_accept = False
        self.cost_rate = 4.0
        self.travel_with = TravelWith.alone

        # Text files
        self.texts_folder = customtkinter.CTkLabel(self,
                                                   text="Choose folder with txt files describing your travel ideas:")
        self.texts_folder.pack(padx=10)
        self.texts_button = customtkinter.CTkButton(self, text="Folder", command=self.get_directory)
        self.texts_button.pack(padx=10)
        self.chosen_dir = customtkinter.CTkLabel(self, text=f"Chosen folder: {self.dir_path}")
        self.chosen_dir.pack()

        # Destination
        self.destination_label = customtkinter.CTkLabel(self, text="Provide name of your destination:")
        self.destination_label.pack()
        self.city = tkinter.StringVar()
        self.destination_input = customtkinter.CTkEntry(self, placeholder_text="City name", textvariable=self.city)
        self.destination_input.pack()

        # Start date
        self.start_date_label = customtkinter.CTkLabel(self, text=f"Selected start day:")
        self.start_date_label.pack()
        self.start_calendar = Calendar(self, selectmode='day', year=2023, month=1, day=1)
        self.start_calendar.pack()
        self.start_date_button = customtkinter.CTkButton(self, text="Save date", command=self.get_start_date)
        self.start_date_button.pack()

        # End date
        self.end_date_label = customtkinter.CTkLabel(self, text=f"Selected end day:")
        self.end_date_label.pack()
        self.end_calendar = Calendar(self, selectmode='day', year=2023, month=1, day=1)
        self.end_calendar.pack()
        self.end_date_button = customtkinter.CTkButton(self, text="Save date", command=self.get_end_date)
        self.end_date_button.pack()

        # Public transport
        self.public_transport_label = customtkinter.CTkLabel(self, text="Do you want to use a public transport?")
        self.public_transport_label.pack()
        self.public_transport_input = customtkinter.CTkOptionMenu(self, values=["Yes", "No"],
                                                                  command=self.use_public_transport)
        self.public_transport_input.set("No")
        self.public_transport_input.pack()

        # Bicycle transport
        self.bicycle_label = customtkinter.CTkLabel(self, text="Do you want to use a bicycle?")
        self.bicycle_label.pack()
        self.bicycle_input = customtkinter.CTkOptionMenu(self, values=["Yes", "No"],
                                                                  command=self.use_bicycle)
        self.bicycle_input.set("No")
        self.bicycle_input.pack()

        # Car transport
        self.car_label = customtkinter.CTkLabel(self, text="Do you want to use a car?")
        self.car_label.pack()
        self.car_input = customtkinter.CTkOptionMenu(self, values=["Yes", "No"],
                                                         command=self.use_car)
        self.car_input.set("No")
        self.car_input.pack()

        # Cost rate
        self.cost_rate_label = customtkinter.CTkLabel(self, text="Choose your cost rate: ")
        self.cost_rate_label.pack()
        self.cost_rate_slider = customtkinter.CTkSlider(self, from_=0, to=4, number_of_steps=50,
                                                        command=self.set_cost_rate)
        self.cost_rate_slider.pack()


        # Calculate
        self.summary_button = customtkinter.CTkButton(self, text="Create your travel plan", command=self.find_travel_plan)
        self.summary_button.pack()

    def find_travel_plan(self):
        model = SentenceTransformer('all-MiniLM-L6-v2')
        templates = {}
        with open("../json/templates.json") as f:
            templates = json.load(f)

        calculations = SentenceTransformerSimilarity(model, [])

        user = UserPreferences(templates=templates, calculation=calculations)
        files = os.listdir(self.dir_path)
        for file_name in files:
            file_path = self.dir_path + f"/{file_name}"
            inp = ""
            with open(file_path) as f:
                inp = f.read()
            user.add_text(inp)
        user.calculate_preferences()
        print(user.get_preferences())
        print(self.start_date)
        print(self.end_date)
        print(self.public_transport_accept)
        print(self.bicycle_travel_accept)
        print(self.car_travel_accept)
        print(self.cost_rate)


    def get_directory(self):
        self.dir_path = filedialog.askdirectory()
        self.chosen_dir.configure(text=f"Chosen folder: {self.dir_path}")

    def get_start_date(self):
        self.start_date_label.configure(text=f"Selected start day: {self.start_calendar.get_date()}")
        date_split = self.start_calendar.get_date().split("/")
        day = int(date_split[0])
        month = int(date_split[1])
        year = int(date_split[2])
        self.start_date = datetime(year, month, day, 0)

    def get_end_date(self):
        self.end_date_label.configure(text=f"Selected end day: {self.end_calendar.get_date()}")
        date_split = self.end_calendar.get_date().split("/")
        day = int(date_split[0])
        month = int(date_split[1])
        year = int(date_split[2])
        self.end_date = datetime(year, month, day, 0)

    def use_public_transport(self, option):
        if option == "Yes":
            self.public_transport_accept = True
        else:
            self.public_transport_accept = False

    def use_bicycle(self, option):
        if option == "Yes":
            self.bicycle_travel_accept = True
        else:
            self.bicycle_travel_accept = False

    def use_car(self, option):
        if option == "Yes":
            self.car_travel_accept = True
        else:
            self.car_travel_accept = False

    def set_cost_rate(self, value):
        self.cost_rate = round(float(value), 2)
        self.cost_rate_label.configure(text=f"Choose your cost rate: {self.cost_rate}")



class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("720x480")
        self.title("Travel agency")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.my_frame = MyFrame(master=self, width=300, height=200, corner_radius=0, fg_color="transparent")
        self.my_frame.grid(row=0, column=0, sticky="nsew")



app = App()
app.mainloop()