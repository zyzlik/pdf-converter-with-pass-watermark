from flask import Flask, request

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
    f = request.files['document']
    f.save(f.filename)
    return "Got your file!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
