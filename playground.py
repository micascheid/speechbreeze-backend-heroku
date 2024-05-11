import requests
from textblob import TextBlob
from mlus_calculator import MLUSCalculator

from spellchecker import SpellChecker
import spacy
import re
nlp = spacy.load("en_core_web_sm")
spell = SpellChecker()

def is_misspelled(word):
    if word not in spell:
        return "Not a word"
    # TextBlob's spellcheck suggests corrections in the form of a list of (word, confidence) tuples.
    # We consider the word misspelled if the suggested correction differs from the original word.
    return "Word"

def sen_counter(transcription: str) -> int:
    doc = nlp(transcription)
    total_sentences = len(list(doc.sents))
    print(total_sentences)
    return total_sentences


def counter(words) -> int:
    return sum(list(d.values())[0] for d in words)


def rules_1():
    text = "The cake was eaten by the dog."
    text2 = "I went to the store with men where the cake was eaten."
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text2)
    for token in doc:
        print(token.pos_)
        # Irregular Past tense verbs
        # A.) Implement via AI: Ritualized reduplications (choo-choo)

        # B.) Irregular past tense verbs
        if token.pos_ == "VERB" and token.tag_ == "VBD":
            # Check if the lemma is different from the token text and does not simply add 'ed'
            if token.lemma_ != token.text and not (token.text.endswith('ed') or token.text.endswith('d')):
                print("Irreg past tense verb:", token.text)
        # C.)

        # D.)
        if token.pos_ == "AUX":
            print("aux verbs: ", token.text)
        # E.) Irregular plurals
        if token.pos_ == "NOUN" and token.tag_ == "NNS":
                    # Get the singular form of the noun
                    singular_form = token.lemma_
                    # Check if the actual text of the token does not end with 's' (simple check for irregularity)
                    if not singular_form + 's' == token.text.lower() and not singular_form + 'es' == token.text.lower():
                        print("irreg pluarl:", token.text)


def rules_2():
    nlp = spacy.load("en_core_web_sm")
    text = "He walks to school every day when he stopped. She writes in her journal every night."
    doc = nlp(text)
    morphology_count = {}
    for token in doc:

        # A.) Possesive nouns
        if token.tag_ == "POS":
            # The possessed noun is the previous token
            possessed_noun = doc[token.i - 1].text
            # Combine the noun and the possessive marker
            possessive_noun = possessed_noun + token.text
            # Count the morphology as 2
            morphology_count[possessive_noun] = 2

        # B.) Plural Nouns
        if token.pos_ == "NOUN" and token.morph.get("Number") == ["Plur"]:
            plural_noun = token.text
            # Count the morphology as 2
            morphology_count[plural_noun] = 2

        # C.) Third person singular present tense verbs (verb + s)
        if (token.pos_ == "VERB" and token.morph.get("Person") == ["3"] and token.morph.get("Tense") == ["Pres"] and
                token.morph.get("Number") == ["Sing"]):
            morphology_count[token.text] = 2

        # D.) Regular past tense verbs (verb + ed)
        if token.tag_ == "VBD" and token.text.endswith("ed"):
            morphology_count[token.text] = 2

        # E.) Present progressive verbs (verb + ing)

        if token.pos_ == "VERB" and token.tag_ == "VBG" and any(child.dep_ == "aux" and child.lemma_ == "be" for
                                                                child in token.head.children):
            morphology_count[token.text] = 2

    print(morphology_count)


def rules_3():
    # A.) Count each word in proper names as one
    text = "Alice and Bob went to Paris. They visited the Louvre Museum."
    doc = nlp(text)
    proper_names = [ent.text for ent in doc.ents if ent.label_ in ["PERSON", "ORG", "GPE"]]
    print(f"Proper names found: {proper_names}")


def rules_4(text):
    # A.) Additional bound morphemes to be counted as additional morphemes
    doc = nlp(text)
    morpheme_counts = {}
    for token in doc:
        word = token.text.lower()
        pos = token.pos_

        # Check for the various bound morphemes and increment the count
        morpheme_count = 1
        suf_count = suffix_check(word, pos, token)
        pref_count = prefix_count(word, pos)
        morpheme_count += suf_count + pref_count

        morpheme_counts[word] = morpheme_count
    return morpheme_counts


def rules_5():
    # A.) Count contractions (do n’t, I’ d, he’ s, we’ ll, they’ ve) as two morphemes
    text = "I'm feeling good because I've finished my work."
    doc = nlp(text)
    # Initialize a list to hold contractions
    contractions = []

    # Iterate through tokens in the doc
    contraction_patterns = ["'m", "'ve", "'d", "'ll", "'re", "'s", "n't"]

    # Iterate through tokens in the doc, except the last one to avoid index errors
    for i, token in enumerate(doc):
        # Check if the token text or its lowercase form is part of our contraction patterns
        if any(token.text.lower().endswith(pattern) for pattern in contraction_patterns):
            # Handle special case for "n't" which is clearly split into two tokens
            if token.text.lower() == "n't" and i > 0:
                contractions.append(f"{doc[i - 1].text}{token.text}")
            # For other contractions, consider the token itself as part of the contraction
            elif i > 0 and doc[i - 1].text.lower() in ["i", "you", "he", "she", "it", "we", "they"]:
                contractions.append(f"{doc[i - 1].text}{token.text}")
            else:
                # This case might not be strictly necessary depending on your contraction patterns,
                # but is here to demonstrate handling standalone contraction tokens
                contractions.append(token.text)
    print(contractions)


