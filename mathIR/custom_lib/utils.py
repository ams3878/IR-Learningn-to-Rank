"""
Utility files used to run Pony Poratal app
    - create Django objects and relations
    - create indexes from tsv
    - clean raw html text
    - helper functions fo query suggestion and expansion
    - document summary and query term highlighting
utils.py
@author Aaron Smith, Grant Larsen
11/26/2019
"""

import re
import os
import string
import csv
import unicodedata

from nltk.tokenize import word_tokenize

INDEX_DIR = 'E:\_Projects\IR_P3\mysite\mathIR\static\idexTSV'
from unidecode import unidecode
from nltk.tokenize import word_tokenize

INDEX_FILENAME = 'wiki_index.tsv'
DOC_INDEX_FILENAME = 'doc_index.tsv'
LINKED_FROM_INDEX_FILENAME = 'linked_from_index.tsv'
PAGE_RANK_INDEX_FILENAME = 'page_rank_index.tsv'
ANCHOR_TEXT_INDEX_FILENAME = 'anchor_text_index.tsv'
STEM_FILE_NAME = "wiki_stems.tsv"
SVM_RESULTS_FILE_NAME = 'svm_weights.tsv'

PAGE_RANK_PARAM = 0.15


def get_translation_dict():
    punctuation_dict = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    punctuation_dict[ord('\'')] = ''
    return punctuation_dict


TRANSLATION_DICT = get_translation_dict()


