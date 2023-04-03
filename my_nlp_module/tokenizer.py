import numpy as np
from collections import Counter


class Tokenizer:
    def __init__(self, max_words):
        
        self.max_words = max_words
        self.vocab = {}
    
    def fit(self, documents):
        list_of_words = []
        for doc in documents:
            for word in doc.split():
                list_of_words.append(word)
        
        most_common = Counter(list_of_words).most_common(self.max_words)
        for i, el in enumerate(most_common):
            self.vocab[el[0]] = i+1
            
    def texts_to_sequences(self, documents):
        result = []
        for doc in documents:
            doc_res = []
            for word in doc.split():
                if word in self.vocab.keys():
                    doc_res.append(self.vocab[word])
            result.append(doc_res)
        return result
