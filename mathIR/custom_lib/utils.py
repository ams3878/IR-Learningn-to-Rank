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
from math import ceil
from ..models import *
from nltk.tokenize import word_tokenize

INDEX_FILENAME = 'ponyportal\static\ponyportal\mlp_index.tsv'
WINDOW_INDEX_FILENAME = 'ponyportal\static\ponyportal\mlp_window_index.tsv'
DOC_INDEX_FILENAME = 'ponyportal\static\ponyportal\doc_names.tsv'


# ---------------------------------------------------------------------------------
# creates all the episodes files needed for indexing
#
# @input: master: html file of all the episodes
#         ep_loc: a directory to store the files
# @return: None
# ---------------------------------------------------------------------------------
def create_episode_files(master, ep_loc):
    f = open(master)
    line = f.readline()
    line_list = line.split('>')

    count = 0
    while line:
        meta = "meta[ "
        script = ''
        script_tag = ''
        script_html = ''
        try:
            if line_list[0].split()[0] == '<h2':
                count += 1
                line_count = 0
                title = line_list[2][:-3]
                meta = meta + "title:" + title
                line = f.readline()
                line_list = line.split('>')
                while line:
                    try:
                        if line_list[0].split()[0] == '<h2':
                            break
                    except IndexError:
                        pass
                    if line != '':
                        clean_line = cleanhtml(line)
                        script_html = script_html + line
                        if clean_line[1] != '\n':
                            line_count += 1
                            script_tag = script_tag + clean_line[1]
                        if clean_line[0] != '\n':
                            script = script + '\t' + clean_line[0]
                    line = f.readline()
                    line_list = line.split('>')
                meta = meta + ', lines: ' + str(line_count) + "]\n"
                f_new_tags = open(ep_loc[:-1] + "_tags\\" + str(count), 'w')
                f_new_tags.write(meta)
                f_new_tags.write(script_tag)
                f_new_tags.close()
                f_new_html = open(ep_loc[:-1] + "_html\\" + str(count) + '.html', 'w')
                f_new_html.write(meta)
                f_new_html.write(script_html)
                f_new_html.close()
                f_new = open(ep_loc + str(count), 'w')
                f_new.write(meta)
                f_new.write(script)
                f_new.close()
                season = get_season(count)
                season_obj = Season.objects.filter(id=season)
                if not season_obj:
                    q = Season(id=season)
                    q.save()
                    season_obj = Season.objects.filter(id=season)
                doc_obj = Document.objects.filter(id=count)
                if not doc_obj:
                    if season >= 10:
                        script_type = 'feature'
                    else:
                        script_type = 'episode'
                    q = Document(id=count,
                                 title=title,
                                 script_type=script_type,
                                 )
                    q.save()
                    doc_obj = Document.objects.filter(id=count)
                season_doc_obj = SeasonToDocument.objects.filter(episode=doc_obj[0], season=season_obj[0])
                if not season_doc_obj:
                    q = SeasonToDocument(episode=doc_obj[0], season=season_obj[0])
                    q.save()
                f_new.close()

        except IndexError:
            pass
    f.close()


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
def get_index(filename):
    index = {}
    with open( 'ponyportal\static\ponyportal\\' + filename, 'r') as index_file:
        line = index_file.readline()
        while line:
            line = line.split('\t')
            posting_list = line[2:]
            posting_dict = {'docs': {}}
            for posting in posting_list:
                posting = posting.split(':')
                posting_dict['docs'][posting[0]] = int(posting[1])
            posting_dict['count'] = str(line[1])
            index[line[0]] = posting_dict

            line = index_file.readline()
    return index


# ---------------------------------------------------------------------------------
# create an index from a tsv with the frequcency of words in  document windows
# window size is set to be one line
# @input: None
# @output: index: dictionary
# ---------------------------------------------------------------------------------
def get_window_index():
    index = {}
    with open(WINDOW_INDEX_FILENAME, 'r') as index_file:
        line = index_file.readline()
        while line:
            line = line.split('\t')
            posting_list = line[2:]
            posting_dict = {'count': int(line[1])}
            for posting in posting_list:
                posting = posting.split(':')
                if posting[0] not in posting_dict:
                    posting_dict[posting[0]] = []
                posting_dict[posting[0]].append(int(posting[1]))
            index[line[0]] = posting_dict

            line = index_file.readline()
    return index


