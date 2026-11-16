# Job Application Tracker

A web application to help track job applications during the job search process.

## Features

- Monitor organizations and employment vacancies
- Keep track of applications made and their progress
- Document interviewing process (stages, interviewers, opinions, and next moves)
- Save phone numbers and other information about firms’ contacts
- Dashboard showing application statistics, application statuses, and recent applications.
- Job Match: input your competencies and see jobs listed according to percentage of fit, containing both the skills already possessed and lacking

## Tools


- MySQL Database
- Python with Flask
- HTML and CSS for the web interface


## Requirements


- Python 3.9 or later versions
- MySQL 8 operating locally (optional: MySQL Workbench)
- Git


## Getting Started


1. Clone the repository:


```
git clone https://github.com/jordyeshua/job-application-tracker.git
cd job-application-tracker
```


2. Install dependencies:


```
pip install -r requirements.txt
```


3. Execute schema.sql file in MySQL Workbench (open schema.sql file and hit the lightning bolt) or via a command line:


```
mysql -u root -p < schema.sql
```


This creates the job_tracker_app database and its four tables. The next execution will reset the tables. Also, the sample_data.sql file can be executed in the same way if you want to load sample data.

4. On the terminal from which you will run the application, set your MySQL password. The password obtained from the environment variable will not be coded in the program. 

For Windows:

set DB_PASSWORD=your_mysql_password

For macOS / Linux:

export DB_PASSWORD=your_mysql_password

The additional settings are indicated with their default values: DB_HOST=localhost, DB_USER=root, DB_NAME=job_tracker_app.

5. Start the application:
python app.py

6. Open the following URL in your web browser: http://127.0.0.1:5000

If Python or pip is not recognized on Windows, replace python with py and pip with py -m pip.

## How to Use

1. Create a company, then create jobs for it. In the job form, enter the required skills separated by commas. For example, one should write Python, SQL, Flask.
2. Submit applications for those jobs and change their status accordingly.
3. Add contacts in each company.
4. Go to Job Match and input your skills to see which jobs match you the most.

## Database

- Companies: Companies of your interest.
- Jobs: Job listings associated with a business (requirements is a JSON column).
- Applications: Applications submitted for a job (interview_data is a JSON column).
- Contacts: Individuals working for companies (related to a particular company).

Foreign keys use ON DELETE CASCADE, so deleting a company also removes its jobs, applications, and contacts.

## Troubleshooting

- The access is forbidden for user root since variable DB_PASSWORD is not configured in the terminal window from which the application is being executed.
- Unknown database job_tracker_app: run schema.sql first.
- The command python is not recognized (Windows), and it should be replaced by py.