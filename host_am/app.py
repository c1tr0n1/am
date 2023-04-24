from flask import Flask, render_template, url_for
import pymongo

app = Flask(__name__)

CONNECTION_STRING = "mongodb+srv://br4pk33t:MJITz7Jc6o5LzwN2@cluster0.fdzzwnj.mongodb.net/?retryWrites=true&w=majority"

@app.route('/')
def index():
    client = pymongo.MongoClient(CONNECTION_STRING)
    db = client.amazdb
    collection = db["amazcol"]
    entries = collection.find()
    entries_amount = collection.count_documents({})
    return render_template('index.html', entries=entries, entries_amount=entries_amount)

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0')
