import json
import uuid
from datetime import datetime
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['JOB_POSTINGS_TABLE'])

REQUIRED_FIELDS = ["title", "description"]

def lambda_handler(event, context):
    print("DEBUG EVENT:", json.dumps(event))
    try:
        # Verify that the event has a body
        if "body" not in event:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Missing request body"})
            }

        # Parse the body of the event
        try:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        except json.JSONDecodeError:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid JSON in request body"})
            }

        # Validate required fields
        missing_fields = [field for field in REQUIRED_FIELDS if field not in body]
        if missing_fields:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": f"Missing fields: {', '.join(missing_fields)}"})
            }

        # Validate description is not empty
        if not body["description"].strip():
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Description cannot be empty"})
            }

        # Get user_id from the event
        claims = event.get("requestContext", {}).get("authorizer", {}).get("claims", {})
        user_id = claims.get("sub")

        if not user_id:
            return {
                "statusCode": 401,
                "body": json.dumps({"message": "Unauthorized - user_id not found"})
            }

        # Generate unique job_id and created_at timestamp
        job_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()

        # Build the item to be stored in DynamoDB
        item = {
            "pk": f"JD#{job_id}",
            "sk": f"USER#{user_id}",
            "created_at": created_at,
            "title": body["title"],
            "description": body["description"],
            "status": 1,  # 1 means active
            "candidates": [],  # Initialize with an empty list
        }

        # Save the item in DynamoDB
        table.put_item(Item=item)

        # Return the job_id as a response
        return {
            "statusCode": 201,
            "body": json.dumps({"job_id": job_id})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Internal server error: {str(e)}"})
        }
