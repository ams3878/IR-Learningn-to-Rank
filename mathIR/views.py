from django.shortcuts import render
from django.http import HttpResponse
from .custom_lib.indexer import index_collection, create_stems
from .custom_lib.utils import get_docs_index, get_index, get_stems, get_svm_weights, conjuctive_query, get_index2, \
    get_lines
from .custom_lib.retrieval_algorithms import query
from .custom_lib.query_expansion import expand_term
from .custom_lib.query_suggestion import clean_terms
import time
import tarfile
import os

DOC_INDEX = get_docs_index()
FREQ_INDEX = get_index()
FREQ_INDEX2 = get_index2()
ANCHOR_INDEX = get_index(anchor=True)
SVM_MODEL = get_svm_weights()
COLLECTION_DIR = "mathIR\static\mathIR\MathTagArticles"
HTML_DIR = "mathIR\static\collectionDocs\html"
# Stems
try:
    STEM_DICT = get_stems('wiki_stems.tsv')
except FileNotFoundError:
    print('wiki_stems.tsv not found creating...')
    create_stems(FREQ_INDEX)
    STEM_DICT = get_stems('wiki_stems.tsv')


def html(request):
    info = request.GET['id'].split()
    with open(os.path.join(HTML_DIR, info[1] + ".html")) as html_page:
        return HttpResponse(html_page.read())

def results(request):
    result_dict = {}
    t1 = time.time_ns()
    results_header = ""
    term_str = request.GET['query'].lower().strip()
    terms_in = term_str.split()
    clean_start = time.time_ns()
    terms_clean = clean_terms(terms_in, FREQ_INDEX, DOC_INDEX)
    clean_stop = time.time_ns()
    if terms_in != terms_clean:
        results_header = "No reasults found for [" + term_str
        term_str = ' '.join(terms_clean)
        results_header += "] searching [" + term_str + "] instead..."
    terms_in = terms_clean
    expand_start = time.time_ns()
    expanded_terms = expand_term(terms_in, STEM_DICT)
    expand_stop = time.time_ns()
    expanded_terms_list = []
    for i in terms_in:
        expanded_terms_list.append(expand_term([i], STEM_DICT))

    t2 = time.time_ns()
    mod_bm25_index = {k: v for k, v in FREQ_INDEX.items() if k in expanded_terms}
    doc_list = conjuctive_query(expanded_terms_list, mod_bm25_index)
    doc_index_terms = {k: v for k, v in DOC_INDEX.items() if k in doc_list}
    res3 = sorted(query(expanded_terms, mod_bm25_index, DOC_INDEX, ANCHOR_INDEX, SVM_MODEL, "bm25mod",
                        doc_index_terms=doc_index_terms),
                  key=lambda x: x[2], reverse=True)[0:10]

    t3 = time.time_ns()
    res1 = sorted(query(expanded_terms, FREQ_INDEX, DOC_INDEX, ANCHOR_INDEX, SVM_MODEL, "bm25"),
                  key=lambda x: x[2], reverse=True)[0:10]

    t4 = time.time_ns()
    res2 = sorted(query(expanded_terms, FREQ_INDEX, DOC_INDEX, ANCHOR_INDEX, SVM_MODEL, "svm"),
                  key=lambda x: x[2], reverse=True)[0:10]

    print("SETUP TIME ", (t2-t1)/1000, "us")
    print("Clean Time: ", (clean_stop-clean_start)/1000000, "ms")
    print("Expand Time: ", (expand_stop-expand_start)/1000000, "ms")

    print("MOD BM 25: ", (t3-t2)/1000000, "ms")
    print("BM 25: ", (t4-t3)/1000000, "ms")
    print("SVM: ", (time.time_ns() - t4)/1000000, "ms")

    print("rank\t", "bm25\t", "svm\t", "mod_bm25")
    print("---------------------------")
    for i in range(10):
        prnt_str = str(i) + '\t'
        if i < len(res1):
            prnt_str += "{:25}\t".format(str(res1[i][1])[:25])
        else:
            prnt_str += '\t'
        if i < len(res2):
            prnt_str += "{:25}\t".format(str(res2[i][1])[:25])
        else:
            prnt_str += '\t'
        if i < len(res3):
            prnt_str += "{:25}\t".format(str(res3[i][1])[:25])
        else:
            prnt_str += '\t'
        print(prnt_str)
    t5 = time.time_ns()
    for i in res2:
        result_dict[i[1]] = (i[0], get_lines(terms_in, FREQ_INDEX, i[0], i[1]))
    t6 = time.time_ns()
    time_to_query = str((t4-t3)/1000000) + "ms"
    time_to_render = str((t6-t5)/1000000) + "ms"
    print("Render Time:", time_to_render, "Query Time: ", time_to_query)

    context = {'results_header': results_header,
               'terms_list': terms_in,
               'result_dict': result_dict,
               'term_string': term_str,
               'time': [time_to_query, time_to_render],
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
