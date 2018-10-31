from flask import redirect, request, render_template, session, flash
import flask_login
from . import name as bp_name, blueprint
# from .user import dm_table, User, get_iyo_login_url, password_protect


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect user if it is the first time here
    if not dm_table.db.count:
        return redirect("/{}/register".format(bp_name))

    # Redirect user if he is already logged in
    if flask_login.current_user.is_authenticated:
        return redirect("/")

    if request.method == 'POST':
        username = request.form['username']
        secret = request.form['password']
        user_id = dm_table.db.list()[0]
        user = dm_table.get(user_id)
        # TODO check hashed secret
        if user.secret and secret == user.secret and username == user.name:
            logged_user = User(user.id, user.name, user.email)
            flask_login.login_user(logged_user)
            next_url = request.args.get('next')
            return redirect(next_url or '/')
        flash("Wrong user or password")
    iyo_url = get_iyo_login_url()
    return render_template('user/login.html', iyo_url=iyo_url)


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect user if he has already configured the system
    if dm_table.db.count:
        return redirect("/{}/login".format(bp_name))

    # Redirect user if he is already logged in
    if flask_login.current_user.is_authenticated:
        return redirect("/")

    if request.method == 'POST':
        username = request.form['username']
        secret = request.form['password']
        secret_confirm = request.form['confirm_password']
        if secret == secret_confirm:
            user = dm_table.set(data={"name": username, "secret": secret})
            logged_user = User(user.id, user.name, user.email)
            flask_login.login_user(logged_user)
            next_url = request.args.get('next')
            return redirect(next_url or '/')
        else:
            flash("Password confirmation doesn't match")
    iyo_url = get_iyo_login_url()
    return render_template('user/register.html', iyo_url=iyo_url)


@blueprint.route('/protected')
@flask_login.login_required
def protected():
    return """
    Logged in as: %s <br/>
    User ID: %s <br/>
    """ % (flask_login.current_user.name, flask_login.current_user.id)


@blueprint.route('/passwd', methods=['GET', 'POST'])
def single_passwd():
    if request.method == 'POST':
        secret = request.form['password']
        if secret == session['current_passwd']:
            next_url = session['current_page']
            session[next_url] = True
            return redirect(next_url)
        else:
            flash('Invalid password provided')
    return render_template('user/passwd.html')


@blueprint.route('/protected-single')
@password_protect(passwd="123")
def protected_single():
    return "Logged in successfully"


@blueprint.route('/logout')
def logout():
    flask_login.logout_user()
    return 'Logged out'
