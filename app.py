from flask import Flask, request, render_template, make_response, jsonify

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
    print(request.form)
    print(request.files)
    link = "https://example.com"
    resp = {'link': link}
    return make_response(jsonify(resp), 200)

@app.route('/', methods=['GET'])
def home():
    """
    Process GET request
    """
    return render_template('form.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
