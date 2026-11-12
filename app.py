import json
import re
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash
from database import query, execute

app = Flask(__name__)
app.secret_key = 'change-me-for-production'


def clean(value):
    value = (value or '').strip()
    return value if value else None


JOB_TYPES = ['Full-time', 'Part-time', 'Contract', 'Internship']
STATUSES = ['Applied', 'Screening', 'Interview', 'Offer', 'Rejected', 'Withdrawn']


def parse_requirements(value):
    """JSON column can come back as str, dict, or None."""
    if not value:
        return {}
    if isinstance(value, (bytes, bytearray)):
        value = value.decode()
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return {}
    return value if isinstance(value, dict) else {}


def skills_to_text(requirements):
    skills = parse_requirements(requirements).get('required_skills', [])
    return ', '.join(skills)


def parse_skills(text):
    seen, skills = set(), []
    for part in (text or '').split(','):
        skill = part.strip()
        if skill and skill.lower() not in seen:
            seen.add(skill.lower())
            skills.append(skill)
    return skills


def parse_int(value, label, errors):
    value = (value or '').strip()
    if not value:
        return None
    if not value.isdigit():
        errors.append(f'{label} must be a whole number (digits only).')
        return None
    return int(value)


def validate_job(form):
    errors = []
    title = clean(form.get('job_title'))
    if not title:
        errors.append('Job title is required.')
    company_id = form.get('company_id', '').strip()
    if not company_id.isdigit() or not query(
            'SELECT company_id FROM companies WHERE company_id = %s', (company_id,), one=True):
        errors.append('Please choose a company.')
    job_type = clean(form.get('job_type'))
    if job_type and job_type not in JOB_TYPES:
        errors.append('Invalid job type.')
    salary_min = parse_int(form.get('salary_min'), 'Minimum salary', errors)
    salary_max = parse_int(form.get('salary_max'), 'Maximum salary', errors)
    if salary_min is not None and salary_max is not None and salary_min > salary_max:
        errors.append('Minimum salary cannot be greater than maximum salary.')
    date_posted = clean(form.get('date_posted'))
    if date_posted:
        try:
            datetime.strptime(date_posted, '%Y-%m-%d')
        except ValueError:
            errors.append('Date posted must be a valid date.')
    values = {
        'company_id': int(company_id) if company_id.isdigit() else None,
        'job_title': title,
        'job_type': job_type,
        'salary_min': salary_min,
        'salary_max': salary_max,
        'job_url': clean(form.get('job_url')),
        'date_posted': date_posted,
    }
    return errors, values


def validate_application(form):
    errors = []
    job_id = form.get('job_id', '').strip()
    if not job_id.isdigit() or not query(
            'SELECT job_id FROM jobs WHERE job_id = %s', (job_id,), one=True):
        errors.append('Please choose a job.')
    app_date = clean(form.get('application_date'))
    if not app_date:
        errors.append('Application date is required.')
    else:
        try:
            datetime.strptime(app_date, '%Y-%m-%d')
        except ValueError:
            errors.append('Application date must be a valid date.')
    status = clean(form.get('status')) or 'Applied'
    if status not in STATUSES:
        errors.append('Invalid status.')
    resume = clean(form.get('resume_version'))
    if resume and len(resume) > 50:
        errors.append('Resume version must be 50 characters or fewer.')
    rounds = clean(form.get('interview_rounds'))
    if rounds and not rounds.isdigit():
        errors.append('Interview rounds must be a whole number.')
    values = {
        'job_id': int(job_id) if job_id.isdigit() else None,
        'application_date': app_date,
        'status': status,
        'resume_version': resume,
        'cover_letter_sent': 1 if form.get('cover_letter_sent') else 0,
    }
    return errors, values


def build_interview_data(form, existing=None):
    data = parse_requirements(existing)
    rounds = clean(form.get('interview_rounds'))
    if rounds and rounds.isdigit():
        data['interview_rounds'] = int(rounds)
    else:
        data.pop('interview_rounds', None)
    interviewers = parse_skills(form.get('interviewers'))
    if interviewers:
        data['interviewers'] = interviewers
    else:
        data.pop('interviewers', None)
    for key in ('feedback', 'next_steps'):
        text = clean(form.get(key))
        if text:
            data[key] = text
        else:
            data.pop(key, None)
    return json.dumps(data) if data else None


