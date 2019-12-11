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
import string
import os
import csv
from math import ceil
from ..models import *
from nltk.tokenize import word_tokenize

COLLECTION_DIR = "mathIR\static\mathIR\MathTagArticles"
INDEX_DIR = "mathIR\static\mathIR"
DOC_INDEX_FILE_NAME = "doc_index.tsv"
INDEX_FILE_NAME = "wiki_index.tsv"
STEM_FILE_NAME = "wiki_stems.tsv"
POSITIONAL_INDEX_FILE_NAME = "wiki_positions.tsv"
BIGRAM_INDEX_FILE_NAME = "wiki_bigrams.tsv"
LINKED_FROM_INDEX_FILE_NAME = "linked_from_index.tsv"
PAGE_RANK_INDEX = 'page_rank_index.tsv'
PAGE_RANK_PARAM = 0.15

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

    fn = PAGE_RANK_INDEX
    with open(fn, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.writer(output_file, delimiter='\t')
        for key in docs_to_index:
            line = [key, new_ranks[docs_to_index[key]]]
            writer.writerow(line)
    return new_ranks

def vector_diff(v1, v2):
    if len(v1) != len(v2):
        return 'nani'
    diff = 0
    for ind in range(0, len(v1)):
        diff += abs(v1[ind] - v2[ind])
    return diff

def get_translation_dict():
    punctuation_dict = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    punctuation_dict[ord('\'')] = ''
    return punctuation_dict

# ---------------------------------------------------------------------------------
# create an index from a tsv with the position of words in the document
#
# @input: none
# @output: index: dictionary
# ---------------------------------------------------------------------------------
def get_pos_index():
    index = {}
    fn = os.path.join(INDEX_DIR, POSITIONAL_INDEX_FILE_NAME)
    with open(fn, 'r', encoding='utf-8') as index_file:
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
# @input: none
# @output: index: dictionary
# ---------------------------------------------------------------------------------
def get_bigrams():
    index = {}
    fn = os.path.join(INDEX_DIR, BIGRAM_INDEX_FILE_NAME)
    with open(fn, 'r', encoding='utf-8') as index_file:
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
def get_index():
    index = {}
    filename = os.path.join(INDEX_DIR, INDEX_FILE_NAME)
    with open(filename, 'r') as index_file:
        for line in index_file:
            line = line.split('\t')
            posting_list = line[2:]
            posting_dict = {}
            for posting in posting_list:
                posting = posting.split(':')
                posting_dict[posting[0]] =  int(posting[1])
            index[line[0]] = posting_dict
    return index



# ---------------------------------------------------------------------------------
# create an index from a tsv mapping episode number to title, word count
# and line count
#
# @input: None
# @output: doc_index: dictionary
# ---------------------------------------------------------------------------------
def get_docs_index():
    doc_index = {}
    filename = os.path.join(INDEX_DIR, DOC_INDEX_FILE_NAME)
    with open(filename, 'r', encoding='utf-8') as doc_file:
        for line in doc_file:
            line = line[:-1]
            split_line = line.split('\t')
            doc_index[split_line[0]] = {
                'title' : split_line[1],
                'name' : split_line[2],
                'words' : int(split_line[3]),
                'links' : int(split_line[4]),
                'links_to' : [],
                'linked_from' : []
            }
            if int(split_line[4]) > 0:
                doc_index[split_line[0]]['links_to'] = split_line[5:]

    filename = os.path.join(INDEX_DIR, LINKED_FROM_INDEX_FILE_NAME)
    with open(filename, 'r', encoding='utf-8') as link_file:
        for line in link_file:
            line = line[:-1]
            split_line = line.split('\t')
            for doc in split_line[2:]:
                doc_index[line[0]]['linked_from'].append(doc)

    return doc_index


# ---------------------------------------------------------------------------------
# create an index from a tsv with the stems and their associated words
#
# @input: filename: tsv of stems
# @output: stems: dictionary
# ---------------------------------------------------------------------------------
def get_stems():
    stems = {}
    filename = os.path.join(INDEX_DIR, STEM_FILE_NAME)
    with open(filename, 'r', encoding='utf-8') as stem_file:
        for line in stem_file:
            line = line.split('\t')
            stems[line[0]] = line[1:-1]
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
# TODO refactor this to work with tar files
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
    # skip the meta line
    f.readline()
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
#         term2: list of documents that contain the second term
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
def clean_text(doc):
    doc = doc.lower()
    doc = doc.translate(str.maketrans('', '', string.punctuation))
    return doc


# ---------------------------------------------------------------------------------
# create tokens from a given string, using the nltk tokenizer
#
# @input: doc: string to create tokens from
# @return: doc_index: a dictionary of tokens and their frequency
# ---------------------------------------------------------------------------------
def tokenize_doc(doc):
    tokens = word_tokenize(doc)
    doc_index = {}
    for token in tokens:
        if token in doc_index:
            doc_index[token] += 1
        else:
            doc_index[token] = 1
    return doc_index


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