from django.shortcuts import render
from django.http import HttpResponse
from .custom_lib.indexer import index_collection, create_stems
from .custom_lib.utils import get_docs_index, get_index, get_stems
from .custom_lib.retrieval_algorithms import query
from .custom_lib.query_expansion import expand_term

import time

DOC_INDEX = get_docs_index()
FREQ_INDEX = get_index()
ANCHOR_INDEX = get_index(anchor=True)
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
    terms_in = term_str.splti()

    expanded_terms = expand_term(terms_in, STEM_DICT)
    terms_out = ["math", "maths", "mathematical", "mathematics", "modeling", "models", "model", "uses", "of", "use",
             "useful", "usefulness"]
    res1 = sorted(query(expanded_terms, FREQ_INDEX, DOC_INDEX, ANCHOR_INDEX, '', "bm25"), key=lambda x: x[2], reverse=True)
    res2 = sorted(query(expanded_terms, FREQ_INDEX, DOC_INDEX, ANCHOR_INDEX, '', "bm25"), key=lambda x: x[2], reverse=True)
    print(len(res1))
    for i in res1[:10]:
        print(i)






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
