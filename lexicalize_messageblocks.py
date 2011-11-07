#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <arne-neumann@web.de>

"""
The C{lexicalize_messageblocks} module realizes message blocks which
consist of one or more messages.

lexicalize_ functions API:

lexicalize_codeexamples(examples, lexicalized_title,
                        lexicalized_plang=None, lexeme="enthalten")
lexicalize_exercises(exercises, lexicalized_title, lexeme="beinhalten")
lexicalize_keywords(keywords, lexicalized_title=None,
                    lexicalized_authors = None, realize="abstract",
                    lexeme="behandeln")
lexicalize_language(language, lexicalized_title, realize="noun")
lexicalize_pages(pages, lexicalized_title, lexeme="länge")
lexicalize_plang(plang, lexicalized_titles=None, lexicalized_authors=None,
                     realize="embedded")
lexicalize_target(target, lexicalized_title)
lexicalize_year(year, lexicalized_title)

only in lastbook_nomatch:
lexicalize_length(length, lexicalized_title,
                      lexicalized_lastbooktitle=None):

only in lastbook_nomatch / extra:
lexicalize_recency(recency, lexicalized_title,
                       lexicalized_lastbooktitle=None):
"""
import random
import cPickle as pickle # TODO: dbg, rm
from nltk.featstruct import Feature, FeatDict

from hlds import Diamond, create_diamond, add_mode_suffix
from lexicalization import *
from realization import OpenCCG #TODO: dbg, mv to main
from debug import gen_all_messages_of_type #TODO: dbg, rm

def load_all_textplans():
    f = open("data/alltextplans-20111028.pickle","r")
    return pickle.load(f)


def lexicalize_message_block(messageblock):
    msg_type = messageblock[Feature("msgType")]
    lexicalize_function_name = "lexicalize_" + msg_type
    return eval(lexicalize_function_name)(messageblock)


def lexicalize_authors_variations(authors):
    r"""
    lexicalize all the possible variations of author descriptions and put
    them in a dictionary, so other functions can easily choose one of them.

    @type authors_tuple: C{tuple} of (C{frozenset} of C{str}, C{str})
    @param author_tuple: tuple containing a set of names, e.g. (["Ronald
    Hausser", "Christopher D. Manning"]) and a rating, i.e. "neutral"

    @rtype: C{dict} of C{str}, C{Diamond} key-value pairs
    @return: "abstract" lexicalizes "der Autor" or "die Autoren", "complete"
    realizes a list of author names (incl. surname), and "lastnames" realizes
    a list of author last names.

    >>> authors_variations = lexicalize_authors_variations((frozenset(["Christopher Manning", "Alan Kay"]),""))
    >>> openccg.realize(authors_variations["complete"])
    ['Christopher Manning und Alan Kay', 'Christopher Mannings und Alan Kays']

    >>> openccg.realize(authors_variations["lastnames"])
    ['Manning und Kay', 'Mannings und Kays']

    >>> openccg.realize(authors_variations["abstract"])
    ['den Autoren', 'der Autoren', 'die Autoren']
    """
    authors_variations = {}
    for variation in ("abstract", "complete", "lastnames"):
        authors_variations[variation] = lexicalize_authors(authors,
                                                           realize=variation)
    return authors_variations

def lexicalize_title_variations(title, authors):
    r"""
    generates several book title lexicalizations and stores them in a C{dict}.
    
    @type title: C{tuple} of (C{str}, C{str})
    @param title: tuple containing a book title and a rating (neutral)
    @rtype: C{dict} of C{str}, C{Diamond} key-value pairs

    generate several different lexicalizations of book title / author
    combinations:
    >>> title_variations = lexicalize_title_variations(("Angewandte Computerlinguistik", ""), (set(["David Cole"]), ""))

    realize "das Buch":
    >>> openccg.realize(title_variations["abstract"])
    ['das Buch', 'dem Buch', 'des Buches']

    realize "es" (in the meaning of "it" / "the book"):
    >>> openccg.realize(title_variations["pronoun"])
    ['es', 'ihm', 'seiner']

    realize "$booktitle":
    >>> openccg.realize(title_variations["complete"])
    ['\xe2\x80\x9e Angewandte_Computerlinguistik \xe2\x80\x9c']

    realize "$fullname's $booktitle":
    >>> openccg.realize(title_variations["title+complete-names-possessive"])
    ['David Coles \xe2\x80\x9e Angewandte_Computerlinguistik \xe2\x80\x9c']

    realize "$lastname's $booktitle":
    >>> openccg.realize(title_variations["title+lastnames-possessive"])
    ['Coles \xe2\x80\x9e Angewandte_Computerlinguistik \xe2\x80\x9c']

    realize "$booktitle von $fullname":
    >>> openccg.realize(title_variations["title+complete-names-preposition"])
    ['\xe2\x80\x9e Angewandte_Computerlinguistik \xe2\x80\x9c von David Cole']

    realize "$booktitle von $lastname":
    >>> openccg.realize(title_variations["title+lastnames-preposition"])
    ['\xe2\x80\x9e Angewandte_Computerlinguistik \xe2\x80\x9c von Cole']

    realize "das Buch von $fullname":
    >>> openccg.realize(title_variations["abstract-title+complete-names-preposition"])
    ['das Buch von David Cole', 'dem Buch von David Cole', 'des Buches von David Cole']

    realize "das Buch von $lastname":
    >>> openccg.realize(title_variations["abstract-title+lastnames-preposition"])
    ['das Buch von Cole', 'dem Buch von Cole', 'des Buches von Cole']
    """
    title_variations = {} #"abstract", "complete", "pronoun" or "authors+title"
    for variation in ("abstract", "complete", "pronoun"):
        title_variations[variation] = lexicalize_title(title,
                                                       realize=variation)

    authors_variations = lexicalize_authors_variations(authors)

    # Noam Chomskys „On Syntax“
    title_variations["title+complete-names-possessive"] = \
        lexicalize_title(title, authors_variations["complete"],
                         realize="complete", authors_realize="possessive")
    # Chomskys „On Syntax“
    title_variations["title+lastnames-possessive"] = \
        lexicalize_title(title, authors_variations["lastnames"],
                         realize="complete", authors_realize="possessive")
    # „Buchtitel“ von Christopher Manning und Alan Kay
    title_variations["title+complete-names-preposition"] = \
        lexicalize_title(title, authors_variations["complete"],
                         realize="complete", authors_realize="preposition")
    # „Buchtitel“ von Manning und Kay
    title_variations["title+lastnames-preposition"] = \
        lexicalize_title(title, authors_variations["lastnames"],
                         realize="complete", authors_realize="preposition")
    # das Buch von Christopher Manning und Alan Kay
    title_variations["abstract-title+complete-names-preposition"] = \
        lexicalize_title(title, authors_variations["complete"],
                         realize="abstract", authors_realize="preposition")
    # das Buch von Manning und Kay
    title_variations["abstract-title+lastnames-preposition"] = \
        lexicalize_title(title, authors_variations["lastnames"],
                         realize="abstract", authors_realize="preposition")

    return title_variations