def prefix_count(word, pos):
    morpheme_count = 0

    # c.) Bound morpheme: dis-, POS: na
    if word.startswith("dis") and pos != "ADJ":
        morpheme_count += 1

    # j.) Bound morpheme: re-, POS: na
    elif word.startswith("re") and pos != "ADJ":
        morpheme_count += 1

    # m.) Bound morpheme: un-, POS: na
    elif word.startswith("un") and pos != "ADJ":
        morpheme_count += 1

    return morpheme_count


def suffix_check(word, pos, token):
    morpheme_count = 0
    # a.) Bound morpheme: -ing, POS: adjective, gerund
    if word.endswith("ing") and (pos == "ADJ" or pos == "VERB"):
        morpheme_count += 1

    # b.) Bound morpheme: -ly, POS: na
    elif word.endswith("ly"):
        morpheme_count += 1

    # d.) Bound morpheme: -er, POS: comparative
    elif word.endswith("er") and pos == "ADJ" and "Degree=Cmp" in token.morph:
        morpheme_count += 1

    # e.) Bound morpheme: -est, POS: Superlative
    elif word.endswith("est") and pos == "ADJ" and "Degree=Sup" in token.morph:
        morpheme_count += 1

    # f.) Bound morpheme: -ful, POS: na
    elif word.endswith("ful") and pos != "ADJ":
        morpheme_count += 1

    # g.) Bound morpheme: -ish, POS: na
    elif word.endswith("ish") and pos != "ADJ":
        morpheme_count += 1

    # h.) Bound morpheme: -ed, POS: adjective
    elif word.endswith("ed") and pos == "ADJ":
        morpheme_count += 1

    # i.) Bound morpheme: -ment, POS: na
    elif word.endswith("ment") and pos != "ADJ":
        morpheme_count += 1

    # k.) Bound morpheme: -y
    elif word.endswith("y") and pos != "ADJ":
        morpheme_count += 1

    # l.) Bound morpheme: -sion, -tion, POS: na
    elif (word.endswith("sion") or word.endswith("tion")) and pos != "ADJ":
        morpheme_count += 1

    return morpheme_count


def mess_around():
    text = "what? I've only had"
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    for token in doc:
        print("INDEX:", token.i, ", TEXT:", token.text)


'''
Determining a sentence:

'''


def cps_calc(text):
    '''

    :return:
    '''
    nlp = spacy.load("en_core_web_sm")

    doc = nlp(text)
    [print(sent) for sent in doc.sents]


def classify_sentence(text):
    doc = nlp(text)
    # Check for the presence of a verb (including auxiliary verbs)
    has_verb = any(token.pos_ in ['VERB', 'AUX'] for token in doc)
    # Check for subjects or potential subjects
    potential_subjects = ['nsubj', 'nsubjpass', 'csubj', 'propn', 'acomp', 'dobj']

    # Identify if there are potential subjects based on broader criteria
    has_potential_subject = any(token.dep_ in potential_subjects for token in doc)

    # Basic criteria for being a definite sentence
    if has_verb and has_potential_subject:
        return True
    # Criteria for being likely not a sentence
    elif not has_verb:
        return False
    # Cases where it's ambiguous or doesn't clearly meet either criteria
    else:
        return "unsure"

dummy_text = ['Where is princess', 'What is that', 'So we can beep it so it can spin', 'So it can do this',
              'Spin it', 'Where is blankey', 'No', 'Oh food', 'My pillow', 'Where is blankey', 'What do you want to eat', "Then maybe you should've cook it", 'Bring it in the oven', 'We need plate', "Where's pizza plate", 'We got to time it', "Where's the timer", 'Maybe I could time', 'Can I do it', 'Where is it', 'Does it open', 'Can I cook it', 'Yea', 'So you can eat it', 'Maybe it', 'I can do it', 'Can we call somebody', 'How you take pictures', 'Do movie', 'What is it', 'I can see it', 'We going to put it', 'I can put it', 'Put it in here', 'Why', 'Is that you', 'Who is this', 'My friend', 'Is this song', 'Will it come on', 'Can you turn it', 'Can I turn it up', 'Bobblehead', 'Then go', "I don't want to go", 'I want play with you', 'Where you going', 'I want play with that', 'I want play with that ball', "We can put in what's this"]

if __name__ == "__main__":
    texts = [
        "Where's pizza plate"  # Complete sentence
    ]
    for text in texts:
        print(f"'{text}': {classify_sentence(text)}")
