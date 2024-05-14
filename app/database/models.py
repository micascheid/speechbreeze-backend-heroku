from app.extensions import db
from sqlalchemy import DECIMAL, Integer, Text, Boolean, Date, String, func, Enum, text, BigInteger
from typing import Optional
from app.utils import normalize_text
import copy


class OrgCustomer(db.Model):
    __tablename__ = 'org_customers'
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    org_code = db.Column(db.String(255), unique=True, nullable=False)
    stripe_id = db.Column(db.String(255))
    sub_start = db.Column(db.Integer)
    sub_end = db.Column(db.Integer)
    slps = db.Column(db.ARRAY(db.String))


class Slp(db.Model):
    __tablename__ = 'slps'
    slp_id = db.Column(db.String(255), primary_key=True)
    account_creation_epoch = db.Column(db.BigInteger, default=text("EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)"))
    free_trial_exp = db.Column(db.BigInteger, default=text("EXTRACT(EPOCH FROM CURRENT_TIMESTAMP + INTERVAL '30 days')"))
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False)
    sub_type = db.Column(db.Integer, default=0)
    stripe_id = db.Column(db.String(255), unique=True)
    sub_start = db.Column(db.Integer)
    sub_end = db.Column(db.Integer)
    org_id = db.Column(db.Integer)

    @staticmethod
    def check_slp_exist(uid):
        try:
            return Slp.query.filter_by(slp_id=uid).first()
        except Exception as e:
            print("Error in check_slp_exist:", e)
            return None

    @staticmethod
    def add_user(uid, email, name):
        exist_check = Slp.query.filter_by(slp_id=uid).first()
        if exist_check:
            return ValueError("An SLP with the given uid already exists")

        new_slp = Slp(slp_id=uid, email=email, name=name)
        db.session.add(new_slp)
        try:
            db.session.commit()
            return new_slp
        except Exception as e:
            db.session.rollback()
            raise Exception("Failed to add SLP to the database: " + str(e))

    @staticmethod
    def update_slp(**kwargs):
        slp_id = kwargs.pop('slp_id', None)
        email = kwargs.pop('email', None)

        try:
            if slp_id:
                slp = Slp.query.filter_by(slp_id=slp_id).first()
            elif email:
                slp = Slp.query.filter_by(email=email).first()
            else:
                raise ValueError("An 'slp_id' or 'email' must be provided")

            if not slp:
                raise ValueError("The SLP with the given identifier does not exist")

            for attr, value in kwargs.items():
                if hasattr(slp, attr):
                    setattr(slp, attr, value)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise Exception("Unable to update SLP" + str(e))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Patient(db.Model):
    __tablename__ = 'patients'
    patient_id = db.Column(db.Integer, primary_key=True)
    slp_id = db.Column(db.String(255), db.ForeignKey('slps.slp_id'), nullable=False)
    name = db.Column(db.String(255))
    age = db.Column(db.Integer)
    lsas = db.relationship('Lsa', backref='patient', lazy=True, cascade="all, delete-orphan")

    @staticmethod
    def add_patient(slp_id, name, age):
        new_patient = Patient(slp_id=slp_id, name=name, age=age)
        db.session.add(new_patient)
        db.session.commit()

    @staticmethod
    def get_patients(slp_id):
        return Patient.query.filter_by(slp_id=slp_id).all()

    @staticmethod
    def get_patient_for_delete(patient_id):
        return Patient.query.options(db.joinedload(Patient.lsas)).filter_by(patient_id=patient_id).first()

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Lsa(db.Model):
    __tablename__ = 'lsas'
    lsa_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(Integer, db.ForeignKey('patients.patient_id', ondelete='CASCADE'), nullable=False)
    name = db.Column(String(255))
    created_at = db.Column(db.BigInteger, nullable=False, default=db.func.extract('epoch', db.func.current_timestamp()))
    audiofile_url = db.Column(Text, nullable=True)
    audio_type = db.Column(Text, nullable=True)
    transcription = db.Column(Text)
    transcription_automated = db.Column(Boolean)
    transcription_final = db.Column(Boolean)
    mlu_sugar_morph_count = db.Column(Integer, nullable=True)
    mlu = db.Column(DECIMAL(10, 2))
    tnw = db.Column(Integer)
    wps = db.Column(DECIMAL(10, 2))
    cps = db.Column(DECIMAL(10, 2))


    @staticmethod
    def get_lsas_by_slp(slp_id):
        lsas = Lsa.query.join(Patient).filter(Patient.slp_id == slp_id).all()
        return lsas

    @staticmethod
    def create_lsa(patient_id, name, transcription_automated, audio_type):
        new_lsa = Lsa(patient_id=patient_id, name=name,
                      audiofile_url=None, transcription='', transcription_automated=transcription_automated,
                      transcription_final=False,
                      audio_type=audio_type, mlu_sugar_morph_count=0, mlu=0.0,
                      tnw=0, wps=0.0, cps=0.0)
        db.session.add(new_lsa)
        db.session.commit()
        return new_lsa

    @staticmethod
    def update_lsa_audio_url(lsa_id, new_audiofile_url):
        # Retrieve the LSA entry by its ID
        lsa_to_update = Lsa.query.get(lsa_id)
        if lsa_to_update:
            # Update the audiofile_url attribute
            lsa_to_update.audiofile_url = new_audiofile_url
            # Commit the changes to the database
            db.session.commit()
            return True
        else:
            # If the LSA entry was not found, return False
            return False

    @staticmethod
    def get_audiofile_url_by_id(lsa_id: int) -> Optional[str]:
        lsa_entry = Lsa.query.filter_by(lsa_id=lsa_id).first()
        if lsa_entry:
            return lsa_entry.audiofile_url
        else:
            return None

    @staticmethod
    def get_lsa_by_id(lsa_id):
        # Retrieve the LSA entry by its ID
        lsa_entry = Lsa.query.get(lsa_id)
        # If the LSA entry was found, return it
        if lsa_entry:
            return lsa_entry
        else:
            # If the LSA entry was not found, return None
            return None

    @staticmethod
    def get_transcription_by_id(lsa_id: int) -> Optional[str]:
        # Retrieve the LSA entry by its ID
        lsa_entry = Lsa.query.get(lsa_id)
        # If the LSA entry was found, return its transcription
        if lsa_entry:
            return lsa_entry.transcription
        else:
            # If the LSA entry was not found, return None
            return None

    @staticmethod
    def create_transcription(lsa_id: int, transcription: str) -> bool:
        # Retrieve the LSA entry by its ID
        lsa_to_update = Lsa.query.get(lsa_id)
        if lsa_to_update:
            # Update the transcription attribute
            normalized_transcription = normalize_text(transcription)
            lsa_to_update.transcription = normalized_transcription
            # Commit the changes to the database
            db.session.commit()
            return True
        else:
            # If the LSA entry was not found, return False
            return False

    @staticmethod
    def update_lsa_transcription(lsa_id, transcription):
        # Retrieve the LSA entry by its ID
        lsa_to_update = Lsa.query.get(lsa_id)
        if lsa_to_update:
            # Update the transcription attribute
            lsa_to_update.transcription = transcription
            # Commit the changes to the database
            db.session.commit()
            return True
        else:
            # If the LSA entry was not found, return False
            return False

    @staticmethod
    def update_lsa_results(lsa_id, **kwargs):
        lsa_to_update = Lsa.query.get(lsa_id)
        if lsa_to_update:
            for key, value in kwargs.items():
                if hasattr(lsa_to_update, key):
                    setattr(lsa_to_update, key, value)
            db.session.commit()
            return True
        else:
            return False

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Utterance(db.Model):
    __tablename__ = 'utterances'
    utterance_id = db.Column(db.Integer, primary_key=True)
    lsa_id = db.Column(db.Integer, db.ForeignKey('lsas.lsa_id'), nullable=False)
    utterance_text = db.Column(db.Text, nullable=False)
    utterance_order = db.Column(db.Integer, nullable=False)
    start_text = db.Column(db.Integer, nullable=False)
    end_text = db.Column(db.Integer, nullable=False)
    morph_sugar_count = db.Column(db.Integer, nullable=False)
    utterance_sugar_obj = db.Column(db.JSON)
    sentence = db.Column(Enum('true', 'false', 'unsure', name='sentence_status'), default='false', nullable=False)
    clause_count = db.Column(db.Integer, nullable=False)
    lsa = db.relationship('Lsa', backref=db.backref('utterances', cascade='all, delete-orphan'))

    @staticmethod
    def get_utterances(lsa_id):
        utterances = Utterance.query.filter_by(lsa_id=lsa_id).order_by(Utterance.utterance_order).all()
        return [utterance.to_dict() for utterance in utterances]

    @staticmethod
    def get_utterances_valid_sentence(lsa_id):
        utterances = Utterance.query.filter_by(lsa_id=lsa_id, sentence='true').all()
        return [utterance.to_dict() for utterance in utterances]

    @staticmethod
    def existence_check(lsa_id):
        count = db.session.query(func.count(Utterance.utterance_id)).filter_by(lsa_id=lsa_id).scalar()
        return count > 0

    @staticmethod
    def delete_utterances_by_lsa_id(lsa_id):
        Utterance.query.filter_by(lsa_id=lsa_id).delete()
        db.session.commit()

    @staticmethod
    def insert_utterances(lsa_id, utterances):
        for utterance_data in utterances:
            new_utterance = Utterance(
                lsa_id=lsa_id,
                utterance_text=utterance_data['utterance_text'],
                utterance_order=utterance_data['utterance_order'],
                start_text=utterance_data['start_text'],
                end_text=utterance_data['end_text'],
            )
            db.session.add(new_utterance)
        db.session.commit()

    @staticmethod
    def update_utterances_objs(utter_counted_objs):
        utterances = {
            utterance.utterance_id: utterance
            for utterance in Utterance.query.filter(Utterance.utterance_id.in_(utter_counted_objs.keys()))
        }

        # Update the objects
        for utterance_id, obj in utter_counted_objs.items():
            utterance = utterances.get(utterance_id)
            if utterance is not None:
                utterance.utterance_sugar_obj = obj
        db.session.commit()

    @staticmethod
    def update_mlu_sugar_count(morph_zero_count, lsa_id):
        lsa_to_update = Lsa.query.get(lsa_id)
        prev_count = lsa_to_update.mlu_sugar_morph_count
        utterance_count = db.session.query(func.count(Utterance.utterance_id)).filter_by(lsa_id=lsa_id).scalar()
        total_additional_morph_count = sum(word_dict['morph_count'] for utterance_obj in morph_zero_count.values() for
                                           word_dict in
                                           utterance_obj.values())
        morph_total = prev_count + total_additional_morph_count
        if lsa_to_update:
            lsa_to_update.mlu = morph_total / utterance_count
            lsa_to_update.mlu_sugar_morph_count = morph_total
            db.session.commit()
            return True
        else:
            return False

    @staticmethod
    def update_morph_zero(utterances_morph_zero, lsa_id):
        # Get all matching utterances
        utterances = {
            utterance.utterance_id: utterance
            for utterance in Utterance.query.filter(Utterance.utterance_id.in_(utterances_morph_zero.keys()))
        }

        # Iterate through utterances to update word details
        for utterance_id, words_data in utterances_morph_zero.items():
            utterance = utterances.get(int(utterance_id))  # Get the utterance object
            if utterance is not None:
                # Parse sugar object from database
                utterance_sugar_obj = copy.deepcopy(utterance.utterance_sugar_obj)
                for word_id, word_data in words_data.items():
                    # Update data and prepare it to be saved back
                    utterance_sugar_obj[word_id]["morph_count"] = word_data["morph_count"]
                # Update sugar object in database
                utterance.utterance_sugar_obj = utterance_sugar_obj
        db.session.commit()
        Utterance.update_mlu_sugar_count(utterances_morph_zero, lsa_id)

    @staticmethod
    def update_utterances(utterances_data, lsa_id):
        # Extract utterance IDs from the keys of the passed object
        utterance_ids = [utterance['utterance_id'] for utterance in utterances_data]

        # Query all matching utterances with the given lsa_id and utterance_ids
        utterances_query = db.session.query(Utterance).filter(
            Utterance.lsa_id == lsa_id,
            Utterance.utterance_id.in_(utterance_ids)
        )

        # Fetch all matching utterances as a list
        matching_utterances = utterances_query.all()

        # Create dictionary for fast access
        matching_utterances_dict = {u.utterance_id: u for u in matching_utterances}

        # Update utterances with new data
        for new_utterance in utterances_data:
            # Find matched utterance
            utterance = matching_utterances_dict.get(new_utterance['utterance_id'])

            if utterance is None:
                # Skip if no matching utterance found
                continue

            # Update fields of the utterance with new values
            for field, value in new_utterance.items():
                # Ensure to update allowed fields
                if field in ['utterance_text', 'utterance_order', 'start_text', 'end_text',
                             'morph_sugar_count', 'utterance_sugar_obj',
                             'sentence', 'clause_count']:
                    setattr(utterance, field, value)

        # Commit changes to the database
        db.session.commit()

    @classmethod
    def bulk_update(cls, utterancesObj):
        for utterance_id, update_dict in utterancesObj.items():
            cls.query.filter_by(utterance_id=int(utterance_id)).update(update_dict)
        db.session.commit()
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
