from flask import Blueprint, jsonify, request
from app.app import Lsa, Utterance
from app.app import mlus_calculator
import spacy
nlp = spacy.load("en_core_web_sm")
lsas_bp = Blueprint('lsas', __name__)


@lsas_bp.route('/<string:uid>', methods=['GET'])
def lsas(uid):
    slp_uid = uid

    try:
        lsas = Lsa.get_lsas_by_slp(slp_uid)
        lsas_list = [lsa.to_dict() for lsa in lsas]
        return jsonify(lsas_list)
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An error occurred retrieving patients"}), 500


@lsas_bp.route('/<int:lsa_id>/utterances/batch-update', methods=['PUT'])
def utterances_batch_update(lsa_id):
    utterances = request.json.get('utterances')
    print("utterances", utterances)
    if utterances is None:
        return jsonify({"error": "Invalid utterances"}), 400
    try:
        existing = Utterance.existence_check(lsa_id)

        Utterance.delete_utterances_by_lsa_id(lsa_id)
        Utterance.insert_utterances(lsa_id=lsa_id, utterances=utterances)
        if existing:
            return jsonify({"message": "Utterances batch-update successful"}), 200
        else:
            return jsonify({"message": "Utterances batch-created successful"}), 201
    except Exception as e:
        print(f"Failed to save utterances: {e}")
        return jsonify({"error": "Failed to batch-update utterances"}), 500


@lsas_bp.route('/<int:lsa_id>/utterances/get', methods=['GET'])
def utterances_get(lsa_id):
    try:
        utterances = Utterance.get_utterances(lsa_id)

        return jsonify({'utterances': utterances})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": f"An error occurred retrieving patients lsa {lsa_id} utterances"}), 500


@lsas_bp.route('/<int:lsa_id>/crunch-results-mlu-tnw', methods=['POST'])
def crunch_results_mlu_tnw(lsa_id):
    try:
        # Get utterances
        utterances = Utterance.get_utterances(lsa_id)
        sent_list = []
        [sent_list.append(utt['utterance_text']) for utt in utterances]
        print(sent_list)
        utterances_total = len(utterances)
        transcription = Lsa.get_transcription_by_id(lsa_id)
        morph_total, morph_zero = mlu_sugar_calc(utterances)
        tnw = tnw_calc(transcription)
        mlu = (morph_total/utterances_total)


        # Update the fields in the Lsa model
        Lsa.update_lsa_results(lsa_id, mlu_sugar_morph_count=morph_total, mlu=mlu, tnw=tnw)
        if morph_zero:
            return jsonify({"message": "Speechbreeze was unable to calculate morphemes for the following:",
                            "morph_zero": morph_zero})
        return jsonify({"message": "Captain Crunch ain't got nothing on your newly crunched data", "morph_zero":
            morph_zero})
    except Exception as e:
        print(f"An error occurred mlu-tnw:", e)
        return jsonify({"error": "Failed to crunch results"}), 500


@lsas_bp.route('/lsas/<int:lsa_id>/morph-zero-update', methods=['POST'])
def morph_zero_update(lsa_id):
    try:
        utterances = request.json.get('utterances')
        Utterance.update_morph_zero(utterances, lsa_id)
        return jsonify({"message": "success"}), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "Unable to save corrected morphemes"}), 500


@lsas_bp.route('/lsas/<int:lsa_id>/crunch-results-wps-cps', methods=['POST'])
def crunch_results_wps_cps(lsa_id):
    try:
        utterances = Utterance.get_utterances(lsa_id)
        utterances_for_review, utterance_to_commit = filter_utterances_for_review(utterances)
        Utterance.update_utterances(utterances, lsa_id)

        return jsonify({'message': "Please modify provide clause amount for the following utterances",
                       "utterances_for_review": utterances_for_review}), 200
    except Exception as e:
        message = f"Error with WPS and CPS analysis: {e}"
        print(message)
        return jsonify({'error': message}), 500


