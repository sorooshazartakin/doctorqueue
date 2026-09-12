from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)

DB = "doctor_queue.db"
VISIT_TIME = 10


def database():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def setup_database():
    con = database()

    con.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_date TEXT NOT NULL,
            gender TEXT NOT NULL,
            name TEXT NOT NULL,
            number INTEGER NOT NULL,
            phone TEXT NOT NULL,
            status TEXT DEFAULT 'waiting',
            sms_sent INTEGER DEFAULT 0
        )
    """)

    con.commit()
    con.close()


setup_database()
HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">

<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>مدیریت صف مطب</title>

<style>

body {
    font-family: Tahoma, Arial, sans-serif;
    background: #f2f4f7;
    margin: 0;
    padding: 20px;
}

.container {
    max-width: 1000px;
    margin: auto;
}

.box {
    background: white;
    padding: 20px;
    margin-bottom: 20px;
    border-radius: 12px;
}

.header {
    background: #17202a;
    color: white;
    padding: 25px;
    border-radius: 12px;
    margin-bottom: 20px;
}

input, select, button {
    padding: 12px;
    margin: 5px;
    font-family: Tahoma;
    border-radius: 7px;
    border: 1px solid #ccc;
}

button {
    background: #1769aa;
    color: white;
    border: none;
    cursor: pointer;
}

.green {
    background: #218c53;
}

.red {
    background: #c0392b;
}

.next {
    width: 100%;
    font-size: 20px;
    padding: 18px;
}

.current {
    background: #eef5ff;
    padding: 20px;
    text-align: center;
    border-radius: 10px;
    margin-bottom: 15px;
}

.current-number {
    font-size: 35px;
    font-weight: bold;
    color: #1769aa;
}

.current-name {
    font-size: 22px;
    font-weight: bold;
    margin: 10px;
}

.sms {
    background: #e8f8ee;
    padding: 15px;
    margin-top: 15px;
    border-radius: 8px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th {
    background: #17202a;
    color: white;
    padding: 10px;
}

td {
    padding: 10px;
    text-align: center;
    border-bottom: 1px solid #ddd;
}

.waiting {
    color: #d68910;
    font-weight: bold;
}

.visiting {
    color: #1769aa;
    font-weight: bold;
}

.done {
    color: #218c53;
    font-weight: bold;
}

</style>

</head>

<body>

<div class="container">

<div class="header">

<h1>سیستم مدیریت صف مطب</h1>

<p>
مدیریت نوبت و زمان انتظار بیماران
</p>

</div>
<div class="box">

<h2>تاریخ مراجعه</h2>

<form method="get" action="/">

<input
    type="date"
    name="date"
    value="{{ selected_date }}"
    required
>

<button type="submit">
نمایش تاریخ
</button>

</form>

<p>
تاریخ انتخاب‌شده:
<strong>{{ selected_date }}</strong>
</p>

</div>
<div class="box">

<h2>ثبت بیمار جدید</h2>

<form method="post" action="/add">

<input
    type="hidden"
    name="visit_date"
    value="{{ selected_date }}"
>

<select name="gender" required>

<option value="">جنسیت</option>

<option value="آقای">آقا</option>

<option value="خانم">خانم</option>

</select>

<input
    type="text"
    name="name"
    placeholder="نام و نام خانوادگی"
    required
>

<input
    type="number"
    name="number"
    placeholder="شماره نوبت"
    required
>

<input
    type="text"
    name="phone"
    placeholder="شماره موبایل"
    required
>

<button class="green" type="submit">
ثبت بیمار
</button>

</form>

</div>


<div class="box">

<h2>وضعیت فعلی</h2>

{% if current_patient %}

<div class="current">

<div>
نوبت در حال ویزیت
</div>

<div class="current-number">
{{ current_patient["number"] }}
</div>

<div class="current-name">
{{ current_patient["gender"] }}
{{ current_patient["name"] }}
</div>

</div>

{% else %}

<div class="current">

<div class="current-name">
هنوز ویزیتی شروع نشده
</div>

<div>
برای شروع روی دکمه زیر بزنید.
</div>

</div>

{% endif %}


<form method="post" action="/next">

<input
    type="hidden"
    name="visit_date"
    value="{{ selected_date }}"
>

<button class="next" type="submit">

نفر بعدی وارد پزشک شد

</button>

</form>


{% for message in sms_messages %}

<div class="sms">

<strong>
SMS آزمایشی:
</strong>

<br><br>

{{ message }}

</div>

{% endfor %}

</div>
<div class="box">

<h2>لیست بیماران</h2>

{% if patients %}

<table>

<tr>

<th>نوبت</th>

<th>نام</th>

<th>موبایل</th>

<th>وضعیت</th>

<th>نفر قبل</th>

<th>زمان انتظار</th>

</tr>

{% for p in patients %}

<tr>

<td>
{{ p["number"] }}
</td>

<td>
{{ p["gender"] }}
{{ p["name"] }}
</td>

<td>
{{ p["phone"] }}
</td>

<td>

{% if p["status"] == "waiting" %}

<span class="waiting">
منتظر
</span>

{% elif p["status"] == "visiting" %}

<span class="visiting">
در حال ویزیت
</span>

{% else %}

<span class="done">
ویزیت شد
</span>

{% endif %}

</td>

<td>

{% if p["status"] == "waiting" %}

{{ p["people_before"] }}

{% else %}

-

{% endif %}

</td>

<td>

{% if p["status"] == "waiting" %}

{{ p["waiting_minutes"] }} دقیقه

{% else %}

-

{% endif %}

</td>

</tr>

{% endfor %}

</table>

{% else %}

<p>
هنوز بیماری ثبت نشده است.
</p>

{% endif %}

</div>


<div class="box">

<h2>شروع روز جدید</h2>

<form method="post" action="/new_day">

<input
    type="hidden"
    name="visit_date"
    value="{{ selected_date }}"
>

<button class="red" type="submit">

حذف بیماران این تاریخ

</button>

</form>

</div>


</div>

</body>

</html>
"""
@app.route("/")
def home():

    selected_date = request.args.get("date")

    if not selected_date:
        selected_date = datetime.now().strftime("%Y-%m-%d")

    con = database()

    rows = con.execute(
        """
        SELECT *
        FROM patients
        WHERE visit_date = ?
        ORDER BY number
        """,
        (selected_date,)
    ).fetchall()

    con.close()

    patients = []

    current_patient = None
    current_index = -1

    for i, row in enumerate(rows):

        patient = dict(row)

        patients.append(patient)

        if patient["status"] == "visiting":

            current_patient = patient
            current_index = i

    sms_messages = []

    for i, patient in enumerate(patients):

        if patient["status"] != "waiting":

            patient["people_before"] = 0
            patient["waiting_minutes"] = 0

            continue

        if current_index >= 0:

            people_before = i - current_index - 1

        else:

            people_before = i

        if people_before < 0:
            people_before = 0

        patient["people_before"] = people_before

        patient["waiting_minutes"] = people_before * VISIT_TIME

        if (
            current_index >= 0
            and people_before == 2
            and patient["sms_sent"] == 0
        ):

            message = (
                patient["gender"]
                + " "
                + patient["name"]
                + "، در تاریخ "
                + selected_date
                + " دو نفر تا نوبت شما باقی مانده است. "
                + "لطفاً به مطب مراجعه کنید."
            )

            sms_messages.append(message)

            update_con = database()

            update_con.execute(
                """
                UPDATE patients
                SET sms_sent = 1
                WHERE id = ?
                """,
                (patient["id"],)
            )

            update_con.commit()
            update_con.close()

    total_patients = len(patients)

    waiting_count = 0
    done_count = 0

    for patient in patients:

        if patient["status"] == "waiting":

            waiting_count += 1

        elif patient["status"] == "done":

            done_count += 1

    return render_template_string(
        HTML,
        patients=patients,
        current_patient=current_patient,
        selected_date=selected_date,
        sms_messages=sms_messages,
        total_patients=total_patients,
        waiting_count=waiting_count,
        done_count=done_count
    )


