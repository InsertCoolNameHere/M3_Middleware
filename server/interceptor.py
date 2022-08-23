from flask import Flask, render_template, session, url_for, request, redirect
from flask import request
import data.mongo_loader as MongoLoader

app = Flask(__name__)

@app.route("/", methods = ['GET', 'POST'])
def index_page():

    if request.method == "POST":
        try:
            f_dict = {}

            f_dict["qbounds"] = request.form["qbounds"]
            f_dict["zlevel"] = int(request.form["zlevel"])
            f_dict["sdate"] = request.form["sdate"]
            f_dict["qband"] = request.form["qband"]

            print(f_dict)

            tileinfo = None
            aggregateinfo = None
            if f_dict["zlevel"] > 16:
                tileinfo = MongoLoader.fetch_image(f_dict["qbounds"],f_dict["zlevel"],f_dict["sdate"],f_dict["qband"])
            else:
                aggregateinfo = MongoLoader.fetch_aggregates(f_dict["qbounds"],f_dict["zlevel"],f_dict["sdate"],f_dict["qband"])

            return render_template('render_output.html', tileinfo=tileinfo, aggregateinfo = aggregateinfo)
        except ConnectionError as ce:
            print(str(ce))
            return redirect(url_for('render_server_down', msg=str(ce)))
        except Exception as err:
            print(str(err))
            return 'ERROR PROCESSING YOUR REQUEST!! ' + str(err)
    else:
        return render_template("index.html")

if __name__ == "__main__":
    app.run(debug = True)