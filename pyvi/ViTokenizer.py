import sys
import os
import codecs
import pickle
import re
import string
import unicodedata as ud

class ViTokenizer:
    bi_grams = set()
    tri_grams = set()
    model_file = 'models/pyvi.pkl'
    if sys.version_info[0] == 3:
        model_file = 'models/pyvi3.pkl'

    with codecs.open(os.path.join(os.path.dirname(__file__), 'models/words.txt'), 'r', encoding='utf-8') as fin:
        for token in fin.read().split('\n'):
            tmp = token.split(' ')
            if len(tmp) == 2:
                bi_grams.add(token)
            elif len(tmp) == 3:
                tri_grams.add(token)
    with open(os.path.join(os.path.dirname(__file__), model_file), 'rb') as fin:
        model = pickle.load(fin)

    @staticmethod
    def word2features(sent, i, is_training):
        word = sent[i][0] if is_training else sent[i]

        features = {
            'bias': 1.0,
            'word.lower()': word.lower(),
            #   'word[-3:]': word[-3:],
            #   'word[-2:]': word[-2:],
            'word.isupper()': word.isupper(),
            'word.istitle()': word.istitle(),
            'word.isdigit()': word.isdigit(),
        }
        if i > 0:
            word1 = sent[i - 1][0] if is_training else sent[i - 1]
            features.update({
                '-1:word.lower()': word1.lower(),
                '-1:word.istitle()': word1.istitle(),
                '-1:word.isupper()': word1.isupper(),
                '-1:word.bi_gram()': ' '.join([word1, word]).lower() in ViTokenizer.bi_grams,
            })
            if i > 1:
                word2 = sent[i - 2][0] if is_training else sent[i - 2]
                features.update({
                    '-2:word.tri_gram()': ' '.join([word2, word1, word]).lower() in ViTokenizer.tri_grams,
                })
                #    else:
                #        features['BOS'] = True

        if i < len(sent) - 1:
            word1 = sent[i + 1][0] if is_training else sent[i + 1]
            features.update({
                '+1:word.lower()': word1.lower(),
                '+1:word.istitle()': word1.istitle(),
                '+1:word.isupper()': word1.isupper(),
                '+1:word.bi_gram()': ' '.join([word, word1]).lower() in ViTokenizer.bi_grams,
            })
            if i < len(sent) - 2:
                word2 = sent[i + 2][0] if is_training else sent[i + 2]
                features.update({
                    '+2:word.tri_gram()': ' '.join([word, word1, word2]).lower() in ViTokenizer.tri_grams,
                })
                #    else:
                #        features['EOS'] = True

        return features

    @staticmethod
    def sent2features(sent, is_training):
        return [ViTokenizer.word2features(sent, i, is_training) for i in range(len(sent))]

    @staticmethod
    def sylabelize(text):
        text = ud.normalize('NFC', text)
        #tmp = re.findall(r"((\d+[\.,-_]*\d*)+|\w+|[^\w\s])", text, re.UNICODE)
        #tmp = re.findall(r"((\d+([\.,-_]\d+)*)+|\w+|[^\w\s])", text, re.UNICODE)
        #tmp = re.findall(r"((\d+([\.,-_]\d+)*)+|\w[\w-]*(\'*\w)*|[^\w\s])", text, re.UNICODE)
        tmp = re.findall(r"((\d+([\.,-_]\d+)*)+|\w['\.\w-]*\w+|\w+|[^\w\s])", text, re.UNICODE)
        return [a[0] for a in tmp]

    @staticmethod
    def tokenize(str):
        tmp = ViTokenizer.sylabelize(str)
        if len(tmp) == 0:
            return str
        labels = ViTokenizer.model.predict([ViTokenizer.sent2features(tmp, False)])
        output = tmp[0]
        for i in range(1, len(labels[0])):
            if labels[0][i] == 'I_W' and tmp[i] not in string.punctuation and\
                            tmp[i-1] not in string.punctuation and\
                    not tmp[i][0].isdigit() and not tmp[i-1][0].isdigit()\
                    and not (tmp[i][0].istitle() and not tmp[i-1][0].istitle()):
                output = output + '_' + tmp[i]
            else:
                output = output + ' ' + tmp[i]
        return output

    @staticmethod
    def spacy_tokenize(str):
        tmp = ViTokenizer.sylabelize(str)
        if len(tmp) == 0:
            return str
        labels = ViTokenizer.model.predict([ViTokenizer.sent2features(tmp, False)])
        token = tmp[0]
        tokens = []
        for i in range(1, len(labels[0])):
            if labels[0][i] == 'I_W' and tmp[i] not in string.punctuation and\
                            tmp[i-1] not in string.punctuation and\
                    not tmp[i][0].isdigit() and not tmp[i-1][0].isdigit()\
                    and not (tmp[i][0].istitle() and not tmp[i-1][0].istitle()):
                token = token + '_' + tmp[i]
            else:
                tokens.append(token)
                token = tmp[i]
        tokens.append(token)
        return tokens, [True]*len(tokens)


def spacy_tokenize(str):
    return ViTokenizer.spacy_tokenize(str)


def tokenize(str):
    return ViTokenizer.tokenize(str)