def lexicalize_id(id_message_block):
    r"""
    pass all the messages directly to their respective lexicalization
    functions.

    TODO: random dict key
    """
    author_variations = id_message_block["authors"]
    title_variations = id_message_block["title"]
    
    if "year" in id_message_block:
        lexicalize_title_description(id_message_block["title"],
                                     id_message_block["authors"],
                                     id_message_block["year"])
    else:
        lexicalize_title_description(id_message_block["title"],
                                     id_message_block["authors"])

    identifiers = set(["title", "authors", "year"])
    for msg_name, msg in id_message_block.items():
        if isinstance(msg_name, Feature) or msg_name in identifiers:
            id_message_block.pop(msg_name)

    msg_names = id_message_block.keys()

    if "codeexamples" in msg_names:
        if "proglang" in msg_names:
            lexicalized_plang = lexicalize_plang(id_message_block["proglang"],
                                realize="embedded")
            print lexicalize_codeexamples(id_message_block["codeexamples"],
                                          lexicalized_plang,
                                          random_variation(title_variations),
                                          lexeme="random")
        else:
            print lexicalize_codeexamples(id_message_block["codeexamples"],
                                          random_variation(title_variations),
                                          lexeme="random")


def lexicalize_extra(extra_message_block):
    r"""
    außerdem / zusätzlich / hinzu kommt
    """
    pass

def lexicalize_lastbook_match(lastbook_match_message_block):
    r"""sowohl als auch / beide Bücher / gemeinsam ist beiden Büchern"""
    pass

def lexicalize_lastbook_nomatch(lastbook_nomatch_message_block):
    r"""im Gegensatz zu / wohingegen"""
    pass

def fake_lastbook_nomatch(lexicalized_lastbook_message, lexicalized_message):
    r"""
    dieses Buch _____, wohingegen das erste Buch ____

    >>> title = lexicalize_title(("foo", ""), realize="pronoun")
    >>> lasttitle = lexicalize_title(("Angewandte Computerlinguistik", ""), realize="complete")
    >>> lang = lexicalize_language("German", title, realize="noun")
    >>> lastlang = lexicalize_language("English", lasttitle, realize="adjective")
    >>> openccg.realize(fake_lastbook_nomatch(lastlang, lang))
    ['es ist auf Deutsch , wohingegen \xe2\x80\x9e Angewandte_Computerlinguistik \xe2\x80\x9c in englischer Sprache ist']
    """
    hs = lexicalized_message
    hs.change_mode("HS")

    vl = lexicalized_lastbook_message
    vl.change_mode("VL")

    ns = create_diamond("NS", "adversativ", "wohingegen", [vl])

    return create_diamond("", "subjunktion", "komma", [hs, ns])



def lexicalize_usermodel_match(usermodel_match_message_block):
    r"""erfüllt Anforderungen / entspricht ihren Wünschen"""
    pass

def lexicalize_usermodel_nomatch(usermodel_nomatch_message_block):
    r"""erfüllt (leider) Anforderungen nicht / entspricht nicht ihren
    Wünschen"""
    pass

def random_variation(lexicalization_dictionary):
    """
    @type lexicalization_dictionary: C{Dict}
    @param lexicalization_dictionary: a dictonary, where each key holds the
    name of a message and the value holds the corresponding C{Message}
    @rtype: a randomly chosen value from the given dictionary
    """
    return random.choice(lexicalization_dictionary.values())
