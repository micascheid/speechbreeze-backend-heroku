import spacy
from sqlalchemy import text
from flask import Flask, request, jsonify
from flask_cors import CORS

from dotenv import load_dotenv
import os
import boto3
from deepgram import DeepgramClient, PrerecordedOptions
from botocore.exceptions import ClientError
from botocore.config import Config
from database import db
from database.models import Slp, Patient, Lsa
from blueprints.stripe_webhooks import stripe_bp
from blueprints.lsas import lsas_bp
from blueprints.org_users import org_bp
from blueprints.slp import slp_bp
from blueprints.patients import patients_bp
from blueprints.lsa import lsa_bp
load_dotenv()
from werkzeug.utils import secure_filename
# Environment variables
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
# AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
API_KEY = os.getenv("DG_API_KEY")
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
nlp = spacy.load("en_core_web_sm")


# Set the database URI for SQLAlchemy
def create_application():
    app = Flask(__name__)
    CORS(app)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.register_blueprint(stripe_bp, url_prefix='/stripe')
    app.register_blueprint(org_bp, url_prefix='/org-customers')
    app.register_blueprint(lsas_bp, url_prefix='/lsas')
    app.register_blueprint(slp_bp, url_prefix='/slp')
    app.register_blueprint(patients_bp, url_prefix='/patients')
    app.register_blueprint(lsa_bp, url_prefix='/lsa')

    with app.app_context():
        db.init_app(app)
    return app


app = create_application()


@app.route('/')
def index():
    return "<p>Alive and super duper duper well</p>"




@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file part'}), 400

    file = request.files['audio']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if 'lsa_id' not in request.form:
        return jsonify({'error': 'No LSA ID provided'}), 400

    lsa_id_str = request.form['lsa_id']
    transcription_automated = bool(request.form.get('transcription_automated', False))

    try:
        lsa_id = int(lsa_id_str)  # Convert to integer
    except ValueError:
        return jsonify({'error': 'Invalid LSA ID format'}), 400

    filename = secure_filename(file.filename)
    unique_filename = f"lsa_{lsa_id}_{filename}"

    # Upload the file to S3
    s3 = boto3.client(
        's3',
        # aws_access_key_id=AWS_ACCESS_KEY_ID,
        # aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_DEFAULT_REGION,
    )
    try:
        s3.upload_fileobj(file, S3_BUCKET_NAME, unique_filename)
        # Construct the URL of the uploaded file
        file_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_DEFAULT_REGION}.amazonaws.com/{unique_filename}"
    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to upload file'}), 500

    # Update the LSA entry with the new audio file URL
    if not Lsa.update_lsa_audio_url(lsa_id, file_url):
        return jsonify({'error': 'Failed to update LSA record'}), 400

    if transcription_automated:
        try:
            # Generate a pre-signed URL for the audio file
            s3_client = boto3.client('s3',
                                     # aws_access_key_id=AWS_ACCESS_KEY_ID,
                                     # aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                     region_name=AWS_DEFAULT_REGION,
                                     config=Config(signature_version='s3v4'))
            pre_signed_url = s3_client.generate_presigned_url('get_object',
                                                              Params={'Bucket': S3_BUCKET_NAME,
                                                                      'Key': unique_filename},
                                                              ExpiresIn=7200)  # URL expires in 1 hour

            # Create a Deepgram client using the API key
            deepgram = DeepgramClient(API_KEY)
            # Configure Deepgram options for audio analysis
            options = PrerecordedOptions(model="nova-2", smart_format=True)
            # Call the transcribe_url method with the audio payload and options
            response = deepgram.listen.prerecorded.v("1").transcribe_url({'url': pre_signed_url}, options)
            transcription = response["results"]["channels"][0]["alternatives"][0]["transcript"]
            print("TRANSCRIPTION", transcription)

            # Update the LSA entry with the new transcription
            if not Lsa.update_lsa_transcription(lsa_id, transcription):
                return jsonify({'error': 'Failed to update LSA transcription'}), 400

        except Exception as e:
            return jsonify({'error': 'Failed to transcribe audio'}), 500

    return jsonify({'file_url': file_url, 'message': f'File {filename} uploaded successfully and LSA updated'}), 200


