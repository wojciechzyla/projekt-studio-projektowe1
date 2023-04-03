from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
import re
from enum import Enum
from typing import List


class PrepOption(Enum):
    LOWERCASE = 1
    STOPWORDS = 2
    STEM = 3
    INTERPUNCTION = 4
    TOKENIZE_WORDS = 5
    RUBBISH = 6
    NUMBERS = 7
    TOKENIZE_SENTENCE = 8
    LEMMA = 9


def preprocess_document(document: str, options: List[PrepOption], stopwords_list: List[str] = None, stemmer=None):
    stop = stopwords.words("english")
    stemmer = PorterStemmer()
    lemmatizer = WordNetLemmatizer()
    sentences_preprocessed = []
    if PrepOption.TOKENIZE_SENTENCE in options:
        sentences = sent_tokenize(document, "english")
    else:
        sentences = [document]

    for sent in sentences:
        if PrepOption.INTERPUNCTION in options:
            sent = re.sub(r"[^-\w\s]", " ", sent)
            sent = re.sub(r"-", " ", sent)
        if PrepOption.LOWERCASE in options:
            sent = " ".join([word.lower() for word in sent.split()])
        if PrepOption.LEMMA in options:
            sent = " ".join([lemmatizer.lemmatize(word) for word in sent.split()])
        elif PrepOption.STEM in options:
            words_stemmed = []
            for word in sent.split():
                stemmed = stemmer.stem(word)
                stemmed = stemmed if stemmed is not None else ""
                words_stemmed.append(stemmed)
            sent = " ".join(words_stemmed)
        if PrepOption.RUBBISH in options:
            sent = re.sub(r"[^a-zA-Z0-9.,?!AaĄąBbCcĆćDdEeĘęFfGgHhIiJjKkLlŁłMmNnŃńOoÓóPpRrSsŚśTtUuWwYyZzŹźŻż\s]", " ", sent)
            sent = re.sub(r"\w*[0-9]+\w*", " ", sent)
        if PrepOption.NUMBERS in options:
            sent = re.sub(r"[0-9]", " ", sent)
        if PrepOption.STOPWORDS in options:
            sent = " ".join([word for word in sent.split() if word not in stop])
        sent = re.sub(r"\s{2,}", " ", sent)
        if PrepOption.TOKENIZE_WORDS in options:
            sent = word_tokenize(sent, "english")
        sentences_preprocessed.append(sent)

    if PrepOption.TOKENIZE_SENTENCE in options:
        result = sentences_preprocessed
    else:
        result = sentences_preprocessed[0]
    return result
