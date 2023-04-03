# projekt-studio-projektowe1

W celu poprawnego uruchomienia kodu naley mieć zainstalowany interpreter języka `Python 3.8.0`.
Następnie należy zainstalować wszystkie wymagane biblioteki z pliku `requirements.txt` używając następującej komendy:

```
pip install -r requirements.txt
```

Następnie należy zainstalować kilka dodatków z biblioteki `nltk`. W celu można uruchomić interaktywny intrpreter języka Python oraz wykonać następujący kod:

```
import nltk
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('punkt')
```

Niektóre notebooki wymagają pobrania wcześniej wytrenowanych modeli. Można je pobrać ze strony http://vectors.nlpl.eu/repository/.
- ID: `40`
- Corpus: `English CoNLL17 corpus`
- Vector size: `100`

Archiwum `.zip` należy rozpakować w folderze `pretrained_models` katalogu roboczego.