@lsas_bp.route('/lsas/<int:lsa_id>/utterances-wps-cps-save', methods=['POST'])
def save_wps_cps(lsa_id):
    try:
        utterances = request.json.get('utterances')
        Utterance.bulk_update(utterances)
        #calculate new wps and cps and update lsa
        wps, cps = wps_cps_calc(lsa_id)
        Lsa.update_lsa_results(lsa_id, wps=wps, cps=cps)
        return jsonify({"message": "success"}), 200
    except Exception as e:
        message = f"Error updating reviewed WPS and CPS data: {e}"
        print(message)
        return jsonify({"error": message}), 500


def mlu_sugar_calc(utterances) -> tuple:
    mlus = mlus_calculator.MLUSCalculator(utterances)
    count, utterances_counted = mlus.morpheme_madness()
    morph_zero = morph_count_zero_check(utterances_counted)
    try:
        #commit utterance_counted to db
        Utterance.update_utterances_objs(utterances_counted)
    except Exception as e:
        raise Exception("mlu_sugar_calc function failed: ", e)
    return count, morph_zero

def wps_cps_calc(lsa_id) -> (float, float):
    utterances = Utterance.get_utterances_valid_sentence(lsa_id)
    sentence_count = len(utterances)
    clause_count = sum(utterance['clause_count'] for utterance in utterances)
    word_count = sum(len(utterance['utterance_text'].split()) for utterance in utterances)

    if sentence_count == 0:
        return 0.0, 0.0

    wps = word_count/sentence_count
    cps = clause_count/sentence_count

    return wps, cps

def morph_count_zero_check(utterances_counted):
    result = {}
    for utterance_id, utterances_obj in utterances_counted.items():
        filtered_for_zero = {word_id: word_data for word_id, word_data in utterances_obj.items() if word_data[
            'morph_count'] == 0}
        if filtered_for_zero:
            result[utterance_id] = filtered_for_zero
    return result

def tnw_calc(transcription) -> int:
    return len(transcription.split())

def filter_utterances_for_review(utterances) -> (dict, dict):

    # Utterances to commit are ones that are either not sentences or sentences with 1 clause
    utter_to_commit = {}

    # Utterances to be sent to the client to proivde clause or sentence feedback on
    utter_to_review = {}

    #1.) Determining if they're sentences
    for utter in utterances:
        is_sentence = 'unsure'
        doc = nlp(utter['utterance_text'])
        # Check for the presence of a verb (including auxiliary verbs)
        has_verb = any(token.pos_ in ['VERB', 'AUX'] for token in doc)
        # Check for subjects or potential subjects
        potential_subjects = ['nsubj', 'nsubjpass', 'csubj', 'propn', 'acomp', 'dobj']

        # Identify if there are potential subjects based on broader criteria
        has_potential_subject = any(token.dep_ in potential_subjects for token in doc)

        clause_count = 1 if has_one_clause(doc) else 0
        # Basic criteria for being a definite sentence
        if has_verb and has_potential_subject and clause_count == 1:
            utter['clause_count'] = clause_count
            utter['sentence'] = 'true'
            utter_to_commit[utter['utterance_id']] = utter
        # Criteria for being likely not a sentence
        elif not has_verb:
            is_sentence = 'false'
            clause_count = 0
            utter['clause_count'] = clause_count
            utter_to_review[utter['utterance_id']] = utter
        else:
            is_sentence = 'unsure'
            clause_count = 0
            utter['clause_count'] = clause_count
            utter['sentence'] = is_sentence
            utter_to_review[utter['utterance_id']] = utter

        # Cases where it's ambiguous or doesn't clearly meet either criteria
    # 2 Of those that are sentences identify if they have 1 clause


    # print(total_sentences)
    return utter_to_review, utter_to_commit


def has_one_clause(sentence) -> bool:
    root_count = 0
    for token in sentence:
        if token.dep_ == "ROOT":
            root_count += 1
        if token.dep_ == "cc":
            return False
    return root_count > 1