def rank_pages(doc_index):
    page_count = len(doc_index)
    link_total = 0
    docs_to_index = {}
    ind = 0
    for doc in doc_index:
        link_total += doc_index[doc]['links']
        docs_to_index[doc] = ind
        ind += 1
    prev_ranks = [len(doc_index[doc]['linked_from'])/link_total for doc in doc_index]
    default_value = PAGE_RANK_PARAM / page_count

    err = 1
    new_ranks = []
    while err > 0.001:
        new_ranks = [default_value]*page_count

        for doc in doc_index:
            current_ind = docs_to_index[doc]
            linked_from = doc_index[doc]['linked_from']
            num_from = len(linked_from)
            if num_from > 0:
                to_add= (1 - PAGE_RANK_PARAM) * prev_ranks[current_ind] / num_from
                for link in linked_from:
                    from_ind = docs_to_index[link]
                    new_ranks[from_ind] += to_add
            else:
                to_add = (1 - PAGE_RANK_PARAM) * prev_ranks[current_ind] / page_count
                for page in doc_index:
                    from_ind = docs_to_index[page]
                    new_ranks[from_ind] += to_add
        err = vector_diff(new_ranks, prev_ranks)
        print(err)
        prev_ranks = new_ranks

    fn = PAGE_RANK_INDEX_FILENAME
    with open(fn, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.writer(output_file, delimiter='\t')
        for key in docs_to_index:
            line = [key, new_ranks[docs_to_index[key]]]
            writer.writerow(line)
    return new_ranks


def vector_diff(v1, v2):
    if len(v1) != len(v2):
        return 'this shouldnt happen'
    diff = 0
    for ind in range(0, len(v1)):
        diff += abs(v1[ind] - v2[ind])
    return diff


def get_svm_weights():
    weights = []
    fn = os.path.join(INDEX_DIR, SVM_RESULTS_FILE_NAME)
    with open(fn, 'r') as svm_file:
        line = svm_file.readline()
        for weight in line.split('\t'):
            weights.append(float(weight))
    return weights


# ---------------------------------------------------------------------------------
# create an index from a tsv with the position of words in the document
#
# @input: filename: tsv of positions
# @output: index: dictionary
# ---------------------------------------------------------------------------------
def get_pos_index(filename):
    index = {}
    with open('ponyportal\static\ponyportal\\' + filename, 'r') as index_file:
        line = index_file.readline()
        while line:
            line = line.split('\t')
            posting_list = line[1:-1]
            posting_dict = {}
            for posting in posting_list:
                posting = posting.split(':')
                try:
                    posting_dict[int(posting[0])].append(int(posting[1]))
                except KeyError:
                    posting_dict[int(posting[0])] = [int(posting[1])]
            index[line[0]] = posting_dict

            line = index_file.readline()
    return index


# ---------------------------------------------------------------------------------
# create an index from a tsv with all the bigrams in the document
#
# @input: filename: tsv of bigrams
# @output: index: dictionary
# ---------------------------------------------------------------------------------
def get_bigrams(filename):
    index = {}
    with open('ponyportal\static\ponyportal\\' + filename, 'r') as index_file:
        line = index_file.readline()
        while line:
            line = line.split('\t')
            posting_list = line[1:-1]
            posting_dict = {}
            for posting in posting_list:
                posting = posting.split(':')
                posting_dict[posting[0]] = posting[1]
            index[line[0]] = posting_dict
            line = index_file.readline()
    return index


# ---------------------------------------------------------------------------------
# create an index from a tsv with frequency words in the document
#
# @input: filename: tsv of frequencies
# @output: index: dictionary
# ---------------------------------------------------------------------------------
def get_index(anchor=False):
    index = {}
    if anchor:
        filename = os.path.join(INDEX_DIR, ANCHOR_TEXT_INDEX_FILENAME)
    else:
        filename = os.path.join(INDEX_DIR, INDEX_FILENAME)

    with open(filename, 'r', encoding='utf-8') as index_file:
        line = index_file.readline()
        while line:
            line = line.split('\t')
            posting_list = line[3:]
            posting_dict = {'docs': {}}
            for posting in posting_list:
                posting = posting.split(':')
                posting_dict['docs'][posting[0]] = int(posting[1])
            posting_dict['count'] = int(line[2])
            posting_dict['idf'] = float(line[1])
            index[line[0]] = posting_dict

            line = index_file.readline()
    return index


# ---------------------------------------------------------------------------------
# create an index from a tsv with the frequcency of words in  document windows
# window size is set to be one line
# @input: None
# @output: index: dictionary
# ---------------------------------------------------------------------------------
# def get_window_index():
#     index = {}
#     with open(WINDOW_INDEX_FILENAME, 'r') as index_file:
#         line = index_file.readline()
#         while line:
#             line = line.split('\t')
#             posting_list = line[2:]
#             posting_dict = {'count': int(line[1])}
#             for posting in posting_list:
#                 posting = posting.split(':')
#                 if posting[0] not in posting_dict:
#                     posting_dict[posting[0]] = []
#                 posting_dict[posting[0]].append(int(posting[1]))
#             index[line[0]] = posting_dict
#
#             line = index_file.readline()
#     return index


# ---------------------------------------------------------------------------------
# create an index from a tsv mapping episdoe number to title, word count
# and line count
#
# @input: None
# @output: doc_index: dictionary
# ---------------------------------------------------------------------------------
def get_docs_index():
    doc_index = {}
    filename = os.path.join(INDEX_DIR, DOC_INDEX_FILENAME)
    with open(filename, 'r', encoding='utf-8') as doc_file:
        line = doc_file.readline()[:-1]
        while line:
            line = line.split('\t')
            if line[0] in doc_index:
                print(line)
            try:
                doc_index[line[0]] = {
                    'title' : line[1],
                    'name' : line[2],
                    'words' : int(line[3]),
                    'links' : int(line[4]),
                    'links_to' : [],
                    'linked_from' : []
                }
                if int(line[4]) > 0:
                    doc_index[line[0]]['links_to'] = line[5:]
            except IndexError:
                print(line)
            line = doc_file.readline()[:-1]

    filename = os.path.join(INDEX_DIR, LINKED_FROM_INDEX_FILENAME)
    with open(filename, 'r', encoding='utf-8') as link_file:
        line = link_file.readline()[:-1]
        while line:
            line = line.split('\t')
            for doc in line[2:]:
                doc_index[line[0]]['linked_from'].append(doc)
            line = link_file.readline()[:-1]

    filename = os.path.join(INDEX_DIR, PAGE_RANK_INDEX_FILENAME)
    with open(filename, 'r', encoding='utf-8') as rank_file:
        for line in rank_file:
            line = line.split('\t')
            doc_index[line[0]]['page_rank'] = float(line[1])

    return doc_index


# ---------------------------------------------------------------------------------
# create an index from a tsv with the stems and their associated words
#
# @input: filename: tsv of stems
# @output: stems: dictionary
# ---------------------------------------------------------------------------------
def get_stems(filename):
    stems = {}
    with open(os.path.join(INDEX_DIR, filename), 'r') as stem_file:
        line = stem_file.readline()
        while line:
            line = line.split('\t')
            stems[line[0]] = line[1:-1]
            line = stem_file.readline()
    return stems



# ---------------------------------------------------------------------------------
# Creates document summaries for each related document and highlights
# any terms that match the query.  Summaries are top 5 lines after scoring each line
# from its normalized tf*idf
#
# @input: term: the list of query terms used by the retrieval algorithm
#         idf_list: list of idfs calculated by the retrieval algorithm
#         episode: number of the episode used to get the raw html
# @return: matched_lines: top 5 of line of the doc sum
# ---------------------------------------------------------------------------------
def get_lines_keywords(terms, idf_list, episode):
    f = open('ponyportal\static\episodes\\' + str(episode), 'r')
    stopword_list = get_stopwords()
    terms_dict = {}
    stop_dict = {}
    for x in terms:
        if x not in stopword_list:
            terms_dict[x] = "<b>" + x + "</b>"
        else:
            stop_dict[x] = "<b>" + x + "</b>"
    matched_lines = []
    matched_lines_stop = []
    term_regex = re.compile('(.*)([\W\s])(' + '|'.join(terms_dict.keys()) + ')([\W\s])(.*)', re.IGNORECASE)
    term_regex_stop = re.compile('(.*)([\W\s])(' + '|'.join(stop_dict.keys()) + ')([\W\s])(.*)', re.IGNORECASE)

    for line in f:
        line_list = line
        line_list = line_list.lower().translate(str.maketrans('', '', string.punctuation)).split()
        score = 0
        for t in range(len(terms)):
            if terms[t] in line_list:
                score += idf_list[t] / len(line_list)
        temp_line = re.sub(term_regex, lambda y: y.group(1) + y.group(2) +
                                                 terms_dict[y.group(3).lower()]
                                                 + y.group(4) + y.group(5), line)
        if line != temp_line:
            matched_lines.append((temp_line, score))
        if len(stop_dict) != 0:
            temp_line_stop = re.sub(term_regex_stop, lambda y: y.group(1) + y.group(2) +
                                                               stop_dict[y.group(3).lower()]
                                                               + y.group(4) + y.group(5), line)
            if line != temp_line_stop:
                matched_lines_stop.append((temp_line_stop, score))

    f.close()

    if len(matched_lines) < 5:
        matched_lines += matched_lines_stop
    return [y[0] for y in sorted(matched_lines[0:5],  key=lambda z: z[1], reverse=True)][0:5]


# ---------------------------------------------------------------------------------
# calculate the dice coefficient of two terms
#
# @input: term1: list of documents that contain the first term
#         term2L list of ducuments that contain the second term
# @output: float: dice coefficient
# ---------------------------------------------------------------------------------
def get_dice_coeff(term1, term2):
    term_intersects = 0
    for doc in term1:
        if doc != 'count' and doc in term2:
            intersect = [value for value in term1[doc] if value in term2[doc]]
            term_intersects += len(intersect)
    return 2*term_intersects/(term1['count'] + term2['count'])


# ---------------------------------------------------------------------------------
# calculate the levenshtein distance of two words in order to correct spelling
# errors
#
# @input: term1: first term
#         term2: second word
# @output: the levenshtein distance
# ---------------------------------------------------------------------------------
def get_levenshtein_distance(term1, term2):
    matrix = [[0 for x in range(len(term2) + 1)] for x in range(len(term1) + 1)]

    for x in range(len(term1) + 1):
        matrix[x][0] = x
    for y in range(len(term2) + 1):
        matrix[0][y] = y

    for x in range(1, len(term1) + 1):
        for y in range(1, len(term2) + 1):
            if term1[x - 1] == term2[y - 1]:
                matrix[x][y] = min(
                    matrix[x - 1][y] + 1,
                    matrix[x - 1][y - 1],
                    matrix[x][y - 1] + 1
                )
            else:
                matrix[x][y] = min(
                    matrix[x - 1][y] + 1,
                    matrix[x - 1][y - 1] + 1,
                    matrix[x][y - 1] + 1
                )

    return matrix[len(term1)][len(term2)]


# ---------------------------------------------------------------------------------
# set a string to lower case and remove all punctuations
#
# @input: doc: string to clean
# @return: doc: the cleaned string
# ---------------------------------------------------------------------------------
def clean_text(doc_text):
    text = doc_text.lower().translate(TRANSLATION_DICT)
    try:
        text = remove_accents(text)
    except UnicodeEncodeError:
        print(doc_text)

    return str(text)


# ---------------------------------------------------------------------------------
# create tokens from a given string, using the nltk tokenizer
#
# @input: doc: string to create tokens from
# @return: doc_index: a dictionary of tokens and their frequency
# ---------------------------------------------------------------------------------
def tokenize_doc(doc_words, index):
    for token in doc_words:
        if token in index:
            index[token] += 1
        else:
            index[token] = 1

# ---------------------------------------------------------------------------------
# Get stop words from file
#
# @input: None
# @ouput: list of stopwords
# ---------------------------------------------------------------------------------
def get_stopwords():
    f = open('ponyportal\static\ponyportal\stopwords.txt', 'r')
    line = f.read()
    f.close()
    return line.split(',')


# ---------------------------------------------------------------------------------
# Get stopwords from list, given by NTLK
#
# @input:
# @ouput:
# ---------------------------------------------------------------------------------
def get_stop_words():
    return ['ourselves', 'hers', 'between', 'yourself', 'but', 'again', 'there', 'about', 'once', 'during', 'out',
            'very', 'having', 'with', 'they', 'own', 'an', 'be', 'some', 'for', 'do', 'its', 'yours', 'such',
            'into',
            'of', 'most', 'itself', 'other', 'off', 'is', 's', 'am', 'or', 'who', 'as', 'from', 'him', 'each',
            'the',
            'themselves', 'until', 'below', 'are', 'we', 'these', 'your', 'his', 'through', 'don', 'nor', 'me',
            'were',
            'her', 'more', 'himself', 'this', 'down', 'should', 'our', 'their', 'while', 'above', 'both', 'up',
            'to',
            'ours', 'had', 'she', 'all', 'no', 'when', 'at', 'any', 'before', 'them', 'same', 'and', 'been', 'have',
            'in', 'will', 'on', 'does', 'yourselves', 'then', 'that', 'because', 'what', 'over', 'why', 'so', 'can',
            'did', 'not', 'now', 'under', 'he', 'you', 'herself', 'has', 'just', 'where', 'too', 'only', 'myself',
            'which', 'those', 'i', 'after', 'few', 'whom', 't', 'being', 'if', 'theirs', 'my', 'against', 'a', 'by',
            'doing', 'it', 'how', 'further', 'was', 'here', 'than', 'get']


def remove_accents(text):
    return unidecode(text)


def format_text(doc_text):
    doc_text = clean_text(doc_text)
    doc_words = word_tokenize(doc_text)
    doc_text = []

    for word in doc_words:
        word = word.strip()
        if word:
            doc_text.append(word)
    return doc_text
