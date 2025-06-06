import json
import boto3
import os

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get("BUCKET_NAME", "cvision-cv-bucket")

def lambda_handler(event, context):
    try:
        # Parse the incoming event to get the body
        body = json.loads(event.get('body', '{}'))

        print("DEBUG EVENT:", event)
        print("DEBUG BODY:", body)

        job_id = body.get("job_id")
        filenames = body.get("filenames")  # We expect an array of filenames

        if not job_id or not filenames or not isinstance(filenames, list):
            return {
                "statusCode": 400,
                "headers": cors_headers(),
                "body": json.dumps({"error": "Se requiere job_id y un array de filenames"})
            }

        # TODO: Validar job_id contra DynamoDB

        result = []
        for filename in filenames:
            key = f"uploads/{job_id}/{filename}"
            url = s3.generate_presigned_url(
                ClientMethod='put_object',
                Params={
                    'Bucket': BUCKET_NAME,
                    'Key': key,
                    'ContentType': 'application/pdf'
                },
                ExpiresIn=3600
            )
            result.append({
                "filename": filename,
                "upload_url": url,
                "s3_key": key
            })

        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps({
                "job_id": job_id,
                "presigned_urls": result
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({"error": str(e)})
        }


def cors_headers():
    return {
        "Access-Control-Allow-Origin": "http://localhost:5173",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "OPTIONS,POST"
    }
