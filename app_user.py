from flask import Flask, request, jsonify
import boto3
import json

app = Flask(__name__)

def transfer_aws_to_aws(source_bucket, destination_bucket, file_name, source_credentials, destination_credentials):
    """Transfer file from AWS to AWS."""
    try:
        # Create S3 clients for source and destination
        session_source = boto3.Session(
            aws_access_key_id=source_credentials['aws_access_key_id'],
            aws_secret_access_key=source_credentials['aws_secret_access_key'],
            region_name=source_credentials['region']
        )
        session_dest = boto3.Session(
            aws_access_key_id=destination_credentials['aws_access_key_id'],
            aws_secret_access_key=destination_credentials['aws_secret_access_key'],
            region_name=destination_credentials['region']
        )

        s3_source = session_source.client('s3')
        s3_dest = session_dest.client('s3')

        # Copy file from source to destination
        copy_source = {'Bucket': source_bucket, 'Key': file_name}
        s3_dest.copy_object(Bucket=destination_bucket, Key=file_name, CopySource=copy_source)

        return f"File {file_name} copied from {source_bucket} to {destination_bucket} (AWS to AWS)."

    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/initiate-transfer', methods=['POST'])
def initiate_transfer():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON request"}), 400

        # Extract required parameters
        source_credentials = data.get('source_credentials')
        destination_credentials = data.get('destination_credentials')
        source_bucket = data.get('source_bucket')
        destination_bucket = data.get('destination_bucket')
        file_name = data.get('file_name')

        if not all([source_credentials, destination_credentials, source_bucket, destination_bucket, file_name]):
            return jsonify({"error": "Missing required parameters"}), 400

        # Perform AWS-to-AWS transfer
        result = transfer_aws_to_aws(source_bucket, destination_bucket, file_name, source_credentials, destination_credentials)

        return jsonify({"message": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5002)
