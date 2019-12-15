import os
import string
import time
import csv
import tarfile
import math

from bs4 import BeautifulSoup
from .utils import tokenize_doc, clean_text, format_text

COLLECTION_DIR = "mathIR\static\mathIR\MathTagArticles"
INDEX_DIR = "mathIR\static\indexTSV"
DOC_FILE_NAME = "doc_index.tsv"
INDEX_FILE_NAME = "wiki_index.tsv"
STEM_FILE_NAME = "wiki_stems.tsv"
POSITIONAL_INDEX_FILE_NAME = "wiki_positions.tsv"
BIGRAM_INDEX_FILE_NAME = "wiki_bigrams.tsv"
WINDOW_INDEX_FILE_NAME = "wiki_window_index.tsv"
ANCHOR_TEXT_INDEX_FILE_NAME = 'indices/anchor_text_index.tsv'
LINKED_FROM_INDEX = 'indices/linked_from_index.tsv'

WINDOW_SIZE = 25


def main():
    index_collection()

# def create_window_index_tsv():
#     index = {}
#     for filename in os.listdir(COLLECTION_DIR):
#         if filename.endswith(".tar.bz2"):
#             dir_name = str(int(filename[7:-8]))
#             formatted_filename = os.path.join(COLLECTION_DIR, filename)
#             tar = tarfile.open(formatted_filename, 'r:bz2')
#             for file in tar:
#                 if not file.name.endswith('.html'):
#                     continue
#
#                 html_file = tar.extractfile(file)
#                 content = html_file.read()
#                 soup = BeautifulSoup(content, 'html.parser')
#
#                 doc_id = dir_name + '-' + soup.title['offset']
#                 doc_index = {}
#                 clean_soup(soup, doc_index)
#                 doc_text = soup.get_text()
#                 words = format_doc(doc_text)
#                 window = 0
#                 for word_index in range(0, len(words), WINDOW_SIZE):
#                     max_ind = word_index + WINDOW_SIZE
#                     if max_ind >= len(words):
#                         max_ind = len(words)
#                     doc_index = {}
#                     index_doc(' '.join(words[word_index:max_ind]), doc_index)
#                     for token in doc_index:
#                         index_str = doc_id + ':' + str(window)
#                         if token not in index:
#                             index[token] = index_str
#                         else:
#                             index[token] += ('\t' + index_str)
#                     window += 1
#
#     # Write index to a file
#     with open(WINDOW_INDEX_FILE_NAME, 'w') as output_file:
#         for key in sorted(index.keys()):
#             line = "%s\t%d\t%s\n" % (key, len(index[key].split('\t')), index[key])
#             output_file.write(line)


def index_collection():
    index = {}
    anchor_text_index = {}
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
                doc_name = clean_text(soup.title.string)
                doc_ids[doc_title] = doc_id
                doc_index = {}
                doc_anchor_index = {}
                links_out = clean_soup(soup, doc_index, doc_anchor_index)
                for link in links_out:
                    if link not in link_index:
                        link_index[link] = []
                    link_index[link].append(doc_id)
                doc_text = soup.get_text()
                words = format_text(doc_text)

                tokenize_doc(words, doc_index)

                # merge document index with the corpus index
                for token in doc_index:
                    index_str = doc_id + ':' + str(doc_index[token])
                    if token not in index:
                        index[token] = []
                    index[token].append(index_str)

                for token in doc_anchor_index:
                    index_str = doc_id + ':' + str(doc_anchor_index[token])
                    if token not in anchor_text_index:
                        anchor_text_index[token] = []
                    anchor_text_index[token].append(index_str)

                doc_file_line = [doc_id, doc_title, doc_name, len(words)]
                for link in links_out:
                    doc_file_line.append(link)
                doc_file_lines.append(doc_file_line)
        else:
            continue

    fn = os.path.join(INDEX_DIR, DOC_FILE_NAME)
    with open(fn, 'w', newline='', encoding='utf-8') as doc_file:
        writer = csv.writer(doc_file, delimiter="\t")
        for file in doc_file_lines:
            new_line = file[:4]
            linked_docs = []
            for link in file[4:]:
                if link in doc_ids:
                    linked_docs.append(doc_ids[link])
            new_line.append(len(linked_docs))
            for link in linked_docs:
                new_line.append(link)
            writer.writerow(new_line)

    doc_count = len(doc_file_lines)
    fn = os.path.join(INDEX_DIR, INDEX_FILE_NAME)
    with open(fn, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.writer(output_file, delimiter='\t')
        for key in sorted(index.keys()):
            docs = index[key]
            num_docs = len(docs)
            idf = math.log(doc_count/num_docs)
            line = [key, idf, num_docs]
            for doc in docs:
                line.append(doc)
            writer.writerow(line)

    fn = os.path.join(INDEX_DIR, ANCHOR_TEXT_INDEX_FILE_NAME)
    with open(fn, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.writer(output_file, delimiter='\t')
        for key in sorted(anchor_text_index.keys()):
            docs = anchor_text_index[key]
            num_docs = len(docs)
            idf = math.log(doc_count/num_docs)
            line = [key, idf, num_docs]
            for doc in docs:
                line.append(doc)
            writer.writerow(line)

    fn = os.path.join(INDEX_DIR, LINKED_FROM_INDEX)
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


def clean_soup(soup, formula_index, anchor_text_index):
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
            link_string = link.string
            if link_string is not None:
                link_words = format_text(link_string)
                for word in link_words:
                    if word not in anchor_text_index:
                        anchor_text_index[word] = 1
                    else:
                        anchor_text_index[word] += 1
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


if __name__ == "__main__":
    main()
