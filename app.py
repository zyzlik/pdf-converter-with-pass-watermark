import shutil

from flask import Flask, request, render_template, make_response, jsonify

from lib.pdf import Document

app = Flask("PDF-coverter")

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
        # https://stackoverflow.com/questions/53146615/getting-file-url-after-upload-amazon-s3-python-boto3
        link = "s3://..."
    
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
