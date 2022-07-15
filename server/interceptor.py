from flask import Flask, render_template, session, url_for, request, redirect

app = Flask(__name__)

@app.route("/", methods = ['GET', 'POST'])
def index_page():
    return render_template("index.html")
    #return redirect(url_for('render_success', job_id=form_data['jId'] ))

if __name__ == "__main__":
    app.run(debug = True)