from flask import Flask, render_template, request, redirect, url_for, session, send_file
import csv
from datetime import date, timedelta
from flask import session, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import base64
from urllib.parse import quote, unquote
import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
import json


app = Flask(__name__)
app.secret_key = "super secret key"
app.permanent_session_lifetime = timedelta(hours=24)

CSV_FILE = "./static/data.csv"


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Dummy user database
USER_DATABASE = {
    "admin": "scrypt:32768:8:1$gat0fsAktSVqwyMS$847099b9bacbaa5a1a52e6fcd4dd036747824dced1302664eb731887c7135cc7c4f707d3373bbb836bc9a0834359ac655cd1f828762b35531f614248d4c9055e",  # username: password
    "gulshan": "scrypt:32768:8:1$NtmqkXIetNPUMzDb$34de47397c7fb3d0e5cc3c2e17f398af2fe1cacf191b5757a9f934e7ee7cb36798578595433e92f9090d8265402e5415174d8c04ae0eaaa1258939f3e860b092"
}

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Load user callback
@login_manager.user_loader
def load_user(user_id):
    if user_id in USER_DATABASE:
        return User(user_id)
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in USER_DATABASE and check_password_hash(USER_DATABASE[username], password):
            user = User(username)
            login_user(user)
            session.permanent = True
            with open("./static/awb_add_logs.txt", "a") as log:
                log.write(f"[{datetime.datetime.now()}] '{(str(current_user.id)).upper()}' LOGGED IN")
                log.write("\n--------------------------------------\n")
            return redirect(url_for("home"))
        else:
            return "Invalid username or password!"

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))



# Ensure the CSV file exists and has headers
def initialize_csv():
    try:
        with open(CSV_FILE, mode='r') as file:
            pass
    except FileNotFoundError:
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Date" , "AWB Number", "Party Name", "Consignee", "Destination", "Number of Pieces", "Weight", "Rate", "GST", "Total Cost", "mode_of_payment"])

# Generate the next AWB number
def generate_awb():
    try:
        with open(CSV_FILE, mode='r') as file:  
            reader = csv.reader(file)
            rows = list(reader)
            if len(rows) > 1:
                last_awb = int(rows[-1][1])  # Get the last AWB number
                return last_awb + 1
            else:
                return 1
    except FileNotFoundError:
        return 1
    

@app.route("/")
@login_required  # Restricts access to logged-in users
def home():
    return render_template("home.html")


@app.route('/download-csv')
@login_required
def download_csv():
    # Path to your CSV file
    file_path = './static/data.csv'
    
    # Check if the file exists
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=str(date.today().strftime("%Y-%m-%d"))+".csv", mimetype='text/csv')
    else:
        return "File not found", 404


