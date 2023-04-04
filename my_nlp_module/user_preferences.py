#!/usr/bin/python
# -*- coding: utf-8 -*-
from typing import List, Dict
from my_nlp_module.similarities_calculation import SimilaritiesCalculation


class UserPreferences:
    def __init__(self, templates: Dict[str, str], calculation: SimilaritiesCalculation, texts: List[str] = None):
        self.__categories_similarities = {}
        if texts is None:
            self.__texts = []
        for category in templates.keys():
            self.__categories_similarities[category] = 0.0
        self.__calculation = calculation
        self.__templates = templates

    def get_texts(self):
        return self.__texts

    def set_texts(self, texts: List[str]):
        self.__texts = texts

    def add_text(self, text: str):
        self.__texts.append(text)

    def calculate_preferences(self):
        similarities = self.__calculation.calculate_similarities(self.__texts, self.__templates)
        self.__categories_similarities = similarities
        return similarities

    def get_preferences(self):
        return self.__categories_similarities