def interview_fields(interview_data):
    data = parse_requirements(interview_data)
    return {
        'interview_rounds': data.get('interview_rounds', ''),
        'interviewers': ', '.join(data.get('interviewers', [])),
        'feedback': data.get('feedback', ''),
        'next_steps': data.get('next_steps', ''),
    }


EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
PHONE_RE = re.compile(r'^[0-9+\-().\s]{7,20}$')


def validate_contact(form):
    errors = []
    name = clean(form.get('contact_name'))
    if not name:
        errors.append('Contact name is required.')
    elif len(name) > 100:
        errors.append('Contact name must be 100 characters or fewer.')
    company_id = form.get('company_id', '').strip()
    if not company_id.isdigit() or not query(
            'SELECT company_id FROM companies WHERE company_id = %s', (company_id,), one=True):
        errors.append('Please choose a company.')
    email = clean(form.get('email'))
    if email and not EMAIL_RE.match(email):
        errors.append('Please enter a valid email address.')
    phone = clean(form.get('phone'))
    if phone and not PHONE_RE.match(phone):
        errors.append('Phone can only contain digits, spaces, + - ( ) . and must be 7-20 characters.')
    values = {
        'company_id': int(company_id) if company_id.isdigit() else None,
        'contact_name': name,
        'title': clean(form.get('title')),
        'email': email,
        'phone': phone,
        'linkedin_url': clean(form.get('linkedin_url')),
        'notes': clean(form.get('notes')),
    }
    return errors, values


def normalize_skill(skill):
    return ' '.join(str(skill).lower().split())


def rank_jobs(user_skills, jobs):
    """Rank jobs by the share of their required skills the user has.

    Returns (ranked, skipped) where skipped counts jobs with no required skills listed.
    """
    have = {normalize_skill(s) for s in user_skills}
    ranked, skipped = [], 0
    for job in jobs:
        required = parse_requirements(job.get('requirements')).get('required_skills', [])
        required = [s for s in required if str(s).strip()]
        if not required:
            skipped += 1
            continue
        matched = [s for s in required if normalize_skill(s) in have]
        missing = [s for s in required if normalize_skill(s) not in have]
        percent = round(len(matched) * 100 / len(required))
        ranked.append({
            'job_id': job['job_id'],
            'job_title': job['job_title'],
            'company_name': job['company_name'],
            'percent': percent,
            'matched_count': len(matched),
            'total': len(required),
            'matched': matched,
            'missing': missing,
        })
    ranked.sort(key=lambda r: (-r['percent'], -r['matched_count'], r['total'], r['job_title'].lower()))
    return ranked, skipped


def build_requirements(skills_text, existing=None):
    data = parse_requirements(existing)
    skills = parse_skills(skills_text)
    if skills:
        data['required_skills'] = skills
    else:
        data.pop('required_skills', None)
    return json.dumps(data) if data else None


@app.route('/')
def dashboard():
    totals = query('''SELECT
            (SELECT COUNT(*) FROM companies) AS companies,
            (SELECT COUNT(*) FROM jobs) AS jobs,
            (SELECT COUNT(*) FROM applications) AS applications,
            (SELECT COUNT(*) FROM contacts) AS contacts''', one=True)
    status_counts = {s: 0 for s in STATUSES}
    for row in query('SELECT status, COUNT(*) AS count FROM applications GROUP BY status'):
        status_counts[row['status']] = row['count']
    total_apps = totals['applications']
    responded = total_apps - status_counts['Applied']
    response_rate = round(responded * 100 / total_apps) if total_apps else 0
    recent = query(APPLICATION_SELECT +
                   ' ORDER BY a.application_date DESC, a.application_id DESC LIMIT 5')
    return render_template('dashboard.html', totals=totals, status_counts=status_counts,
                           response_rate=response_rate, recent=recent)


# ---------- COMPANIES ----------
@app.route('/companies')
def companies():
    rows = query('SELECT * FROM companies ORDER BY company_name')
    return render_template('companies.html', companies=rows)


