from flask import Flask, request, jsonify
from pcaka import init_user, cj_respond_handshake
from cryptography.fernet import Fernet
import boto3
from google.cloud import storage as gcp_storage
import logging
from auth import token_required
import json

app = Flask(__name__)

cj_private_key, cj_public_key = init_user()
shared_key_cj = None

logging.basicConfig(level=logging.INFO)

@app.route('/respond-handshake', methods=['POST'])
@token_required
def respond_handshake():
    global shared_key_cj
    Ai_x = request.json['Ai_x']
    Ai_y = request.json['Ai_y']
    Aj, shared_key_cj = cj_respond_handshake(cj_private_key, cj_public_key)
    return jsonify({'Aj_x': Aj.pubkey.point.x(), 'Aj_y': Aj.pubkey.point.y()})

@app.route('/receive-file', methods=['POST'])
@token_required
def receive_file():
    data = request.json
    file_name = data['file_name']
    encrypted_data = data['data'].encode('utf-8')
    fernet_key = data['fernet_key'].encode('utf-8')
    fernet = Fernet(fernet_key)
    destination_provider = data['destination_provider']

    try:
        decrypted_data = fernet.decrypt(encrypted_data)
        logging.info("File decrypted successfully!")
    except Exception as e:
        logging.error(f"Decryption failed: {str(e)}")
        return jsonify({'error': 'Decryption failed'}), 500

    if destination_provider == 'aws':
        aws_credentials = data['destination_credentials']
        session = boto3.Session(
            aws_access_key_id=aws_credentials['aws_access_key_id'],
            aws_secret_access_key=aws_credentials['aws_secret_access_key'],
            region_name=aws_credentials.get('region', 'us-east-1')
        )
        s3 = session.client('s3')
        destination_bucket = data['destination_bucket']

        try:
            s3.put_object(Bucket=destination_bucket, Key=file_name, Body=decrypted_data)
            logging.info(f"File {file_name} uploaded successfully to S3 bucket {destination_bucket}!")
        except Exception as e:
            logging.error(f"Upload to S3 failed: {str(e)}")
            return jsonify({'error': 'Upload to S3 failed'}), 500
    
    elif destination_provider == 'gcp':
        gcp_credentials = json.loads(data['destination_credentials']['service_account_json'])
        storage_client = gcp_storage.Client.from_service_account_info(gcp_credentials)
        bucket = storage_client.bucket(data['destination_bucket'])
        blob = bucket.blob(file_name)
        blob.upload_from_string(decrypted_data)
        logging.info(f"File {file_name} uploaded successfully to GCP bucket {data['destination_bucket']}!")
    
    return jsonify({'message': f'File {file_name} uploaded to {destination_provider} successfully!'})

if __name__ == '__main__':
    app.run(port=5001)