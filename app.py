from flask import Flask, render_template, request, redirect, url_for, flash
from database import query, execute

app = Flask(__name__)
app.secret_key = 'change-me-for-production'


def clean(value):
    value = (value or '').strip()
    return value if value else None


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


if __name__ == '__main__':
    app.run(debug=True)