# ---------------------------------------------------------------------------------
# create an index from a tsv mapping episdoe number to title, word count
# and line count
#
# @input: None
# @output: doc_index: dictionary
# ---------------------------------------------------------------------------------
def get_docs_index():
    doc_index = {}
    with open(DOC_INDEX_FILENAME, 'r') as doc_file:
        line = doc_file.readline()
        while line:
            line = line.split('\t')
            doc_index[line[0]] = (line[1], line[2])
            line = doc_file.readline()
    return doc_index


# ---------------------------------------------------------------------------------
# create an index from a tsv with the stems and their associated words
#
# @input: filename: tsv of stems
# @output: stems: dictionary
# ---------------------------------------------------------------------------------
def get_stems(filename):
    stems = {}
    with open('ponyportal\static\ponyportal\\' + filename, 'r') as stem_file:
        line = stem_file.readline()
        while line:
            line = line.split('\t')
            stems[line[0]] = line[1:-1]
            line = stem_file.readline()
    return stems


# ---------------------------------------------------------------------------------
# removes all html tags from a document, and adds "%%" tag on speakers
#
# @input: raw_html: string of txt to be cleaned
# @output: cleantext: text without tags
#          taggedtext: text with names tagged
# ---------------------------------------------------------------------------------
def cleanhtml(raw_html):
    find_name = re.compile('</dd><dd><b>.*?</b>')

    temp = re.match(find_name, raw_html)
    tagged = raw_html
    if temp:
        match = temp.group(0).split('<b>')[1].split('</b>')[0]
        tagged = re.sub(find_name, '%%' + match + '%%',  raw_html)

    cleanr = re.compile('<.*?>')
    taggedtext = re.sub(cleanr, '', tagged)
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext, taggedtext


# ---------------------------------------------------------------------------------
# Creates characters by looking at the tagged HTML and adds them to Django model
#
# @input: None
# @ouput: None
# ---------------------------------------------------------------------------------
def create_new_chars():
    chars_set = list(Character.objects.all())
    chars = []
    for c in chars_set:
        chars.append(c.id)
    for i in range(243):
        f = open('ponyportal\static\episodes_tags\\' + str(i+1))
        meta = f.readline()
        line = f.readline()
        while line:
            try:
                findname = re.compile('%%.*?%%')
                temp = re.match(findname, line)

                if temp:
                    name = temp.group(0)[2:-2]
                    char = re.sub(r'\bbut.*', '', name)
                    char = re.sub(r'\bexcept.*', '', char)
                    char = (re.sub(r'\band\b', ',', char)).split(',')
                    for c in char:
                        if c not in chars:
                            q = Character(id=re.sub(r'[^\w\s]', '', c))
                            q.save()
                            chars.append(c)
            except IndexError:
                pass
            line = f.readline()


# ---------------------------------------------------------------------------------
# Creates Documents for each episodes, and adds the Character relation if they
# appear in that episode
#
# @input: None
# @ouput: None
# ---------------------------------------------------------------------------------
def create_char_episode():
    for i in range(243):
        f = open('ponyportal\static\episodes\\' + str(i+1))
        line = f.readline()
        meta = f.readline()
        doc_obj = Document.objects.filter(id=i + 1)[0]
        while line:
            try:
                findname = re.compile('%%.*?%%')
                temp = re.match(findname, line)

                if temp:
                    name = temp.group(0)[2:-2]
                    char = name.split('and')
                    if len(char) > 1 and char[1]:
                        char_name = re.sub(r'\W+', '', char[1])
                        char_obj = Character.objects.filter(id=char_name)[0]
                        if not CharacterToDocument.objects.filter(character=char_obj, episode=doc_obj):
                            q = CharacterToDocument(character=char_obj, episode=doc_obj)
                            q.save()
                    char = char[0].split(',')
                    for c in char:
                        char_name = re.sub(r'\W+', '', c)
                        char_obj = Character.objects.filter(id=char_name)[0]
                        if not CharacterToDocument.objects.filter(character=char_obj, episode=doc_obj):
                            char_obj = Character.objects.filter(id=char_name)[0]
                            doc_obj = Document.objects.filter(id=i+1)[0]
                            q = CharacterToDocument(character=char_obj, episode=doc_obj)
                            q.save()
            except IndexError:
                pass
            line = f.readline()


# ---------------------------------------------------------------------------------
# Creates Season django models and adds relations for the episodes to seasons
#
# @input: None
# @ouput: None
# ---------------------------------------------------------------------------------
def get_season(episode):
    if episode <= 52:
        return ceil(episode / 26)
    elif episode <= 65:
        return 3
    elif episode <= 221:
        return 3 + ceil((episode - 65) / 26)
    elif episode <= 239:
        return 10
    else:
        return episode - 239 + 10


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