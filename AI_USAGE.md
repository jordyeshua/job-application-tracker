# AI Usage Documentation

## Tools Used
- Claude: I used it for project planning, SQL queries, Flask routes, debugging, and Git/GitHub help.

## Key Prompts
1. "What are the things needed to do at the initial phase of this project?" (with the project assignment and specification attached). Claude prepared a schedule to do this project step by step. I made schema.sql based on the table definitions given in the specification, and Claude told me why ON DELETE CASCADE is used for the foreign keys, so I included it into my schema.
2. I was provided with a step-by-step action plan for the project which was rather a phase-by-phase action plan, including next phases: setup, database, CRUD of one table at a time and also dashboard and Job Match.
3. Instructions on how to build the features in the right order were provided: companies CRUD, jobs CRUD, applications CRUD, contacts CRUD, and then the dashboard and Job Match.
4. I attached screenshots of errors, such as Python not being recognized and Git not being installed, and asked Claude how to fix them.
5. Throughout the project, I asked Claude to explain how the generated functions worked, including cascade deletes for foreign keys and how the different features operated.

## What Worked Well
- The Flask routes, templates, and SQL queries for the four tables were created by Claude with ease by following the same template for each.
- The validation process started with the earliest versions (required fields, salary range checks, and email/phone formatting).
- The Job Match algorithm works as follows – it takes each skill, converts it to lower case, removes leading space, counts how many skills are required from the job description, calculates the percentage of required skills, and sorts by that percent. Additionally, it points out the missing skills like in the example in the specifications.
- Claude tested the program before sending me the code by creating a mock database first and later using a working MySQL-compatible database with the schema and demo data, including cascade deletes and JSON columns.
- A number of screenshots of errors allowed me to realize exactly what to fix, e.g., py instead of python, git installation, user.name and user.email settings, and the necessity of running git reset prior to pulling.
- Description of each feature provided by Claude showed me how pages are connected with each other through SQL queries and databases.

## What I Modified
- I prepared the schema.sql file with a reference to the table definitions specified in the project specifications, and later I added ON DELETE CASCADE to the foreign keys once Claude provided clarification for this addition.
- I reused the GitHub repo I generated in Assignment 1 for the current project instead of setting a new repo, which included merging the repo contents to my local version of the project.
- I created a new database called job_tracker_app so the schema for this project does not mess with the previous tables from Assignment 1 to Assignment 7.
- I adjusted the system to work with my computer; I had to use py launcher, since python was not recognized; I also installed git and set my username and email on Git.
- I tested the web pages in my browser in terms of adding, modifying, and removing records before committing each feature.

## Lessons Learned
- The AI code must be executed and validated on my machine. It turned out that the problems were caused by something related to the setup (Python path, Git name), rather than the code itself.
- Providing an error message or screenshot led to a better solution than simply explaining the problem.
- Completing all CRUD operations for one table before moving to the next made it easier to identify errors and reuse the same approach for the remaining tables.
- Keeping the flexible data (such as job skills and interview notes) in JSON columns allowed to avoid having to create additional tables, but required searching JSON so Job Match performs it in Python.
- I learned how to operate the terminal for Git and GitHub: git init, git add, git commit, and git push, and solving problems that appeared (Git was not installed, name and email were missing, and there was a merge conflict in .gitignore that I resolved with git reset and git pull).