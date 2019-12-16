"""
Collection of functions used for Query Suggestion

query_suggestion.py
@author Aaron Smith, Grant Larsen
11/26/2019
"""
from .utils import get_levenshtein_distance, get_dice_coeff, get_stop_words
MAX_DIST = 2
NUM_ASSOCIATIONS = 10


# ---------------------------------------------------------------------------------
# Attempts to fix queries that don't match anything in the index.
#
# @input: terms: list of query terms
#         index: frequency dictionary to find new terms
#         doc_index: doc dictionary for word count
#         window_index: window dictionary to find new terms
#         dice_scores: dictionary to store dice_scores
# @output: fixed_terms: list of corrected terms
# ---------------------------------------------------------------------------------
def clean_terms(terms, index, doc_index):
    fixed_terms = []

    for term in terms:
        if term not in index:
            most_similar = get_most_similar(term, index, doc_index)
            if most_similar not in index and len(most_similar) > 2:
                for split in range(1, len(most_similar)):
                    half1 = most_similar[:split]
                    half2 = most_similar[split:]
                    if half1 in index and len(half1) > 2:
                        fixed_terms.append(half1)
                    if half2 in index and len(half2) > 2:
                        fixed_terms.append(half2)
            else:
                fixed_terms.append(most_similar)
        else:
            fixed_terms.append(term)
    return fixed_terms


# ---------------------------------------------------------------------------------
# find the term in the index that is the most likely replacement for a given
# query term that was not found in the index
#
# @input: term: string of bad term
#         adj_term: the term next in the query if more than one word
#         doc_index: dictionary of document frequency
#         window_index: dictionary of window frequency
#         dice_scores: dictionary to score dice scores
# @ouput: most_similar: string most likely to replace bad query term
# ---------------------------------------------------------------------------------
def get_most_similar(term, index, doc_index):
    most_similar = term
    most_similar_score = 0
    doc_count = len(doc_index)
    for word in index:
        if abs(len(word) - len(term)) <= MAX_DIST:
            if term == word:
                dist = 0
            else:
                dist = get_levenshtein_distance(term, word)
            if dist <= 3:
                if dist == 0:
                    similarity = 1.5
                else:
                    similarity = 1 - dist / len(word)
                usage = int(index[word]['count']) / doc_count
                score = similarity + usage
                if score > most_similar_score:
                    most_similar_score = score
                    most_similar = word

    return most_similar


# ---------------------------------------------------------------------------------
# find words associated with query term to use for query suggestion
#
# @input: word: query term to check association
#         terms: all the query terms from query
#         window_index: dictionary of window frequency
#         dice_scores: dice_scores of the query terms
# @output: associated_words: list of words best associated with the term
# ---------------------------------------------------------------------------------
def find_associations(word, terms, window_index, dice_scores):
    associated_words = []
    min_coeff = 0
    indexed_word = window_index[word]
    if word in dice_scores:
        dice_index = dice_scores[word]
    else:
        dice_index = None
    for term in window_index:
        if term not in terms and term not in get_stop_words():
            compared_term = window_index[term]
            if dice_index is not None and term in dice_index:
                dice_coeff = dice_index[term]
            else:
                dice_coeff = get_dice_coeff(indexed_word, compared_term)
            if dice_coeff > min_coeff:
                if len(associated_words) < NUM_ASSOCIATIONS:
                    associated_words.append((term, dice_coeff))
                    if len(associated_words) == NUM_ASSOCIATIONS:
                        associated_words = sorted(associated_words, key=lambda tup: tup[1], reverse=True)
                else:
                    for ind in range(0, NUM_ASSOCIATIONS):
                        if dice_coeff > associated_words[ind][1]:
                            associated_words.insert(ind, (term, dice_coeff))
                            del associated_words[-1]
                            break
                min_coeff = associated_words[-1][1]
    return associated_words


# ---------------------------------------------------------------------------------
# find word associations using dice score to give query suggestions
#
# @input: terms: list of query terms
#         window_index: dictionary of window frequencies
#         dice_scores: list of dice scores for the terms
# @output: similar_terms: list of associated words
# ---------------------------------------------------------------------------------
def get_additional_query_terms(terms, window_index, dice_scores):
    associations = {}

    for term in terms:
        for similiar in find_associations(term, terms, window_index, dice_scores):
            if similiar not in associations:
                associations[similiar[0]] = 0
            associations[similiar[0]] += similiar[1]

    similar_terms = []
    for term in associations:
        similar_terms.append((term, associations[term]))
    similar_terms = sorted(similar_terms, key=lambda tup: tup[1], reverse=True)
    return similar_terms
