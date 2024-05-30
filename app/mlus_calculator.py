import random
import spacy
from spellchecker import SpellChecker
import re
class MLUSCalculator:
    def __init__(self, utterances):
        self.utterances = utterances

    def morpheme_calc(self):
        return random.randint(0,10)

    def morpheme_madness(self):
        # [{'utterance_id': 101, 'lsa_id': 17, 'utterance_text': "he's always there, and I always see him there",
        # 'utterance_order': 0, 'start': 33, 'end': 78},]
        # {<word>:{word: <word>, morph_count: <int>}}
        utter_counted = {}
        nlp = spacy.load("en_core_web_sm")
        for index, utter in enumerate(self.utterances):
            utter_obj = self.utterance_text_to_obj(utter)
            doc = nlp(utter['utterance_text'])
            utter_obj = self.rules_1(doc, utter_obj)
            utter_obj = self.rules_2(doc, utter_obj)
            utter_obj = self.rules_3(doc, utter_obj)
            utter_obj = self.rules_4(doc, utter_obj)
            utter_obj = self.rules_5(doc, utter_obj)
            self.check_spelling(utter_obj)
            utter_counted[utter['utterance_id']] = utter_obj

        total_morph_count = sum(word_dict['morph_count'] for utterance_obj in utter_counted.values() for word_dict in utterance_obj.values())
        return total_morph_count, utter_counted

    @staticmethod
    def check_spelling(utter_obj):
        spell = SpellChecker()
        single_letter_words = {'i', 'a'}
        for item in utter_obj:

            word_obj = utter_obj[item]
            word = word_obj['word'].lower()
            if word in single_letter_words:
                word_obj['morph_count'] = 1
                continue

            if utter_obj[item]['rule'] not in [11, 13]:
                word_obj = utter_obj[item]
                word = word_obj['word']
                if word not in spell:
                    word_obj['morph_count'] = 0


    @staticmethod
    def utterance_text_to_obj(utterance):
        result = {}
        words = re.findall(r"\b\w+(?:'\w+)?\b", utterance['utterance_text'])
        start_index = 0
        for index, word in enumerate(words):
            # Since we've already removed punctuation, we calculate end_index directly
            end_index = start_index + len(word)
            result[index] = {
                "word": word,
                "morph_count": 0,
                "start": start_index,
                "end": end_index,
                "rule": 0
            }
            start_index = end_index + 1  # Account for the space or punctuation now removed

        return result

    @staticmethod
    def find_utter_obj_index(token, utter_obj):
        for index, item in utter_obj.items():
            # Check if the token's character span overlaps with the item's span
            if item["start"] <= token.idx < item["end"]:
                return index
        return None

    @staticmethod
    def update_morph_count_if_higher(utter_obj, index, new_morph_count, rule):
        if index in utter_obj:
            # Retrieve the current morpheme count for the word at the specified index
            current_morph_count = utter_obj[index]['morph_count']
            # Update the morpheme count only if the new count is higher
            if new_morph_count > current_morph_count:
                utter_obj[index]['morph_count'] = new_morph_count
                utter_obj[index]['rule'] = rule

    def rules_1(self, doc, utter_obj):
        for token in doc:
            # Irregular Past tense verbs
            # A.) Implement via user_input: Ritualized reduplications (choo-choo)

            # B.) Irregular past tense verbs
            index = self.find_utter_obj_index(token, utter_obj)
            if index is not None:
                if token.pos_ == "VERB" and token.tag_ == "VBD":
                    # Check if the lemma is different from the token text and does not simply add 'ed'
                    if token.lemma_ != token.text and not (token.text.endswith('ed') or token.text.endswith('d')):
                        self.update_morph_count_if_higher(utter_obj, index, 1, 1)
                # C.)

                # D.)
                if token.pos_ == "AUX":
                    self.update_morph_count_if_higher(utter_obj, index, 1, 2)
                # E.) Irregular plurals
                if token.pos_ == "NOUN" and token.tag_ == "NNS":
                    # Get the singular form of the noun
                    singular_form = token.lemma_
                    # Check if the actual text of the token does not end with 's' (simple check for irregularity)
                    if not singular_form + 's' == token.text.lower() and not singular_form + 'es' == token.text.lower():
                        self.update_morph_count_if_higher(utter_obj, index, 1, 3)
        return utter_obj

    def rules_2(self, doc, utter_obj):
        morphology_count = {}
        for token in doc:
            index = self.find_utter_obj_index(token, utter_obj)
            if index is not None:
                # A.) Possesive nouns
                if token.tag_ == "POS":
                    # The possessed noun is the previous token
                    possessed_noun = doc[token.i - 1].text
                    # Combine the noun and the possessive marker
                    possessive_noun = possessed_noun + token.text
                    # Count the morphology as 2
                    self.update_morph_count_if_higher(utter_obj, index, 2, 4)

                # B.) Plural Nouns
                if token.pos_ == "NOUN" and token.morph.get("Number") == ["Plur"]:
                    plural_noun = token.text
                    # Count the morphology as 2
                    self.update_morph_count_if_higher(utter_obj, index, 2, 5)

                # C.) Third person singular present tense verbs (verb + s)
                if (token.pos_ == "VERB" and token.morph.get("Person") == ["3"] and token.morph.get("Tense") == ["Pres"] and
                        token.morph.get("Number") == ["Sing"]):
                    self.update_morph_count_if_higher(utter_obj, index, 2, 6)

                # D.) Regular past tense verbs (verb + ed)
                if token.tag_ == "VBD" and token.text.endswith("ed"):
                    self.update_morph_count_if_higher(utter_obj, index, 2, 7)

                # E.) Present progressive verbs (verb + ing)
                if token.pos_ == "VERB" and token.tag_ == "VBG" and any(child.dep_ == "aux" and child.lemma_ == "be" for
                                                                        child in token.head.children):
                    self.update_morph_count_if_higher(utter_obj, index, 2, 8)

        return utter_obj

    def rules_3(self, doc, utter_obj):
        # A.) Count each word in proper names as one

        for ent in doc.ents:  # Each 'ent' is a span representing a named entity.
            if ent.label_ in ["PERSON", "ORG", "GPE"]:
                # Iterate over each token in the span
                for token in ent:
                    index = self.find_utter_obj_index(token, utter_obj)
                    if index is not None:
                        self.update_morph_count_if_higher(utter_obj, index, 1, 9)

        return utter_obj

    def rules_4(self, doc, utter_obj):
        # A.) Additional bound morphemes to be counted as additional morphemes
        morpheme_counts = {}
        for token in doc:
            index = self.find_utter_obj_index(token, utter_obj)
            if index is not None:
                word = token.text.lower()
                pos = token.pos_

                # Check for the various bound morphemes and increment the count
                morpheme_count = 0
                suf_count = self.suffix_check(word, pos, token)
                pref_count = self.prefix_count(word, pos)
                morpheme_count += suf_count + pref_count + 1

                # Where I need to make modification
                self.update_morph_count_if_higher(utter_obj, index, morpheme_count, 10)

        return utter_obj

    def rules_5(self, doc, utter_obj):
        # A.) Count contractions (do n’t, I’ d, he’ s, we’ ll, they’ ve) as two morphemes
        # Initialize a list to hold contractions
        contraction_patterns = ["'m", "'ve", "'d", "'ll", "'re", "'s", "n't"]

        for token in doc:
            # Check if the token text or its lowercase form is part of our contraction patterns
            is_contraction_part = any(token.lower_.endswith(pattern) for pattern in contraction_patterns)
            if is_contraction_part:
                # Find the index in utter_obj that corresponds to this token
                index = self.find_utter_obj_index(token, utter_obj)

                # For "n't", the contraction is split into two tokens by SpaCy
                if token.lower_ == "n't" and index is not None:
                    # Since "n't" is always the second part of a contraction,
                    # increase the morph count for the token preceding "n't" as well
                    self.update_morph_count_if_higher(utter_obj, index, 2, 11)  # Update "not" part of the contraction


                # For other contraction patterns, ensure the entire contraction is counted as two morphemes
                elif index is not None:
                    # Update the morph count for the token
                    self.update_morph_count_if_higher(utter_obj, index, 2, 13)

        return utter_obj

    def prefix_count(self, word, pos):
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

    def suffix_check(self, word, pos, token):
        morpheme_count = 0
        # a.) Bound morpheme: -ing, POS: adjective, gerund
        if word.endswith("ing"):
            if (pos == "VERB" and token.morph.get('VerbForm') == ["Part"]) or pos == "NOUN":
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
        elif word.endswith("y") and pos == "ADJ":
            morpheme_count += 1

        # l.) Bound morpheme: -sion, -tion, POS: na
        elif (word.endswith("sion") or word.endswith("tion")) and pos != "ADJ":
            morpheme_count += 1

        return morpheme_count

