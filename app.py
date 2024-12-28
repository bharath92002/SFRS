import os
import base64
import bcrypt
import numpy as np
from PIL import Image
import mysql.connector
from deepface import DeepFace
from flask import Flask, render_template, request, redirect, url_for, send_file, session

app = Flask(__name__, template_folder="templates")
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="0916",
    database="mydatabase"
)
cursor = db.cursor()


def allowed_file(filename):
    if "." in filename:
        parts = filename.rsplit(".", 1)

        if len(parts) == 2:
            file_extension = parts[1].lower()
            if file_extension in {"jpg", "jpeg", "png"}:
                return True
    return False


def compare_faces(stored_image_path, uploaded_file):
    try:
        uploaded_image = Image.open(uploaded_file).convert('RGB')
        uploaded_image_np = np.array(uploaded_image)
        result = DeepFace.verify(stored_image_path, uploaded_image_np, model_name="Facenet", enforce_detection=False)
        verified = result["verified"]
        return verified
    except Exception as e:
        print("Error in compare_faces function:", e)
        return False


def get_role(email):
    query = "SELECT role FROM login_info WHERE email = %s"
    args = (email,)
    cursor.execute(query, args)
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return None


@app.route("/")
def exam_cell():
    return render_template("examcell.html")


@app.route("/login_options")
def login_options():
    return render_template("login_options.html")


@app.route("/ad_login")
def ad_login():
    session['role'] = "admin"
    return redirect(url_for("login"))


@app.route("/teach_login")
def teach_login():
    session['role'] = "teacher"
    return redirect(url_for("login"))


@app.route("/login", methods=["POST", "GET"])
def login():
    message = ""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        query = "SELECT password, role, user_id FROM login_info WHERE email = %s"
        args = (email,)
        cursor.execute(query, args)
        result = cursor.fetchone()

        if result:
            stored_password = result[0].encode("utf-8")
            entered_password = password.encode("utf-8")
            #stored_role = result[1]
            teacher_name = result[2]

            if bcrypt.checkpw(entered_password, stored_password):
                user_role = get_role(email)
                if session.get('role') == user_role: 
                     session['role'] = user_role
                     if user_role == "admin":
                        return redirect(url_for("admin"))
                     elif user_role == "teacher":
                        session['teacher_name'] = teacher_name  
                        return redirect(url_for("teacher"))
                else:
                    message = "Invalid role. Please contact support."
            else:
                message = "Incorrect password"
        else:
            message = "Email not found"

    return render_template("login.html", message=message)



@app.route("/admin")
def admin():
    session['role'] = 'admin'
    return render_template("admin_exam.html")


@app.route("/teacher")
def teacher():
    session['role'] = 'teacher'
    return render_template("teacher_exam.html", teacher_name=session.get('teacher_name'))


@app.route("/select_year", methods=["GET", "POST"])
def select_year():
    if request.method == "POST":
        session['year'] = int(request.form.get("selected_year"))
        if session['role'] == "admin":
            return redirect(url_for("admin_page"))
        elif session['role'] == "teacher":
            return redirect(url_for("teacher_page"))
    else:
        return render_template("select_year.html")


@app.route("/admin_exam")
def admin_page():
    return render_template("admin_page.html", exam_type=session.get('exam_type'))


@app.route("/teacher_exam")
def teacher_page():
    return render_template("teacher.html", teacher_name=session.get('teacher_name'))


@app.route("/mid_exams", methods=["GET"])
def mid_examinations():
    session['exam_type'] = "mid_exams"
    return render_template("select_year.html")


@app.route("/sem_exams", methods=["GET"])
def sem_examinations():
    session['exam_type'] = "sem_exams"
    return render_template("select_year.html")

@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    message = ""
    if request.method == "POST":
        student_name = request.form.get("student_name")
        hall_ticket_number = request.form.get("hall_ticket_number")
        uploaded_student_image = request.files["student_image"]
        uploaded_hall_ticket_image = request.files["hall_ticket_image"]

        if student_name and hall_ticket_number and uploaded_student_image and uploaded_hall_ticket_image:
            student_image_folder = "student_images"
            hall_ticket_image_folder = "hall_tickets"
            
            student_image_path = os.path.join("static", student_image_folder, f"{hall_ticket_number}.png")
            uploaded_student_image.save(student_image_path)
            
            hall_ticket_image_path = os.path.join("static", hall_ticket_image_folder, f"{hall_ticket_number}_hall_ticket.png")
            uploaded_hall_ticket_image.save(hall_ticket_image_path)

            try:
                cursor.execute(
                    f"INSERT INTO {session.get('exam_type')} (student_name, hall_ticket_number, verified, image_path, hall_tkt_path, year) VALUES (%s, %s, %s, %s, %s, %s)",
                    (student_name, hall_ticket_number, 0, student_image_path, hall_ticket_image_path,
                     session.get('year')))
                db.commit()
                message = "Student added successfully!"
            except Exception as e:
                message = f"An error occurred: {str(e)}"
        else:
            message = "Please fill out all the fields"
    
    return render_template("add_students.html", message=message)


