"""
Collection of functions used for query expansion

query_expansion.py
@author Aaron Smith, Grant Larsen
11/26/2019
"""
from .porter import PorterStemmer


# ---------------------------------------------------------------------------------
# get terms from the stem dictionary if they match the query term
#
# @input: terms: list of given query terms
#         stem_dict: dictionary with the stem associations
# @return: new_term_list: the expanded list of query terms to use in retrieval
# ---------------------------------------------------------------------------------
def expand_term(terms, stem_dict):
    new_term_list = []
    ps = PorterStemmer()
    for i in terms:
        term_stem = "/" + ps.stem(i)
        if term_stem in stem_dict.keys():
            new_term_list += stem_dict[term_stem]
        else:
            new_term_list.append(i)
    return new_term_list
