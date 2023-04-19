#!/usr/bin/python
# -*- coding: utf-8 -*-
from my_nlp_module.preprocessing import PrepOption, preprocess_document
from typing import List, Dict
import abc
from copy import copy
from sentence_transformers import SentenceTransformer, util
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import defaultdict


class SimilaritiesCalculation:
    def __init__(self, preprocessing_options: List[PrepOption]):
        self.__sentiment_analyzer = SentimentIntensityAnalyzer()
        self.__preprocessing_options = preprocessing_options
        if PrepOption.TOKENIZE_SENTENCE in self.__preprocessing_options:
            self.__preprocessing_options.remove(PrepOption.TOKENIZE_SENTENCE)

    @abc.abstractmethod
    def calculate_similarities(self, texts: List[str], templates: Dict[str, str]):
        pass


class SentenceTransformerSimilarity(SimilaritiesCalculation):
    def __init__(self, model: SentenceTransformer, preprocessing_options: List[PrepOption]):
        super().__init__(preprocessing_options=preprocessing_options)
        self.__model = model
        self.__sentiment_analyzer = SentimentIntensityAnalyzer()
        self.__preprocessing_options = preprocessing_options
        if PrepOption.TOKENIZE_SENTENCE in self.__preprocessing_options:
            self.__preprocessing_options.remove(PrepOption.TOKENIZE_SENTENCE)

    def calculate_similarities(self, texts: List[str], templates: Dict[str, str]) -> Dict[str, float]:
        result: Dict[str, float] = {}
        for k in templates.keys():
            result[k] = 0.0
        texts = copy(texts)
        documents_lengths: Dict[int, List[Dict]] = {}

        for text in texts:
            sentences = preprocess_document(text, [PrepOption.TOKENIZE_SENTENCE])
            partial_similarity = self.__partial_similarity(sentences, templates)
            doc_length = len(sentences)
            if doc_length in documents_lengths:
                documents_lengths[doc_length].append(partial_similarity)
            else:
                documents_lengths[doc_length] = [partial_similarity]

        all_document_length = list(documents_lengths.keys())
        for doc_len in all_document_length:
            average_sim_for_len = defaultdict(float)
            normalization: Dict[str, int] = defaultdict(int)
            for partial_similarity in documents_lengths[doc_len]:
                for k in templates.keys():
                    average_sim_for_len[k] += partial_similarity[k]
                    normalization[k] += 1 if partial_similarity[k] > 0 else 0
            for k in templates.keys():
                if normalization[k] > 0:
                    average_sim_for_len[k] /= normalization[k]
                result[k] += (doc_len/sum(all_document_length))*average_sim_for_len[k]

        return result

    def __partial_similarity(self, document: List[str], templates: Dict[str, str]) -> Dict[str, float]:
        categories = list(templates.keys())
        number_of_categories = len(categories)
        document_similarity = np.zeros(shape=number_of_categories)
        normalization = [0 for _ in range(number_of_categories)]
        template_strings = []
        for cat in categories:
            template_strings.append(templates[cat])

        embeddings_templates = self.__model.encode(template_strings, convert_to_tensor=True)
        for sentence in document:
            sentiment = self.__sentiment_analyzer.polarity_scores(sentence)
            sentence = preprocess_document(sentence, self.__preprocessing_options)
            embedding_sentence = self.__model.encode(sentence, convert_to_tensor=True)
            sim = util.cos_sim(embedding_sentence, embeddings_templates).numpy().squeeze()
            for i in range(sim.shape[0]):
                sim[i] = sim[i] if np.abs(sim[i]) > 0.2 else 0
            norm_idx = np.where(sim != 0)[0]
            for i in norm_idx:
                normalization[i] += 1
            if sentiment["neg"] < 0.5:
                sim = sim * (1 - sentiment["neg"])
            else:
                sim = sim * (-sentiment["neg"])
            document_similarity += sim

        for i, el in enumerate(normalization):
            if el > 0:
                document_similarity[i] /= el

        return {category: document_similarity[i] for i, category in enumerate(categories)}
