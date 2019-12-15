"""
Collection of retrieval algorithms

retrieval_algorithms.py
@author Aaron Smith, Grant Larsen
11/26/2019
"""
import math

from svm_util import get_features
# -----
# BM25 parameters
# -----
K_1 = 1.2
K_2 = 100.0
B = 0.75
R = 0
R_i = 0


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
