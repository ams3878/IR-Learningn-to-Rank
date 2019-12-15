from django.shortcuts import render
from django.http import HttpResponse
from .custom_lib.indexer import index_collection
from .custom_lib.utils import get_docs_index, get_index
from .custom_lib.retrieval_algorithms import query
import time

DOC_INDEX = get_docs_index()
FREQ_INDEX = get_index()
ANCHOR_INDEX = get_index()
def results(request):
    t1 = time.time_ns()
    terms = ["math", "maths", "mathematical", "mathematics", "modeling", "models", "model", "uses", "of", "use",
             "useful", "usefulness"]

    res1 = sorted(query(terms, FREQ_INDEX, DOC_INDEX, '', "bm25"), key=lambda x: x[2], reverse=True)
    res2 = sorted(query(terms, FREQ_INDEX, DOC_INDEX, '', "bm25"), key=lambda x: x[2], reverse=True)
    print(len(res))
    for i in res[:10]:
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