@app.route('/get-audio-url', methods=['GET'])
def get_audio_url():
    lsa_id = request.args.get('lsa_id')
    audio_fileurl = Lsa.get_audiofile_url_by_id(int(lsa_id))

    if not audio_fileurl:
        return jsonify({'message': 'No audio file associated with the requested LSA'}), 200

    audio_filename = audio_fileurl.split('/')[-1]
    print("audifilename", audio_filename)
    try:
        # Generate a pre-signed URL for the audio file
        s3_client = boto3.client('s3',
                                 # aws_access_key_id=AWS_ACCESS_KEY_ID,
                                 # aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                 region_name=AWS_DEFAULT_REGION,
                                 config=Config(signature_version='s3v4'))

        pre_signed_url = s3_client.generate_presigned_url('get_object',
                                                          Params={'Bucket': S3_BUCKET_NAME,
                                                                  'Key': audio_filename},
                                                          ExpiresIn=7200)  # URL expires in 1 hour

        print("pre signed url", pre_signed_url)
        return jsonify({'url': pre_signed_url}), 200
    except ClientError as e:
        print(e)
        return jsonify({'error': 'Failed to generate pre-signed URL'}), 500


@app.route('/create-automated-transcription', methods=['GET'])
def create_automated_transcription():
    lsa_id = request.args.get('lsa_id')
    audio_fileurl = Lsa.get_audiofile_url_by_id(int(lsa_id))
    audio_filename = audio_fileurl.split('/')[-1]

    print("\n\naudiofileurl: ", audio_fileurl, "\n\n")
    try:
        # Generate a pre-signed URL for the audio file
        s3_client = boto3.client('s3',
                                 # aws_access_key_id=AWS_ACCESS_KEY_ID,
                                 # aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                 region_name=AWS_DEFAULT_REGION,
                                 config=Config(signature_version='s3v4'))

        pre_signed_url = s3_client.generate_presigned_url('get_object',
                                                          Params={'Bucket': S3_BUCKET_NAME,
                                                                  'Key': audio_filename},
                                                          ExpiresIn=7200)  # URL expires in 1 hour

        print("pre signed url", pre_signed_url)

    except ClientError as e:
        print(e)
        return jsonify({'error': 'Failed to generate pre-signed URL'}), 500

    AUDIO_URL = {
        "url": pre_signed_url
    }
    try:
        # STEP 1 Create a Deepgram client using the API key
        deepgram = DeepgramClient(API_KEY)

        # STEP 2: Configure Deepgram options for audio analysis
        options = PrerecordedOptions(
            model="nova-2",
            smart_format=True,
        )

        # STEP 3: Call the transcribe_url method with the audio payload and options
        response = deepgram.listen.prerecorded.v("1").transcribe_url(AUDIO_URL, options)

        # STEP 4: Print the response
        print(response.to_json(indent=4))

    except Exception as e:
        print(f"Exception: {e}")


@app.route('/get-transcription', methods=['GET'])
def get_transcription():
    lsa_id = request.args.get('lsaId')
    print('get-transcription', lsa_id)

    try:
        transcription = Lsa.get_transcription_by_id(int(lsa_id))

        return jsonify({'transcription': transcription})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": f"An error occurred retrieving patients lsa {lsa_id} transcription"}), 500


@app.route('/update-transcription/<int:lsa_id>', methods=['PATCH'])
def update_transcription(lsa_id):
    data = request.json

    update_values = ['{}=:{}'.format(field, field) for field, value in data.items() if value is not None]

    if not update_values:
        jsonify({'error': 'No valid fields provided for update'}), 400

    try:
        update_clause = ', '.join(update_values)
        query = text('UPDATE lsas SET {} WHERE lsa_id = :lsa_id'.format(update_clause))
        data['lsa_id'] = lsa_id
        db.session.execute(query, params=data)
        db.session.commit()
        return jsonify({'message': 'Lsa updated successfully'}), 201
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Failed to add Lsa"}), 500


if __name__ == "__main__":
    app.run()
