"""
RDS 데이터 로딩 Lambda 핸들러
S3에서 SQL 파일을 다운로드하여 RDS에 실행합니다.
"""

import os
import json

import boto3
import psycopg2


def lambda_handler(event, context):
    s3 = boto3.client("s3")
    response = s3.get_object(
        Bucket=os.environ["S3_BUCKET"],
        Key=os.environ["S3_KEY"],
    )
    sql = response["Body"].read().decode("utf-8")

    try:
        conn = psycopg2.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
        )
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        conn.close()
        return {"statusCode": 200, "body": json.dumps("Data loaded successfully")}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}