@app.route('/companies/add', methods=['GET', 'POST'])
def add_company():
    if request.method == 'POST':
        name = clean(request.form.get('company_name'))
        if not name:
            flash('Company name is required.', 'error')
            return render_template('company_form.html', company=request.form, title='Add Company')
        execute(
            '''INSERT INTO companies (company_name, industry, website, city, state, notes)
               VALUES (%s, %s, %s, %s, %s, %s)''',
            (name, clean(request.form.get('industry')), clean(request.form.get('website')),
             clean(request.form.get('city')), clean(request.form.get('state')),
             clean(request.form.get('notes')))
        )
        flash('Company added.', 'success')
        return redirect(url_for('companies'))
    return render_template('company_form.html', company={}, title='Add Company')


@app.route('/companies/<int:company_id>/edit', methods=['GET', 'POST'])
def edit_company(company_id):
    company = query('SELECT * FROM companies WHERE company_id = %s', (company_id,), one=True)
    if not company:
        flash('Company not found.', 'error')
        return redirect(url_for('companies'))
    if request.method == 'POST':
        name = clean(request.form.get('company_name'))
        if not name:
            flash('Company name is required.', 'error')
            return render_template('company_form.html', company=request.form, title='Edit Company')
        execute(
            '''UPDATE companies SET company_name=%s, industry=%s, website=%s,
               city=%s, state=%s, notes=%s WHERE company_id=%s''',
            (name, clean(request.form.get('industry')), clean(request.form.get('website')),
             clean(request.form.get('city')), clean(request.form.get('state')),
             clean(request.form.get('notes')), company_id)
        )
        flash('Company updated.', 'success')
        return redirect(url_for('companies'))
    return render_template('company_form.html', company=company, title='Edit Company')


@app.route('/companies/<int:company_id>/delete', methods=['POST'])
def delete_company(company_id):
    execute('DELETE FROM companies WHERE company_id = %s', (company_id,))
    flash('Company deleted.', 'success')
    return redirect(url_for('companies'))


# ---------- JOBS ----------
@app.route('/jobs')
def jobs():
    rows = query('''SELECT j.*, c.company_name
                    FROM jobs j JOIN companies c ON j.company_id = c.company_id
                    ORDER BY j.date_posted DESC, j.job_title''')
    for row in rows:
        row['skills'] = skills_to_text(row['requirements'])
    return render_template('jobs.html', jobs=rows)


