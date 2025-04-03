from flask import Flask, request, jsonify
from pcaka import init_user, generate_pid, ci_initiate_handshake
from cryptography.fernet import Fernet
import requests
import boto3
from google.cloud import storage as gcp_storage
from auth import token_required
import json

app = Flask(__name__)

ci_private_key, ci_public_key = init_user()
ci_pid = generate_pid(ci_public_key)
shared_key_ci = None

fernet_key = Fernet.generate_key()  # Generate a single encryption key
fernet = Fernet(fernet_key)

@app.route('/handshake', methods=['POST'])
@token_required
def handshake():
    global shared_key_ci
    cj_url = request.json['cj_url']
    Ai, shared_key_ci = ci_initiate_handshake(ci_private_key, ci_public_key)
    response = requests.post(f'{cj_url}/respond-handshake', headers=request.headers, json={
        'Ai_x': Ai.pubkey.point.x(),
        'Ai_y': Ai.pubkey.point.y()
    })
    return jsonify({'message': 'Handshake successful'})

@app.route('/transfer-file', methods=['POST'])
@token_required
def transfer_file():
    global fernet
    data = request.json
    file_name = data['file_name']
    source_provider = data['source_provider']
    source_bucket = data['source_bucket']

    if source_provider == 'aws':
        aws_credentials = data['source_credentials']
        session = boto3.Session(
            aws_access_key_id=aws_credentials['aws_access_key_id'],
            aws_secret_access_key=aws_credentials['aws_secret_access_key'],
            region_name=aws_credentials.get('region', 'us-east-1')  # Default to us-east-1
        )
        s3 = session.client('s3')

        try:
            obj = s3.get_object(Bucket=source_bucket, Key=file_name)
            file_data = obj['Body'].read()
        except Exception as e:
            return jsonify({'error': f'Failed to download from S3: {str(e)}'}), 500

    elif source_provider == 'gcp':
        gcp_credentials = json.loads(data['source_credentials']['service_account_json'])
        storage_client = gcp_storage.Client.from_service_account_info(gcp_credentials)
        bucket = storage_client.bucket(source_bucket)
        blob = bucket.blob(file_name)
        file_data = blob.download_as_bytes()

    encrypted_data = fernet.encrypt(file_data)

    requests.post(f'{data["cj_url"]}/receive-file', headers=request.headers, json={
        'file_name': file_name,
        'data': encrypted_data.decode('utf-8'),
        'fernet_key': fernet_key.decode('utf-8'),  # Send the encryption key
        'destination_credentials': data['destination_credentials'],
        'destination_provider': data['destination_provider'],
        'destination_bucket': data['destination_bucket']
    })
    return jsonify({'message': f'File {file_name} transferred successfully from {source_provider} to {data["destination_provider"]}.'})

if __name__ == '__main__':
    app.run(port=5000)
