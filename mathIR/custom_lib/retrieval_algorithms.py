"""
Collection of retrieval algorithms

retrieval_algorithms.py
@author Aaron Smith, Grant Larsen
11/26/2019
"""
import math
import os
import csv
from .utils import get_index, get_docs_index, format_text
from sklearn import svm

# -----
# BM25 parameters
# -----
K_1 = 1.2
K_2 = 100.0
B = 0.75
R = 0
R_i = 0

TRAINING_DATA_FILE_NAME = 'training_data.tsv'
WEIGHT_VECTOR_FILE_NAME = 'svm_weights.tsv'


def main():
    doc_index = get_docs_index()
    index = get_index()
    anchor_index = get_index(anchor=True)
    train_svm(doc_index, index, anchor_index)


# ---------------------------------------------------------------------------------
# wrapper function to be called to get the related documents
#
# @input: terms: list of given query terms
#         index: dictionary with document word frequencies
#         doc_index: index with word, and line counts
#         query_model: string to specify retrieval algorithm to use
# @return: list of documents(some variation based on algorithm)
# ---------------------------------------------------------------------------------
def query(terms, index, doc_index, anchor_index, svm_model, query_model, **kwargs):
    if query_model == 'bm25':
        return query_bm25(terms, index, doc_index, **kwargs)
    else:
        return query_svm(terms, index, doc_index, anchor_index, svm_model)


def query_bm25_mod(terms, index, doc_index, **kwargs):
    term_counts = {}
    for term in terms:
        if term in term_counts:
            term_counts[term] += 1
        else:
            term_counts[term] = 1

    avg_dl = 0.0
    doc_scores = {}
    for doc in doc_index:
        avg_dl += float(doc_index[doc]['words'])

    avg_dl /= len(doc_index)
    n = len(doc_index)

    doc_k = {}
    for doc in doc_index:
        doc_k[doc] = K_1 * ((1 - B) + B * (float(doc_index[doc]['words']) / avg_dl))

    for term in term_counts:
        try:
            index_entry = index[term]
            n_i = float(index_entry['count'])
        except KeyError:
            continue
        term_weight = math.log(((R_i + 0.5) / (R - R_i + 0.5)) / ((n_i - R_i + 0.5) / (n - n_i - R + R_i + 0.5)), 10)
        if term_weight < -0.25:
            term_weight = -0.25
        query_term_weight = ((K_2 + 1) * term_counts[term]) / (K_2 + term_counts[term])

        try:
            for doc, f_i in index[term]['docs'].items():
                k = doc_k[doc]
                doc_weight = (K_1 + 1) * f_i / (k + f_i)

                if doc not in doc_scores:
                    doc_scores[doc] = 0.0
                doc_scores[doc] += term_weight * doc_weight * query_term_weight

        except KeyError:
            continue
    doc_scores = [(doc, doc_index[doc]['name'], doc_scores[doc]) for doc in doc_scores]
    if 'limit_to' in kwargs:
        limited_scores = []
        for doc in doc_scores:
            if doc[0] in kwargs['limit_to']:
                limited_scores.append(doc)
        doc_scores = limited_scores
    doc_scores = sorted(doc_scores, key=lambda tup: tup[2], reverse=True)
    return doc_scores


# ---------------------------------------------------------------------------------
# get list of documents using BM25 to rank
#
# @input: terms: list of given query terms
#         index: dictionary with document word frequencies
#         doc_index: dictionary for word and line count
# @return: doc_scores: list tuples(documents,score)
# ---------------------------------------------------------------------------------
def query_bm25(terms, index, doc_index, **kwargs):
    term_counts = {}
    for term in terms:
        if term in term_counts:
            term_counts[term] += 1
        else:
            term_counts[term] = 1

    avg_dl = 0.0
    doc_scores = {}
    for doc in doc_index:
        avg_dl += float(doc_index[doc]['words'])

    avg_dl /= len(doc_index)
    n = len(doc_index)

    doc_k = {}
    for doc in doc_index:
        doc_k[doc] = K_1*((1 - B) + B * (float(doc_index[doc]['words'])/avg_dl))

    for term in term_counts:
        try:
            index_entry = index[term]
            n_i = float(index_entry['count'])
        except KeyError:
            continue
        term_weight = math.log(((R_i + 0.5)/(R - R_i + 0.5))/((n_i - R_i + 0.5)/(n - n_i - R + R_i + 0.5)), 10)
        if term_weight < -0.25:
            term_weight = -0.25
        query_term_weight = ((K_2 + 1)*term_counts[term])/(K_2 + term_counts[term])

        try:
            for doc, f_i in index[term]['docs'].items():
                k = doc_k[doc]
                doc_weight = (K_1 + 1)*f_i/(k + f_i)

                if doc not in doc_scores:
                    doc_scores[doc] = 0.0
                doc_scores[doc] += term_weight*doc_weight*query_term_weight

        except KeyError:
            continue
    doc_scores = [(doc, doc_index[doc]['name'], doc_scores[doc]) for doc in doc_scores]
    if 'limit_to' in kwargs:
        limited_scores = []
        for doc in doc_scores:
            if doc[0] in kwargs['limit_to']:
                limited_scores.append(doc)
        doc_scores = limited_scores
    doc_scores = sorted(doc_scores, key=lambda tup: tup[2], reverse=True)
    return doc_scores