@app.route("/add-awb", methods=["GET", "POST"])
@login_required
def form():
    if request.method == "POST":
        party_name = (request.form.get("party_name")).upper()
        consignee = (request.form.get("consignee")).upper()
        destination = (request.form.get("destination")).upper()
        number_of_pieces = request.form.get("number_of_pieces")
        weight = request.form.get("weight")
        mode_of_payment = request.form.get("mode_of_payment")
        rate = request.form.get("rate")
        total_cost = request.form.get("total_cost")
        gst = request.form.get("gst")
        awb = generate_awb()
        today = date.today().strftime("%d-%m-%Y")



        # Save data to CSV
        with open(CSV_FILE, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([today, awb, party_name, consignee, destination, number_of_pieces, weight,rate, gst, total_cost, mode_of_payment])

        encoded_data = base64.urlsafe_b64encode(f"{awb}|{party_name}|{destination}|{consignee}|{number_of_pieces}|{weight}|{rate}|{gst}|{total_cost}|{mode_of_payment}|{today}".encode()).decode()

        with open("./static/awb_add_logs.txt", "a") as log:
            log.write(f"\n[{datetime.datetime.now()}] '{(str(current_user.id)).upper()}' Added AWB Number '{awb}':\n \t Party Name : '{party_name}',\n \t consignee : '{consignee}', \n \t destination : '{destination}', \n \t number_of_pieces : '{number_of_pieces}',\n \t weight : '{weight}',\n \t rate : '{rate}', \n \t gst : '{gst}', \n \t total_cost : '{total_cost}', \n \t mode_of_payment : '{mode_of_payment}' \n")
            log.write("\n--------------------------------------\n")

        return redirect(url_for("success", data=quote(encoded_data)))

    return render_template("form.html")


@app.route("/success")
@login_required
def success():
    encoded_data = request.args.get("data")
    
    
    awb = party_name = destination = consignee = number_of_pieces = weight = mode_of_payment = rate = gst = total_cost = "-"

    # If data exists, try decoding and extracting it
    if encoded_data:
        try:
            decoded_data = base64.urlsafe_b64decode(unquote(encoded_data)).decode()
            awb, party_name, destination, consignee, number_of_pieces, weight, rate, gst, total_cost, mode_of_payment, today = (x if x else "-" for x in decoded_data.split("|"))
        except Exception:
            # If decoding fails, keep the default values
            pass
    # print(awb, party_name, destination, consignee, number_of_pieces, weight, mode_of_payment, rate, gst, total_cost)
    data={"awb":awb , "party_name":party_name , "destination":destination , "consignee":consignee , "number_of_pieces":number_of_pieces , "weight":weight , "rate":rate , "gst":gst , "total_cost":total_cost , "mode_of_payment":mode_of_payment, "date":today}
    return render_template("awb.html", data=data)
    # return "Form submitted successfully! AWB Number has been generated."


@app.route("/navigate")
@login_required
def navigate():
    return render_template("navigate.html")

# @app.route("/manifest")
# @login_required
# def manifest():
#     import csv
#     from datetime import date

#     today = date.today().strftime("%Y-%m-%d")
#     entries = []

#     # Read entries from the CSV
#     with open("./static/data.csv", "r") as csvfile:
#         reader = csv.DictReader(csvfile)
#         for row in reader:
#             if row["Date"] == today:
#                 entries.append(row)
#     # print(entries)
#     return render_template("manifest.html", entries=enumerate(entries))

@app.route("/manifest")
@login_required
def manifest():
    import csv
    import base64
    from urllib.parse import quote
    from datetime import date

    today = date.today().strftime("%d-%m-%Y")
    entries = []

    # Read entries from the CSV
    with open("./static/data.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["Date"] == today:
                # Encode row data
                raw_data = f"{row['AWB Number']}|{row['Party Name']}|{row['Destination']}|{row['Consignee']}|{row['Number of Pieces']}|{row['Weight']}|{row['Rate']}|{row['GST']}|{row['Total Cost']}|{row['mode_of_payment']}|{row['Date']}"
                encoded_data = base64.urlsafe_b64encode(raw_data.encode()).decode()
                row["encoded_data"] = quote(encoded_data)  # URL-safe encoding
                entries.append(row)

    return render_template("manifest.html", entries=enumerate(entries))




@app.route("/search")
@login_required
def search():
    import csv

    filter_by = request.args.get("filter")
    query = request.args.get("query")
    results = []

    # Read entries from the CSV and filter by the query
    with open("./static/data.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if query.lower() == row[filter_by].lower():
                raw_data = f"{row['AWB Number']}|{row['Party Name']}|{row['Destination']}|{row['Consignee']}|{row['Number of Pieces']}|{row['Weight']}|{row['Rate']}|{row['GST']}|{row['Total Cost']}|{row['mode_of_payment']}|{row['Date']}"
                encoded_data = base64.urlsafe_b64encode(raw_data.encode()).decode()
                row["encoded_data"] = quote(encoded_data)  # URL-safe encoding
                results.append(row)

    return render_template("manifest.html", entries=enumerate(results))




@app.route("/get-party-names")
@login_required
def get_party_names():
    import csv
    from flask import jsonify

    party_names = set()

    # Read party names from the CSV
    with open("./static/data.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["Party Name"]:
                party_names.add(row["Party Name"])

    return jsonify(list(party_names))  # Return as JSON


@app.route("/search-party-names")
@login_required
def search_party_names():
    import csv
    from flask import request, jsonify

    query = request.args.get("query", "").lower()  # Get the user query
    party_names = set()

    # Read CSV and filter party names based on the query
    with open("./static/data.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["Party Name"] and query in row["Party Name"].lower():
                party_names.add(row["Party Name"].strip())

    return jsonify(list(party_names))  # Return matching party names as JSON


@app.route("/get-rate")
@login_required
def get_rate():
    # import csv
    from flask import request, jsonify

    party_name = (request.args.get("party_name", "").strip()).upper()
    destination = (request.args.get("destination", "").strip()).upper()

    # print(party_name)
    # print(destination)
    with open('rates.json', 'r') as file:
        data = json.load(file)
    rate = data.get(party_name, {}).get(destination, None)
    return jsonify({"rate": rate})



# def read_csv():
#     entries = []
#     with open(CSV_FILE, 'r') as file:
#         reader = csv.DictReader(file)
#         for row in reader:
#             entries.append(row)
#     return entries

# def write_csv(entries):
#     with open(CSV_FILE, 'w', newline='') as file:
#         fieldnames = ['AWB Number', 'Date', 'Party Name', 'Consignee', 'Destination', 'Number of Pieces', 'Weight', 'Rate', 'GST', 'Total Cost', 'Mode of Payment']
#         writer = csv.DictWriter(file, fieldnames=fieldnames)
#         writer.writeheader()
#         for entry in entries:
#             writer.writerow(entry)


@app.route("/edit_view", methods=["GET", "POST"])
@login_required
def edit_view():
    if request.method == "POST":
        # Handle form submission for editing an entry
        awb_number = request.form["awb"]
        # print(awb_number)
        updated_data = {
            "Party Name": str(request.form["party_name"]).upper(),
            "Consignee": str(request.form["consignee"]).upper(),
            "Destination": str(request.form["destination"]).upper(),
            "Number of Pieces": request.form["number_of_pieces"],
            "Weight": request.form["weight"],
            "Rate": request.form["rate"],
            "GST": request.form["gst"],
            "Total Cost": request.form["total_cost"],
            "mode_of_payment": request.form["mode_of_payment"],
        }
        
        # Update the CSV file
        updated = False
        rows = []
        with open("./static/data.csv", "r") as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames
            for row in reader:
                if row["AWB Number"] == awb_number:
                    changes = []
                    for key, new_value in updated_data.items():
                        old_value = row.get(key, "")
                        if old_value != new_value:
                            changes.append(f"{key}: '{old_value}' -> '{new_value}'")
                            row[key] = new_value  # Update the value   
                    if changes:
                        with open("./static/logs.txt", "a") as log:
                            log.write(
                                f"[{datetime.datetime.now()}] '{(str(current_user.id)).upper()}' edited AWB Number '{awb_number}':\n"
                            )
                            log.write("\n".join(changes) + "\n\n")
                            log.write("\n--------------------------------------\n")
                        updated = True
                rows.append(row)

        # Write the updated data back to the CSV file
        if updated:
            with open(CSV_FILE, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

        return redirect(url_for("edit_view"))

    # For GET request, load all entries

    entries = []
    with open("./static/data.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Strip whitespace from all values
            row = {key: (value.strip() if isinstance(value, str) else value) for key, value in row.items()}
            entries.append(row)
    # print(entries)
    return render_template("edit_view.html", entries=entries)



# Function to log changes (username, date/time, field changed)
def log_change(awb_number, updated_entry):
    timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    log_message = f"User: {current_user} | AWB: {awb_number} | Changes: {updated_entry} | Time: {timestamp}\n"
    
    with open('logs.txt', 'a') as log_file:
        log_file.write(log_message)
        log_file.write("\n--------------------------------------\n")




RATES_FILE = "rates.json"

# Load rates from the file
def load_rates():
    try:
        with open(RATES_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save rates to the file
def save_rates(rates):
    with open(RATES_FILE, "w") as file:
        json.dump(rates, file, indent=4)



def log_rate_change(action, party, city, old_rate=None, new_rate=None):
    """Logs changes made to rates."""
    with open("./static/rates_logs.txt", 'a') as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user = str(current_user.id).upper()
        log_message = f"{timestamp} | {user} | Action: {action} | Party: {party} | City: {city} "
        
        if action == "edit":
            log_message += f"| From: {old_rate} To: {new_rate}"
        elif action == "add":
            log_message += f"| Added: {new_rate}"
        elif action == "delete":
            log_message += f"| Deleted: {old_rate}"
        log_message += "\n"
        log_file.write(log_message)
        log_file.write("\n--------------------------------------\n")

@app.route("/rates", methods=["GET", "POST"])
@login_required
def rates():
    rates_data = load_rates()

    if request.method == "POST":
        party = (request.form.get("party")).upper()
        city = (request.form.get("city")).upper()
        new_rate = request.form.get("rate")
        action = request.form.get("action")  # Add or Edit action

        if party and city and new_rate.isdigit():
            if action == "add":
                rates_data.setdefault(party, {})[city] = int(new_rate)
                log_rate_change("add", party, city, new_rate=new_rate)
            elif action == "edit":
                old_rate = rates_data.get(party, {}).get(city, None)
                if old_rate != int(new_rate):
                    rates_data.setdefault(party, {})[city] = int(new_rate)
                    log_rate_change("edit", party, city, old_rate=old_rate, new_rate=new_rate)

            save_rates(rates_data)
            return redirect(url_for("rates"))

    return render_template("rates.html", rates=rates_data)


@app.route("/delete-rate", methods=["POST"])
@login_required
def delete_rate():
    rates_data = load_rates()
    party = request.form.get("party")
    city = request.form.get("city")

    if party in rates_data and city in rates_data[party]:
        old_rate = rates_data[party][city]
        del rates_data[party][city]
        if not rates_data[party]:  # Remove party if no cities are left
            del rates_data[party]
        save_rates(rates_data)
        log_rate_change("delete", party, city, old_rate=old_rate)

    return redirect(url_for("rates"))






def load_manifest():
    entries = []
    with open("./static/data.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Strip whitespace from all values
            row = {key: (value.strip() if isinstance(value, str) else value) for key, value in row.items()}
            entries.append(row)
    return entries


def save_manifest(entries):
    if not entries:
        return
    with open("./static/data.csv", "w", newline="") as csvfile:
        fieldnames = entries[0].keys()  # Get headers from the first row
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)



@app.route("/bill-generator", methods=["GET", "POST"])
@login_required
def bill_generator():
    entries = load_manifest()
    bill_data = []
    total_amount = 0
    total_gst = 0
    print()
    # print(type(entries[0]['Date']))
    if request.method == "POST":
        party_name = request.form.get("party_name")
        date = request.form.get("date")
        all_time = request.form.get("all_time") in ["true", "on"] 
        # Checkbox to indicate "All Time"
        print(request.form.get("all_time"))
        print(all_time)
        # date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
        # date = date_obj.strftime("%d-%m-%Y")
        # date = datetime.datetime.strptime(date, "%d-%m-%Y").date()
        # date1 = datetime.datetime.strptime(entries[0]['Date'], "%Y-%m-%d").date()
        # print(date1)
        # print(type(date1))
        if date!="":
            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        print(date)
        print(type((date)))
        # Filter entries based on party name, payment mode, and date
        for entry in entries:
            try:
                if (
                    (party_name=="++" or  str(entry["Party Name"]).upper() == party_name.upper())
                    and entry["mode_of_payment"] == "toPay"
                    and (all_time or ((datetime.datetime.strptime(str(entry["Date"]), "%d-%m-%Y").date()) >= date))
                ):
                    bill_data.append(entry)
                    total_amount += float(entry["Total Cost"])
                    total_gst += float(entry["GST"])
            except:
                print(f"Skipping entry with invalid date: {entry['Date']} {type(entry['Date'])} ")
                continue

    return render_template(
    "bill_generator.html",
    bill_data=enumerate(bill_data),  # Add index using enumerate
    total_amount=total_amount,
    total_gst=total_gst,
    )



@app.route("/mark-as-paid", methods=["POST"])
@login_required
def mark_as_paid():
    entries = load_manifest()
    party_name = request.form.get("party_name")
    date1 = request.form.get("date")
    all_time = request.form.get("all_time") in ["true", "on"]
  # Checkbox to indicate "All Time"
    if date1!="":
        date1 = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    # print(date)
    # print(request.form)
    # print(all_time)

    # Update entries
    for entry in entries:
        try:
            if (
                str(entry["Party Name"]).upper() == party_name.upper()
                and entry["mode_of_payment"] == "toPay"
                and (all_time or ((datetime.datetime.strptime(str(entry["Date"]), "%d-%m-%Y").date()) >= date1))
            ):
                entry["mode_of_payment"] = "Paid on "+str(date.today().strftime("%Y-%m-%d"))
                with open('./static/bills_logs.txt', 'a') as log:
                    log.write(f"\n[{datetime.datetime.now()}] '{(str(current_user.id)).upper()}' Marked AWB Number '{entry["AWB Number"]}'as paid:\n \t Party Name : '{entry["Party Name"]}',\n \t consignee : '{entry["Consignee"]}', \n \t destination : '{entry["Destination"]}', \n \t number_of_pieces : '{entry["Number of Pieces"]}',\n \t weight : '{entry["Weight"]}',\n \t rate : '{entry["Rate"]}', \n \t gst : '{entry["GST"]}', \n \t total_cost : '{entry["Total Cost"]}', \n \t mode_of_payment : '{entry["mode_of_payment"]}' \n")
                    log.write("\n--------------------------------------\n")
                print(f"marked: {entry['Date']} {type(entry['Date'])} {((datetime.datetime.strptime(str(entry["Date"]), "%d-%m-%Y").date()) >= date1)} ")
        except Exception as p:
                print(f"Skipping entry with invalid date: {entry['Date']} {type(entry['Date'])} ")
                print(p)
                continue

    save_manifest(entries)
    return redirect(url_for("bill_generator"))




LOGS_DIR = './static'  # Ensure this folder exists with the log files

# Route for the Show Logs page
def load_logs(filename):
    log_path = os.path.join(LOGS_DIR, filename)
    if os.path.exists(log_path):
        with open(log_path, 'r') as file:
            content = file.read()

        # Split the logs based on the separator line
        logs = content.split('\n--------------------------------------\n')
        logs = [log.strip() for log in logs if log.strip()]  # Remove any empty logs
        return logs
    return []

# Route for the Show Logs page
@app.route("/show-logs", methods=["GET", "POST"])
@login_required
def show_logs():
    selected_file = None
    logs = []

    if request.method == "POST":
        # Get the selected log file
        selected_file = request.form.get("log_file")
        logs = load_logs(selected_file)  # Load and process the logs

    return render_template("show_logs.html", logs=logs, selected_file=selected_file)

# Route to handle downloading the log file
@app.route("/download-log/<filename>")
@login_required
def download_log(filename):
    log_path = os.path.join(LOGS_DIR, filename)
    if os.path.exists(log_path):
        return send_file(log_path, as_attachment=True)
    return "File not found", 404









if __name__ == "__main__":
    initialize_csv()
    app.run(debug=True, host='192.168.31.180')