@app.route("/remove_student", methods=["GET", "POST"])
def remove_student():
    message = ""
    if request.method == "POST":
        hall_ticket_number = request.form.get("hall_ticket_number")

        if hall_ticket_number:
            try:
                cursor.execute(f"DELETE FROM {session.get('exam_type')} WHERE hall_ticket_number = '{hall_ticket_number}'")
                db.commit()
                message = f"Student with Hall Ticket Number {hall_ticket_number} has been removed successfully."
            except Exception as e:
                message = f"An error occurred: {str(e)}"
        else:
            message = "Please enter a Hall Ticket Number."
    
    return render_template("remove_students.html", message=message)


@app.route("/students_list", methods=['GET','POST'])
def show_student_list():
    exam_type = session.get('exam_type')
    year = session.get('year')

    if not exam_type or not year:
        return "Session variables not set", 400
    
    cursor.execute(f"SELECT student_name, hall_ticket_number, verified FROM {exam_type} WHERE year = {year}")
    student_list = cursor.fetchall()

    return render_template("show_student_list.html", student_list=student_list)


@app.route('/save_image', methods=['POST'])
def save_image():
    image_data = request.json.get('image_data')

    if not os.path.exists('static/images'):
        os.makedirs('static/images')

    with open('static/images/captured_image.png', 'wb') as f:
        f.write(base64.b64decode(image_data.split(',')[1]))

    return 'Image saved successfully'


@app.route("/face_scan", methods=["POST", "GET"])
def face_scan():
    return render_template("face_scan.html")


@app.route("/face_scan_verification", methods=["POST"])
def face_scan_verification():
    exam = session.get('exam_type')
    hall_ticket_number = request.form.get("hall_ticket_number")
    uploaded_image_path = 'static/images/captured_image.png'

    if not exam:
        return render_template("face_scan.html", verification_result="failure",
                               message="Error: Exam type is not set.")

    if not hall_ticket_number:
        return render_template("face_scan.html", verification_result="failure",
                               message="Error: Hall ticket number is missing.")

    cursor.execute(
        f"SELECT student_name, hall_ticket_number, image_path, hall_tkt_path FROM {exam} WHERE hall_ticket_number = '{hall_ticket_number}'")
    result = cursor.fetchone()

    if not result:
        return render_template("face_scan.html", verification_result="failure",
                               message="Error: Student record not found.")

    stored_image_path = result[2]
    hall_ticket_path = result[3]

    if not stored_image_path or not os.path.exists(stored_image_path):
        return render_template("face_scan.html", verification_result="failure",
                               message="Error: Stored image not found.")

    if compare_faces(stored_image_path, uploaded_image_path):
        cursor.execute(f"UPDATE {exam} SET verified = 1 WHERE hall_ticket_number = '{hall_ticket_number}'")
        db.commit()
        return render_template("face_scan.html", verification_result="success", hall_ticket_path=hall_ticket_path,
                               message="Verification successful")  # Added hall ticket path and message
    else:
        return render_template("face_scan.html", verification_result="failure", message="Error: Face do not match.")



@app.route("/authenticated_students")
def authenticated_students_page():
    cursor.execute(
        f"SELECT student_name, hall_ticket_number FROM {session.get('exam_type')} WHERE verified = 1 AND year = {session.get('year')}")
    authenticated_students = cursor.fetchall()

    if authenticated_students:
        return render_template("authenticated_students.html", authenticated_students=authenticated_students)
    else:
        return render_template("authenticated_students.html", authenticated_students=None)


@app.route("/phoney_students")
def phoney_students_page():
    cursor.execute(
        f"SELECT student_name, hall_ticket_number FROM {session.get('exam_type')} WHERE verified = 0 AND year = {session.get('year')}")
    phoney_students = cursor.fetchall()

    if phoney_students:
        return render_template("phoney_students.html", phoney_students=phoney_students)
    else:
        return render_template("phoney_students.html", phoney_students=None)


if __name__ == "__main__":
    app.run(debug=True)