def query_svm(terms, index, doc_index, anchor_index, svm_weights):
    doc_ids = list(doc_index.keys())
    features = get_features(terms, doc_ids, doc_index, index, anchor_index)
    doc_scores = score_docs(doc_ids, doc_index, features, svm_weights)
    doc_scores = sorted(doc_scores, key=lambda tup: tup[2], reverse=True)
    return doc_scores


def score_docs(doc_ids, doc_index, features, svm_weights):
    scores = []
    for doc in range(0, len(doc_ids)):
        doc_id = doc_ids[doc]
        scores.append((doc_id, doc_index[doc_id]['name'], sum(x_i*y_i for x_i, y_i in zip(features[doc], svm_weights))))
    return scores


def make_training_data_file():
    dirs = [x[0] for x in os.walk('rel_data')]
    training_data_lines = []
    for dir in dirs[1:]:
        with open(os.path.join(dir, 'queries.txt'), 'r', encoding='utf-8') as query_file:
            for q_count in range(1, 6):
                terms = query_file.readline().strip().lower()
                fn = 'q%d.qrel' % q_count
                with open(os.path.join(dir, fn), 'r', encoding='utf-8') as qrel:
                    for qrel_line in qrel:
                        qrel_line = qrel_line
                        print(qrel_line)
                        if '\t' in qrel_line:
                            rels = qrel_line.split('\t')
                        else:
                            rels = qrel_line.split()
                        line = [terms, rels[-2], rels[-1]]
                        training_data_lines.append(line)

    with open(TRAINING_DATA_FILE_NAME, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.writer(output_file, delimiter='\t')
        writer.writerows(training_data_lines)


def train_svm(doc_index, index, anchor_index):
    features = []
    rels = []
    with open(TRAINING_DATA_FILE_NAME, 'r', encoding='utf-8') as data_file:
        line = data_file.readline()
        line = line.split('\t')
        while line:
            query_text = line[0]
            doc_ids = [line[1]]
            rels.append(int(line[2].strip()))
            next_line = data_file.readline()
            while next_line:
                next_line = next_line.split('\t')
                if next_line[0] != query_text:

                    break
                doc_ids.append(next_line[1])
                rels.append(int(line[2].strip()))
                next_line = data_file.readline()

            query_features = get_features(format_text(query_text), doc_ids, doc_index, index, anchor_index)
            for feature in query_features:
                features.append(feature)
            line = next_line
    svm_model = svm.LinearSVC(max_iter=2000)
    svm_model.fit(features, rels)
    relevant_weights = list(svm_model.coef_[2])
    with open(WEIGHT_VECTOR_FILE_NAME, 'w') as weight_file:
        csv.writer(weight_file, delimiter='\t').writerow(relevant_weights)

    return relevant_weights


def get_features(query_words, doc_ids, doc_index, index, anchor_index):
    features = [[0 for x in range(0, 5)] for i in range(0, len(doc_ids))]
    if len(doc_ids) < len(doc_index):
        bm25_results = query(query_words, anchor_index, doc_index, None, None, 'bm25', limit_to=doc_ids)
    else:
        bm25_results =query(query_words, anchor_index, doc_index, None, None, 'bm25')
    results_dict = {}
    for result in bm25_results:
        results_dict[result[0]] = result
    num_query_terms = len(query_words)
    for doc in range(0, len(doc_ids)):
        doc_id = doc_ids[doc]
        if doc_id in results_dict:
            result = results_dict[doc_id]
            features[doc][0] = result[2]
            features[doc][1] = similarity(query_words, result[1])
        features[doc][2] = doc_index[doc_id]['page_rank']
        for term in query_words:
            if term in index:
                features[doc][3] += get_term_frequency(term, index, doc_id)
                features[doc][4] += index[term]['idf']
        features[doc][3] /= num_query_terms
        features[doc][4] /= num_query_terms
    return features


def get_term_frequency(term, index, doc_id):
    try:
        term_count = index[term]['docs'][doc_id]
        return math.log(term_count+1)
    except KeyError:
        return 0.0


def similarity(query_words, doc_title):
    num_in_title = 0
    doc_title_words = doc_title.split()
    for word in query_words:
        if word in doc_title_words:
            num_in_title += 1
    return num_in_title/len(query_words)


if __name__ == '__main__':
    main()
