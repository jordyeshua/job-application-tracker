import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from database import query, execute

app = Flask(__name__)
app.secret_key = 'change-me-for-production'


def clean(value):
    value = (value or '').strip()
    return value if value else None


JOB_TYPES = ['Full-time', 'Part-time', 'Contract', 'Internship']


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
    return redirect(url_for('companies'))


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


if __name__ == '__main__':
    app.run(debug=True)
