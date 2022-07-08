from flask import Flask

app = Flask("PDF-coverter")

@app.route('/ping')
def hello():
    return 'pong'


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