@app.route("/add", methods=["POST"])
def add_patient():

    visit_date = request.form.get("visit_date")
    gender = request.form.get("gender")
    name = request.form.get("name")
    number = request.form.get("number")
    phone = request.form.get("phone")

    if not visit_date:
        return "تاریخ وارد نشده است."

    if not gender:
        return "جنسیت وارد نشده است."

    if not name:
        return "نام وارد نشده است."

    if not number:
        return "شماره نوبت وارد نشده است."

    if not phone:
        return "شماره موبایل وارد نشده است."

    try:

        number = int(number)

    except ValueError:

        return "شماره نوبت باید عدد باشد."

    con = database()

    existing = con.execute(
        """
        SELECT id
        FROM patients
        WHERE visit_date = ?
        AND number = ?
        """,
        (visit_date, number)
    ).fetchone()

    if existing:

        con.close()

        return "این شماره نوبت قبلاً ثبت شده است."

    con.execute(
        """
        INSERT INTO patients
        (
            visit_date,
            gender,
            name,
            number,
            phone
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            visit_date,
            gender,
            name,
            number,
            phone
        )
    )

    con.commit()
    con.close()

    return redirect("/?date=" + visit_date)
@app.route("/next", methods=["POST"])
def next_patient():

    visit_date = request.form.get("visit_date")

    if not visit_date:
        return "تاریخ مشخص نشده است."

    con = database()

    current = con.execute(
        """
        SELECT id
        FROM patients
        WHERE visit_date = ?
        AND status = 'visiting'
        LIMIT 1
        """,
        (visit_date,)
    ).fetchone()

    if current:

        con.execute(
            """
            UPDATE patients
            SET status = 'done'
            WHERE id = ?
            """,
            (current["id"],)
        )

    next_p = con.execute(
        """
        SELECT id
        FROM patients
        WHERE visit_date = ?
        AND status = 'waiting'
        ORDER BY number
        LIMIT 1
        """,
        (visit_date,)
    ).fetchone()

    if next_p:

        con.execute(
            """
            UPDATE patients
            SET status = 'visiting'
            WHERE id = ?
            """,
            (next_p["id"],)
        )

    con.commit()
    con.close()

    return redirect("/?date=" + visit_date)


@app.route("/new_day", methods=["POST"])
def new_day():

    visit_date = request.form.get("visit_date")

    if not visit_date:
        return "تاریخ مشخص نشده است."

    con = database()

    con.execute(
        """
        DELETE FROM patients
        WHERE visit_date = ?
        """,
        (visit_date,)
    )

    con.commit()
    con.close()

    return redirect("/?date=" + visit_date)


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )