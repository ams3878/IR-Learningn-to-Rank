"""
Collection of functions used to create all the indexes used for IR

indexer.py
@author Aaron Smith, Grant Larsen
11/26/2019
"""
import re
import os
import tarfile
import time
import string
import csv
import unicodedata
from bs4 import BeautifulSoup
from nltk import word_tokenize
from .utils import get_index, clean_text, tokenize_doc, get_translation_dict
from .porter import PorterStemmer

COLLECTION_DIR = "mathIR\static\mathIR\MathTagArticles"
INDEX_DIR = "mathIR\static\mathIR"
DOC_FILE_NAME = "doc_index.tsv"
INDEX_FILE_NAME = "wiki_index.tsv"
STEM_FILE_NAME = "wiki_stems.tsv"
POSITIONAL_INDEX_FILE_NAME = "wiki_positions.tsv"
BIGRAM_INDEX_FILE_NAME = "wiki_bigrams.tsv"
WINDOW_INDEX_FILE_NAME = "wiki_window_index.tsv"
LINKED_FROM_INDEX = 'indices/linked_from_index.tsv'

TRANSLATION_DICT = get_translation_dict()
WINDOW_SIZE = 30


# ---------------------------------------------------------------------------------
# creates document level frequency tsv
#
# @input: None
# @return: None
# ---------------------------------------------------------------------------------
def index_collection():
    index = {}
    doc_ids = {}
    link_index = {}
    doc_file_lines = []
    t1 = time.perf_counter()



    for filename in os.listdir(COLLECTION_DIR):
        if filename.endswith(".tar.bz2"):
            dir_name = str(int(filename[7:-8]))
            formatted_filename = os.path.join(COLLECTION_DIR, filename)
            tar = tarfile.open(formatted_filename, 'r:bz2')

            for file in tar:
                if not file.name.endswith('.html'):
                    continue

                html_file = tar.extractfile(file)
                content = html_file.read()
                soup = BeautifulSoup(content, 'html.parser')

                doc_id = dir_name + '-' + soup.title['offset']
                doc_title = file.name[14:-5].lower()
                doc_name = clean_str(soup.title.string)
                doc_ids[doc_title] = doc_id
                doc_index = {}
                links_out = clean_soup(soup, doc_index)
                for link in links_out:
                    if link not in link_index:
                        link_index[link] = []
                    link_index[link].append(doc_id)
                doc_text = soup.get_text()
                words = format_doc(doc_text)

                index_doc(words, doc_index)

                # merge document index with the corpus index
                for token in doc_index:
                    index_str = doc_id + ':' + str(doc_index[token])
                    if token not in index:
                        index[token] = []
                    index[token].append(index_str)
                doc_file_line = [doc_id, doc_title, doc_name, len(words), len(links_out)]
                for link in links_out:
                    doc_file_line.append(link)
                doc_file_lines.append(doc_file_line)
        else:
            continue

    with open(DOC_FILE_NAME, 'w', newline='', encoding='utf-8') as doc_file:
        writer = csv.writer(doc_file, delimiter="\t")
        for file in doc_file_lines:
            new_line = file[:5]
            for link in file[5:]:
                if link in doc_ids:
                    new_line.append(doc_ids[link])
            writer.writerow(new_line)

    fn = INDEX_FILE_NAME
    with open(fn, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.writer(output_file, delimiter='\t')
        for key in sorted(index.keys()):
            docs = index[key]
            line = [key, len(docs)]
            for doc in docs:
                line.append(doc)
            writer.writerow(line)

    fn = LINKED_FROM_INDEX
    with open(fn, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.writer(output_file, delimiter='\t')
        for key in sorted(link_index.keys()):
            if key in doc_ids:
                docs = link_index[key]
                line = [doc_ids[key], len(docs)]
                for doc in docs:
                    line.append(doc)
                writer.writerow(line)
    print(time.perf_counter() - t1)


# ---------------------------------------------------------------------------------
# creates window level frequency tsv with window size of one line
#
# @input: None
# @return: None
# ---------------------------------------------------------------------------------
def create_window_index_tsv():
    index = {}

    for filename in os.listdir(COLLECTION_DIR):
        if filename.endswith(".tar.bz2"):
            dir_name = str(int(filename[7:-8]))
            formatted_filename = os.path.join(COLLECTION_DIR, filename)
            tar = tarfile.open(formatted_filename, 'r:bz2')
            for file in tar:
                if not file.name.endswith('.html'):
                    continue

                html_file = tar.extractfile(file)
                content = html_file.read()
                soup = BeautifulSoup(content, 'html.parser')

                doc_id = dir_name + '-' + soup.title['offset']
                doc_index = {}
                clean_soup(soup, doc_index)
                doc_text = soup.get_text()
                words = format_doc(doc_text)
                window = 0
                for word_index in range(0, len(words), WINDOW_SIZE):
                    max_ind = word_index + WINDOW_SIZE
                    if max_ind >= len(words):
                        max_ind = len(words)
                    doc_index = {}
                    index_doc(' '.join(words[word_index:max_ind]), doc_index)
                    for token in doc_index:
                        index_str = doc_id + ':' + str(window)
                        if token not in index:
                            index[token] = index_str
                        else:
                            index[token] += ('\t' + index_str)
                    window += 1

    # Write index to a file
    with open(WINDOW_INDEX_FILE_NAME, 'w') as output_file:
        for key in sorted(index.keys()):
            line = "%s\t%d\t%s\n" % (key, len(index[key].split('\t')), index[key])
            output_file.write(line)


# ---------------------------------------------------------------------------------
# creates tsv with word positions
#
# @input: None
# @return: None
# ---------------------------------------------------------------------------------
def create_index_tsv_positions():
    doc_index = {}
    for filename in os.listdir('./ponyportal/static/episodes'):
        formatted_filename = os.path.join('.\ponyportal\static\episodes', filename)

        with open(formatted_filename, 'r') as f:
            doc_text = f.read()
            doc_text = clean_text(doc_text)
            tokens = word_tokenize(doc_text)
            for i in range(len(tokens)):
                try:
                    doc_index[tokens[i]].append((filename, i+1))
                except KeyError:
                    doc_index[tokens[i]] = [(filename, i+1)]

    # Write index to a file
    with open(POSITIONAL_INDEX_FILE_NAME, 'w') as output_file:
        for word, pos_list in sorted(doc_index.items()):
            line = word
            for pos in pos_list:
                line += "\t%s:%s" % (pos[0], pos[1])
            line += "\t\n"
            output_file.write(line)


# ---------------------------------------------------------------------------------
# creates tsv of all the bigrams, with relation above a given threshold
#
# @input: pos_index: dictionary with word positions
#         freq_index: dictionary with word frequencies
# @return: None
# ---------------------------------------------------------------------------------
def make_bigrams(pos_index, freq_index, threshold):
    with open(BIGRAM_INDEX_FILE_NAME, 'w') as output_file:
        for word_1 in pos_index:
            bigrams = {}
            for word_2 in pos_index:
                for doc, pos_list in pos_index[word_1].items():
                    if doc in pos_index[word_2].keys():
                        for pos in pos_list:
                            if pos + 1 in pos_index[word_2][doc]:
                                try:
                                    bigrams[word_2] += 1
                                except KeyError:
                                    bigrams[word_2] = 1

            line = word_1
            for word_2, count in bigrams.items():
                freq = 0
                for w, w_count in freq_index[word_1]["docs"].items():
                    freq += int(w_count)
                ratio = count/freq
                if ratio > threshold:
                    line += "\t" + word_2 + ":" + str(ratio)
            line += "\t\n"
            if line != word_1 + "\t\n":
                output_file.write(line)


# ---------------------------------------------------------------------------------
# creates tsv of stems, only stems with more than one associated words are stored
# used the porter stemmer to create the stems
#
# @input: index_tsv: the tsv of word frequencies
# @return: None
# ---------------------------------------------------------------------------------
def create_stems(index_tsv):
    vocab = list(get_index(index_tsv).keys())
    stemmer = PorterStemmer()
    stems = [stemmer.stem(word) for word in vocab]
    stem_dict = {}
    for i in range(len(stems)):
        try:
            stem_dict[stems[i]].append(vocab[i])
        except KeyError:
            stem_dict[stems[i]] = [vocab[i]]
    with open(STEM_FILE_NAME, 'w') as f:
        for stem, word_list in sorted(stem_dict.items()):
            if len(word_list) > 1:
                line = "/" + stem
                for word in word_list:
                    line = line + "\t" + word
                line = line + "\t\n"
                f.write(line)

"""
Tokenizes the words in a document then returns a dictionary from each word to its number of occurances in the doc
"""
def index_doc(doc_words, index):
    for token in doc_words:
        if token in index:
            index[token] += 1
        else:
            index[token] = 1

def format_doc(doc_text):
    doc_text = clean_str(doc_text)
    doc_words = word_tokenize(doc_text)
    doc_text = []

    for word in doc_words:
        word = word.rstrip()
        if word:
            if re.match("^[A-Za-z0-9]*$", word):
                if len(word):
                    doc_text.append(word)
    return doc_text


def clean_soup(soup, formula_index):
    links_out = []
    for formula in soup.find_all('math'):
        if formula.a:
            continue

        try:
            if formula and formula.semantics and formula.semantics.annotation and formula.semantics.annotation.string:
                formula_string = formula.semantics.annotation.string
            else:
                formula_string = formula.semantics.mn.string
            formula_string = formula_string.replace('%\n', '')
            formula_string = formula_string.translate({ord(c): None for c in string.whitespace})
            if formula_string not in formula_index:
                formula_index[formula_string] = 1
            else:
                formula_index[formula_string] += 1
        except AttributeError:
            continue


        formula.decompose()

    for link in soup.find_all('a'):
        try:
            # I tried "if 'title' in link:" but it didnt work...
            link['title']
            anchor_text = link['href'].lower()
            if 'category:' in anchor_text or 'file:' in anchor_text or 'image:' in anchor_text or 'portal:' in anchor_text:
                continue
            elif anchor_text.find('s:') == 0:
                anchor_text = anchor_text[2:]
            elif len(anchor_text) > 4 and anchor_text[0] == ':' and anchor_text[3] == ':':
                anchor_text = anchor_text[4:]
            elif '#' in anchor_text:
                anchor_text = anchor_text[:anchor_text.find('#')]
            if anchor_text not in links_out:
                links_out.append(anchor_text)
        except KeyError:
            continue

    for span in soup.find_all('span'):
        if 'class' in span:
            if 'LaTeX' in span['class']:
                span.string.replace_with('')
    for thing in soup.find_all('csymbol'):
        if thing.string is not None:
            thing.string.replace_with('')

    return links_out


def clean_str(doc_text):
    text = doc_text.lower().translate(TRANSLATION_DICT)
    try:
        text = remove_accents(text)
    except UnicodeEncodeError:
        print(doc_text)

    return str(text)

def remove_accents(text):
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")
    return text