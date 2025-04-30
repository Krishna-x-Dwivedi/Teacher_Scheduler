# **Timetable Scheduler & Admin Application**

This web application helps manage academic scheduling information, including faculties, subjects, classes, and requirements, with features for basic timetable generation.

## **Features**

* **User Management:**  
  * User Sign Up & Login  
  * Persistent login sessions (user stays logged in across browser refreshes)  
* **Data Management (Admin):**  
  * Manage Faculties (Add/View)  
  * Manage Subjects (Add/View \- including Lab designation)  
  * Manage Faculty-Subject Assignments (Assign/View/Remove which subjects a faculty can teach)  
  * Manage Branches (Add/View)  
  * Manage Sections (Add/View)  
  * Manage Classes (Add/View \- linking Branch, Section, Year)  
  * Manage Subject Requirements (Define lectures per week for a subject per branch/year)  
  * Manage Locations (Add/View \- including Lab designation)  
  * Manage Time Slots (Add/View \- defining periods, times, and applicable year groups)  
* **Reminders:**  
  * Add, view, and delete personal reminders.  
* **Timetable Generation (Basic):**  
  * Placeholder endpoint to trigger generation based on defined data.  
  * Basic algorithm attempts to schedule lectures respecting faculty, class, and location constraints. (Further development needed for complex scenarios and optimization).

## **Technology Stack**

* **Backend:**  
  * Language: **Python**  
  * Web Framework: **Flask**  
  * Database: **MySQL**  
  * API Handling: Flask routes, **Flask-Cors**  
  * Session Management: Flask Sessions (Secure Cookies)  
  * Database Connector: **mysql-connector-python**  
* **Frontend:**  
  * Structure: **HTML**  
  * Styling: **Tailwind CSS** (via CDN)  
  * Interactivity: **Vanilla JavaScript** (using fetch for API calls)

## **Setup and Running**

Follow these steps to set up and run the project locally. For more detailed explanations, refer to the Project Setup Guide.md document.  
**1\. Prerequisites:**

* **Python 3.8+** installed (with pip).  
* **MySQL Server** installed and running.

**2\. Clone or Download:**

* Get the project files (app.py, scheduler.html) and place them in a dedicated folder (e.g., TimetableProject).

**3\. Create MySQL Database:**

* Connect to your MySQL server (using command line or a tool like MySQL Workbench/phpMyAdmin).  
* Create the database:  
  CREATE DATABASE timetable\_db;

**4\. Install Python Dependencies:**

* Open your terminal or command prompt.  
* Navigate (cd) into your project folder (TimetableProject).  
* Install the required libraries:  
  pip install Flask Flask-Cors mysql-connector-python

**5\. Configure Database Connection:**

* Open the app.py file in a text editor.  
* Locate the MYSQL\_CONFIG dictionary near the top.  
* Update the 'user', 'password', 'host' (usually 'localhost'), and 'database' values to match your MySQL setup.

**6\. Configure Flask Secret Key:**

* In app.py, find the line app.config\['SECRET\_KEY'\] \= 'your-very-secret-key-for-development-sessions'.  
* **Important:** Change the placeholder string to your own unique, random, and secret key, especially if deploying. For development, the provided string is okay, but remember it controls session security.

**7\. Run the Backend:**

* In your terminal (still in the project folder), run:  
  python app.py

* The server should start, initialize the database tables (if they don't exist), and indicate it's running (usually on http://127.0.0.1:5000). Keep this terminal window open.

**8\. Open the Frontend:**

* In your computer's file explorer, navigate to the project folder.  
* Double-click the scheduler.html file to open it in your web browser.

**9\. Use the Application:**

* Sign up for a new user account first.  
* Log in with your credentials.  
* Use the sidebar to navigate through the different admin sections to add data (Branches, Sections, Faculties, Subjects, Mappings, Classes, Requirements, etc.) before attempting timetable generation.

**10\. Stop the Application:**

* Go back to the terminal window where the backend is running.  
* Press Ctrl \+ C to stop the Flask server.

## **Future Development / TODO**

* Implement robust password hashing for user accounts.  
* Add Update and Delete functionality for all admin data types (Faculties, Subjects, Branches, etc.).  
* Develop a more sophisticated timetable generation algorithm to handle complex constraints and optimize schedules.  
* Implement timetable display on the frontend.  
* Add timetable export functionality (PDF/Excel).  
* Refine error handling and user feedback.  
* Add input validation on both frontend and backend.  
* Implement role-based access control (Admin vs. Teacher/Student).