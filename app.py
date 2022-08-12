import os
import shutil

from flask import Flask, request, render_template, make_response, jsonify

from lib.aws import save_file_to_s3, BUCKET_NAME
from lib.pdf import Document

app = Flask("PDF-coverter")
app.config["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID", "")
app.config["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

@app.route('/ping')
def ping():
    """
    Route for connection testing
    """
    return 'pong'

@app.route('/', methods=['POST'])
def main():
    """
    Receives POST requests and processes the file
    """
    files = []
    error = ""
    for f in request.files.getlist('files'):
        f.save(f.filename)
        files.append(f.filename)
    password = request.form["password"]
    watermark = request.form["watermark"]
    d = Document(files, password, watermark)
    d.validate_all()
    path = d.process()

    link = ""
    if app.config["ENV"] == "development":
        # save file locally
        link = save_locally(path)
    else:
        # upload to S3
        save_file_to_s3(path, app.config["AWS_ACCESS_KEY_ID"], app.config["AWS_SECRET_ACCESS_KEY"])
        link = f"https://{BUCKET_NAME}.s3.amazonaws.com/{path}"
    
    resp = {'link': link}
    return make_response(jsonify(resp), 200)

@app.route('/', methods=['GET'])
def home():
    """
    Process GET request
    """
    return render_template('form.html')

def save_locally(filename):
    new_filename = f"static/{filename}"
    shutil.move(filename, new_filename)
    return new_filename


if __name__ == "__main__":
    print(app.config.keys())
    app.run(host="0.0.0.0", debug=True)
