import boto3


BUCKET_NAME = "pdf-with-watermark"

def save_file_to_s3(filename: str, access_key: str, secret_key: str):
    print("Uploading to S3...")
    if access_key and secret_key:
        s3 = boto3.resource('s3')
        s3.Bucket(BUCKET_NAME).upload_file(filename, filename)
        return
    print("Can't find credentials")