@app.route('/jobs/add', methods=['GET', 'POST'])
def add_job():
    companies_list = query('SELECT company_id, company_name FROM companies ORDER BY company_name')
    if not companies_list:
        flash('Add a company first, then you can add jobs for it.', 'error')
        return redirect(url_for('add_company'))
    if request.method == 'POST':
        errors, values = validate_job(request.form)
        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('job_form.html', job=request.form, companies=companies_list,
                                   job_types=JOB_TYPES, title='Add Job')
        execute(
            '''INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max,
               job_url, date_posted, requirements) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
            (values['company_id'], values['job_title'], values['job_type'], values['salary_min'],
             values['salary_max'], values['job_url'], values['date_posted'],
             build_requirements(request.form.get('skills')))
        )
        flash('Job added.', 'success')
        return redirect(url_for('jobs'))
    return render_template('job_form.html', job={}, companies=companies_list,
                           job_types=JOB_TYPES, title='Add Job')


@app.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
def edit_job(job_id):
    job = query('SELECT * FROM jobs WHERE job_id = %s', (job_id,), one=True)
    if not job:
        flash('Job not found.', 'error')
        return redirect(url_for('jobs'))
    companies_list = query('SELECT company_id, company_name FROM companies ORDER BY company_name')
    if request.method == 'POST':
        errors, values = validate_job(request.form)
        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('job_form.html', job=request.form, companies=companies_list,
                                   job_types=JOB_TYPES, title='Edit Job')
        execute(
            '''UPDATE jobs SET company_id=%s, job_title=%s, job_type=%s, salary_min=%s,
               salary_max=%s, job_url=%s, date_posted=%s, requirements=%s WHERE job_id=%s''',
            (values['company_id'], values['job_title'], values['job_type'], values['salary_min'],
             values['salary_max'], values['job_url'], values['date_posted'],
             build_requirements(request.form.get('skills'), job['requirements']), job_id)
        )
        flash('Job updated.', 'success')
        return redirect(url_for('jobs'))
    job['skills'] = skills_to_text(job['requirements'])
    return render_template('job_form.html', job=job, companies=companies_list,
                           job_types=JOB_TYPES, title='Edit Job')


@app.route('/jobs/<int:job_id>/delete', methods=['POST'])
def delete_job(job_id):
    execute('DELETE FROM jobs WHERE job_id = %s', (job_id,))
    flash('Job deleted.', 'success')
    return redirect(url_for('jobs'))


# ---------- APPLICATIONS ----------
APPLICATION_SELECT = '''SELECT a.*, j.job_title, c.company_name
    FROM applications a
    JOIN jobs j ON a.job_id = j.job_id
    JOIN companies c ON j.company_id = c.company_id'''


def job_choices():
    return query('''SELECT j.job_id, j.job_title, c.company_name
                    FROM jobs j JOIN companies c ON j.company_id = c.company_id
                    ORDER BY c.company_name, j.job_title''')


@app.route('/applications')
def applications():
    status = request.args.get('status', '')
    if status in STATUSES:
        rows = query(APPLICATION_SELECT + ' WHERE a.status = %s ORDER BY a.application_date DESC',
                     (status,))
    else:
        status = ''
        rows = query(APPLICATION_SELECT + ' ORDER BY a.application_date DESC')
    return render_template('applications.html', applications=rows, statuses=STATUSES,
                           selected_status=status)


@app.route('/applications/<int:application_id>')
def view_application(application_id):
    row = query(APPLICATION_SELECT + ' WHERE a.application_id = %s', (application_id,), one=True)
    if not row:
        flash('Application not found.', 'error')
        return redirect(url_for('applications'))
    return render_template('application_detail.html', application=row,
                           interview=interview_fields(row['interview_data']))


@app.route('/applications/add', methods=['GET', 'POST'])
def add_application():
    jobs_list = job_choices()
    if not jobs_list:
        flash('Add a job first, then you can add applications for it.', 'error')
        return redirect(url_for('add_job'))
    if request.method == 'POST':
        errors, values = validate_application(request.form)
        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('application_form.html', application=request.form,
                                   jobs=jobs_list, statuses=STATUSES, title='Add Application')
        execute(
            '''INSERT INTO applications (job_id, application_date, status, resume_version,
               cover_letter_sent, interview_data) VALUES (%s, %s, %s, %s, %s, %s)''',
            (values['job_id'], values['application_date'], values['status'],
             values['resume_version'], values['cover_letter_sent'],
             build_interview_data(request.form))
        )
        flash('Application added.', 'success')
        return redirect(url_for('applications'))
    return render_template('application_form.html',
                           application={'application_date': date.today().isoformat(),
                                        'status': 'Applied'},
                           jobs=jobs_list, statuses=STATUSES, title='Add Application')


@app.route('/applications/<int:application_id>/edit', methods=['GET', 'POST'])
def edit_application(application_id):
    row = query('SELECT * FROM applications WHERE application_id = %s', (application_id,), one=True)
    if not row:
        flash('Application not found.', 'error')
        return redirect(url_for('applications'))
    jobs_list = job_choices()
    if request.method == 'POST':
        errors, values = validate_application(request.form)
        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('application_form.html', application=request.form,
                                   jobs=jobs_list, statuses=STATUSES, title='Edit Application')
        execute(
            '''UPDATE applications SET job_id=%s, application_date=%s, status=%s,
               resume_version=%s, cover_letter_sent=%s, interview_data=%s
               WHERE application_id=%s''',
            (values['job_id'], values['application_date'], values['status'],
             values['resume_version'], values['cover_letter_sent'],
             build_interview_data(request.form, row['interview_data']), application_id)
        )
        flash('Application updated.', 'success')
        return redirect(url_for('applications'))
    row.update(interview_fields(row['interview_data']))
    return render_template('application_form.html', application=row, jobs=jobs_list,
                           statuses=STATUSES, title='Edit Application')


@app.route('/applications/<int:application_id>/delete', methods=['POST'])
def delete_application(application_id):
    execute('DELETE FROM applications WHERE application_id = %s', (application_id,))
    flash('Application deleted.', 'success')
    return redirect(url_for('applications'))


# ---------- CONTACTS ----------
CONTACT_SELECT = '''SELECT ct.*, c.company_name
    FROM contacts ct JOIN companies c ON ct.company_id = c.company_id'''


@app.route('/contacts')
def contacts():
    companies_list = query('SELECT company_id, company_name FROM companies ORDER BY company_name')
    selected = request.args.get('company_id', '')
    if selected.isdigit():
        rows = query(CONTACT_SELECT + ' WHERE ct.company_id = %s ORDER BY ct.contact_name',
                     (int(selected),))
    else:
        selected = ''
        rows = query(CONTACT_SELECT + ' ORDER BY ct.contact_name')
    return render_template('contacts.html', contacts=rows, companies=companies_list,
                           selected_company=selected)


@app.route('/contacts/add', methods=['GET', 'POST'])
def add_contact():
    companies_list = query('SELECT company_id, company_name FROM companies ORDER BY company_name')
    if not companies_list:
        flash('Add a company first, then you can add contacts for it.', 'error')
        return redirect(url_for('add_company'))
    if request.method == 'POST':
        errors, v = validate_contact(request.form)
        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('contact_form.html', contact=request.form,
                                   companies=companies_list, title='Add Contact')
        execute(
            '''INSERT INTO contacts (company_id, contact_name, title, email, phone,
               linkedin_url, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)''',
            (v['company_id'], v['contact_name'], v['title'], v['email'], v['phone'],
             v['linkedin_url'], v['notes'])
        )
        flash('Contact added.', 'success')
        return redirect(url_for('contacts'))
    return render_template('contact_form.html', contact={}, companies=companies_list,
                           title='Add Contact')


@app.route('/contacts/<int:contact_id>/edit', methods=['GET', 'POST'])
def edit_contact(contact_id):
    contact = query('SELECT * FROM contacts WHERE contact_id = %s', (contact_id,), one=True)
    if not contact:
        flash('Contact not found.', 'error')
        return redirect(url_for('contacts'))
    companies_list = query('SELECT company_id, company_name FROM companies ORDER BY company_name')
    if request.method == 'POST':
        errors, v = validate_contact(request.form)
        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('contact_form.html', contact=request.form,
                                   companies=companies_list, title='Edit Contact')
        execute(
            '''UPDATE contacts SET company_id=%s, contact_name=%s, title=%s, email=%s,
               phone=%s, linkedin_url=%s, notes=%s WHERE contact_id=%s''',
            (v['company_id'], v['contact_name'], v['title'], v['email'], v['phone'],
             v['linkedin_url'], v['notes'], contact_id)
        )
        flash('Contact updated.', 'success')
        return redirect(url_for('contacts'))
    return render_template('contact_form.html', contact=contact, companies=companies_list,
                           title='Edit Contact')


@app.route('/contacts/<int:contact_id>/delete', methods=['POST'])
def delete_contact(contact_id):
    execute('DELETE FROM contacts WHERE contact_id = %s', (contact_id,))
    flash('Contact deleted.', 'success')
    return redirect(url_for('contacts'))


# ---------- JOB MATCH ----------
@app.route('/job-match')
def job_match():
    skills_text = request.args.get('skills', '').strip()
    user_skills = parse_skills(skills_text)
    results, skipped = [], 0
    if user_skills:
        rows = query('''SELECT j.job_id, j.job_title, j.requirements, c.company_name
                        FROM jobs j JOIN companies c ON j.company_id = c.company_id''')
        results, skipped = rank_jobs(user_skills, rows)
    return render_template('job_match.html', skills_text=skills_text, user_skills=user_skills,
                           results=results, skipped=skipped, searched=bool(user_skills))


if __name__ == '__main__':
    app.run(debug=True)
