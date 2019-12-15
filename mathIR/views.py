from django.shortcuts import render
from django.http import HttpResponse
from .custom_lib.indexer import index_collection, create_stems
from .custom_lib.utils import get_docs_index, get_index, get_stems, get_svm_weights
from .custom_lib.retrieval_algorithms import query
from .custom_lib.query_expansion import expand_term

import time

DOC_INDEX = get_docs_index()
FREQ_INDEX = get_index()
ANCHOR_INDEX = get_index(anchor=True)
SVM_MODEL = get_svm_weights()
# Stems
try:
    STEM_DICT = get_stems('wiki_stems.tsv')
except FileNotFoundError:
    print('wiki_stems.tsv not found creating...')
    create_stems(FREQ_INDEX)
    STEM_DICT = get_stems('wiki_stems.tsv')

def results(request):
    t1 = time.time_ns()
    term_str = "uses of mathematical modeling"
    terms_in = term_str.split()

    expanded_terms = expand_term(terms_in, STEM_DICT)
    expanded_terms_list = []
    for i in terms_in:
        expanded_terms_list.append(expanded_terms(i, STEM_DICT))
    print(expanded_terms_list)
    terms_out = ["math", "maths", "mathematical", "mathematics", "modeling", "models", "model", "uses", "of", "use",
             "useful", "usefulness"]
    #doc_list = conjuctive_query(expanded_terms)
    mod_bm25_index = {k: v for k, v in FREQ_INDEX.items() if k in expanded_terms}
    doc_index_terms = {k: v for k, v in DOC_INDEX.items() if k in doc_list}
    res1 = sorted(query(expanded_terms, FREQ_INDEX, DOC_INDEX, ANCHOR_INDEX, SVM_MODEL, "bm25"),
                  key=lambda x: x[2], reverse=True)

    res3 = sorted(query(expanded_terms, FREQ_INDEX, DOC_INDEX, ANCHOR_INDEX, SVM_MODEL, "bm25",
                        doc_index_terms=DOC_INDEX),
                  key=lambda x: x[2], reverse=True)

    res2 = sorted(query(expanded_terms, FREQ_INDEX, DOC_INDEX, ANCHOR_INDEX, SVM_MODEL, "svm"),
                  key=lambda x: x[2], reverse=True)

    print(len(res1))
    print("rank", "bm25", "svm")
    print("---------------------------")
    for i in range(10):
        print(i, res1[i], res2[i])






    context = {'results_header': "Your Search was interpeted as: F(x) = m * a",
               'terms_list': ['term1'],
               'result_dict': {"Newton's laws of motion": ["Second law:	In an inertial frame of reference, "
                                                           "the vector sum of the forces F on an object is equal to ",
                                                           "the mass m of that object multiplied by the acceleration"
                                                           "a of the object: <b>F = ma</b>. (It is assumed here that",
                                                           "the mass m is constant – see below.)"],
                               "Kinematics": ["The acceleration of a particle is the vector defined by the rate of"
                                              " change of the velocity vector.",
                                              " The average acceleration of a particle "
                                              "over a time interval is defined as the ratio."]},

               'term_string': 'fx=ma',
               'facets': [('Maths', 'Maths', ''),
                          ('Physics', 'Physics', ''),
                          ('Biology', 'Biology', ''),
                          ('Economics', 'Economics', '')],
               'related': [('Kinematics', 1),
                           ('Classical Mechanics', 1),
                           ('Issac Newton', 1)],
               }
    return render(request, 'home/results.html', context)


def home(request):
    context = {}
    return render(request, 'home/home.html', context)


def main(request):
    #index_collection()
    return HttpResponse('Running Main')
