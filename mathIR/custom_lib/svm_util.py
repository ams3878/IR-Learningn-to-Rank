import os
import csv
import math
import sys

from .utils import get_index, get_docs_index, format_text
from sklearn import svm


TRAINING_DATA_FILE_NAME = 'training_data.tsv'
SVM_RESULTS_FILE_NAME = 'weight_vector.tsv'


def main():
    doc_index = get_docs_index()
    index = get_index()
    anchor_index = get_index(anchor=True)
    train_svm(doc_index, index, anchor_index)


def make_training_data_file():
    dirs = [x[0] for x in os.walk('rel_data')]
    training_data_lines = []
    for dir in dirs[1:]:
        with open(os.path.join(dir, 'queries.txt'), 'r', encoding='utf-8') as query_file:
            for q_count in range(1, 6):
                terms = query_file.readline().strip().lower()
                fn = 'q%d.qrel' % q_count
                with open(os.path.join(dir, fn), 'r', encoding='utf-8') as qrel:
                    for qrel_line in qrel:
                        qrel_line = qrel_line
                        print(qrel_line)
                        if '\t' in qrel_line:
                            rels = qrel_line.split('\t')
                        else:
                            rels = qrel_line.split()
                        line = [terms, rels[-2], rels[-1]]
                        training_data_lines.append(line)

    with open(TRAINING_DATA_FILE_NAME, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.writer(output_file, delimiter='\t')
        writer.writerows(training_data_lines)


def train_svm(doc_index, index, anchor_index):
    features = []
    rels = []
    with open(TRAINING_DATA_FILE_NAME, 'r', encoding='utf-8') as data_file:
        line = data_file.readline()
        line = line.split('\t')
        while line:
            query_text = line[0]
            doc_ids = [line[1]]
            rels.append(int(line[2].strip()))
            next_line = data_file.readline()
            while next_line:
                next_line = next_line.split('\t')
                if next_line[0] != query_text:

                    break
                doc_ids.append(next_line[1])
                rels.append(int(line[2].strip()))
                next_line = data_file.readline()

            query_features = get_features(format_text(query_text), doc_ids, doc_index, index, anchor_index)
            for feature in query_features:
                features.append(feature)
            line = next_line
    svm_model = svm.LinearSVC(max_iter=2000)
    svm_model.fit(features, rels)
    relevant_weights = list(svm_model.coef_[2])
    with open(SVM_RESULTS_FILE_NAME, 'w') as weight_file:
        csv.writer(weight_file, delimiter='\t').writerow(relevant_weights)

    return relevant_weights


def get_features(query_words, doc_ids, doc_index, index, anchor_index):
    features = [[0 for x in range(0, 5)] for i in range(0, len(doc_ids))]
    if len(doc_ids) < len(doc_index):
        bm25_results = query(query_words, anchor_index, doc_index, None, None, 'bm25', limit_to=doc_ids)
    else:
        bm25_results = query(query_words, anchor_index, doc_index, None, None, 'bm25')
    results_dict = {}
    for result in bm25_results:
        results_dict[result[0]] = result
    num_query_terms = len(query_words)
    for doc in range(0, len(doc_ids)):
        doc_id = doc_ids[doc]
        if doc_id in results_dict:
            result = results_dict[doc_id]
            features[doc][0] = result[2]
            features[doc][1] = similarity(query_words, result[1])
        features[doc][2] = doc_index[doc_id]['page_rank']
        for term in query_words:
            if term in index:
                features[doc][3] += get_term_frequency(term, index, doc_id)
                features[doc][4] += index[term]['idf']
        features[doc][3] /= num_query_terms
        features[doc][4] /= num_query_terms
    return features


def get_term_frequency(term, index, doc_id):
    try:
        term_count = index[term]['docs'][doc_id]
        return math.log(term_count+1)
    except KeyError:
        return 0.0


def similarity(query_words, doc_title):
    num_in_title = 0
    doc_title_words = doc_title.split()
    for word in query_words:
        if word in doc_title_words:
            num_in_title += 1
    return num_in_title/len(query_words)


if __name__ == '__main__':
    main()
