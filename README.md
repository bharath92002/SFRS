Student Face Recognition System for Exam Authentication
This project is a web-based application that integrates face recognition technology to enhance the authentication process for student exams. Built using Flask, MySQL, and the DeepFace library, it streamlines the identification and verification of students through facial recognition, ensuring a secure and efficient examination environment.

Key Features:
Role-Based Access Control: Separate login options for administrators and teachers with customized access and functionalities.
Student Management:
Add or remove students with associated images and hall ticket numbers.
Maintain records categorized by examination type and academic year.
Face Recognition:
Verify students' identities using facial recognition technology.
Automatic comparison of uploaded images with stored records.
Exam Management:
Separate management for mid-term and semester examinations.
Track authenticated and unauthenticated (phoney) students.
Secure Data Handling:
Passwords are hashed with bcrypt.
Secure image storage for student records and captured images.
Tech Stack:
Backend: Python, Flask
Frontend: HTML, CSS, templates
Database: MySQL
Face Recognition: DeepFace with Facenet model
Libraries: NumPy, PIL, bcrypt
