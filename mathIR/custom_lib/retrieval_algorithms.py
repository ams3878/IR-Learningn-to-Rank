"""
Collection of retrieval algorithms

retrieval_algorithms.py
@author Aaron Smith, Grant Larsen
11/26/2019
"""
import math

# -----
# BM25 parameters
# -----
K_1 = 1.2
K_2 = 100.0
B = 0.75


# ---------------------------------------------------------------------------------
# wrapper function to be called to get the related documents
#
# @input: terms: list of given query terms
#         index: dictionary with document word frequencies
#         doc_index: index with word, and line counts
#         query_model: string to specify retrieval algorithm to use
# @return: list of documents(some variation based on algorithm)
# ---------------------------------------------------------------------------------
def query(terms, index, doc_index, query_model):
    if query_model == 'tfidf':
        return tfidf(terms, index)
    else:
        return query_bm25(terms, index, doc_index)


# ---------------------------------------------------------------------------------
# get list of documents using basic tf-idf to rank
#
# @input: terms: list of given query terms
#         index: dictionary with document word frequencies
# @return: doc_scores: list tuples(documents,score)
#          idf_list: list of idfs for each term(used in doc sum)
# ---------------------------------------------------------------------------------
def tfidf(terms, index):
    doc_sums = {}
    doc_scores = []
    prev_idf_sqrs = []
    idf_list = []
    for term in terms:
        try:
            idf = math.log(244 / int(index[term]['count']))
            idf_list.append(idf)
            for doc, frequency in index[term]['docs'].items():
                tf = math.log(frequency+1)
                tf_idf = tf*idf
                sqrs = tf_idf*tf_idf
                try:
                    doc_sums[doc] = (doc_sums[doc][0] + tf_idf, doc_sums[doc][1] + sqrs)
                except KeyError:
                    for i in prev_idf_sqrs:
                        sqrs += i
                    doc_sums[doc] = (tf_idf, sqrs)
            prev_idf_sqrs.append(idf*idf)
        except KeyError:
            idf_list.append(0)
            continue
        update_old = [x for x in doc_sums if x not in index[term]['docs']]
        for x in update_old:
            doc_sums[x] = (doc_sums[x][0], doc_sums[x][1] + sqrs)
    for i, sums in doc_sums.items():
        doc_scores.append((i, sums[0]/math.pow(sums[1], .5)))
    doc_scores = sorted(doc_scores, key=lambda tup: tup[1], reverse=True)
    return doc_scores, idf_list


# ---------------------------------------------------------------------------------
# get list of documents using BM25 to rank
#
# @input: terms: list of given query terms
#         index: dictionary with document word frequencies
#         doc_index: dictionary for word and line count
# @return: doc_scores: list tuples(documents,score)
# ---------------------------------------------------------------------------------
def query_bm25(terms, index, doc_index):
    term_counts ={}
    for term in terms:
        if term in term_counts:
            term_counts[term] += 1
        else:
            term_counts[term] = 1

    avg_dl = 0.0
    doc_scores = {}
    for doc in doc_index:
        avg_dl += float(doc_index[doc][1])

    avg_dl /= len(doc_index)
    n = len(doc_index)

    doc_k = {}
    for doc in doc_index:
        doc_k[doc] = K_1*((1 - B) + B * (float(doc_index[doc][1])/avg_dl))

    for term in term_counts:
        try:
            index_entry = index[term]
            n_i = float(index_entry['count'])
        except KeyError:
            continue

        term_weight = math.log(n/n_i, 10)

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
    doc_scores = [(doc, doc_scores[doc]) for doc in doc_scores]
    doc_scores = sorted(doc_scores, key=lambda tup: tup[1], reverse=True)
    return doc_scores
