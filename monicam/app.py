from flask import Flask, render_template, request, redirect, url_for, session, flash
import firebase_admin
from firebase_admin import credentials, auth, db
import os
from functools import wraps
import time

#config firebase

FIREBASE_CREDENTIALS_PATH = 'monicam-71f84-firebase-adminsdk-fbsvc-143937e60e.json'
FIREBASE_DB_URL = 'https://monicam-71f84-default-rtdb.firebaseio.com/'
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'chave_super_forte_monicam')


def create_app():
    app = Flask(__name__)
    app.secret_key = FLASK_SECRET_KEY

#inicializacao do firebase
    try:
        if not firebase_admin._apps:
            if os.path.exists(FIREBASE_CREDENTIALS_PATH):
                cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})
                print("Firebase inicializado com sucesso!")
            else:
                print("Arquivo de credenciais não encontrado.")
    except Exception as e:
        print(f"Erro ao inicializar Firebase: {e}")

#registro de rotas
    app.add_url_rule('/', view_func=index_redirect)
    app.add_url_rule('/login', view_func=login, methods=['GET', 'POST'])
    app.add_url_rule('/logout', view_func=logout)
    app.add_url_rule('/cadastro', view_func=cadastro, methods=['GET', 'POST'])
    app.add_url_rule('/cadastro/sucesso/<int:id>', view_func=cadastro_sucesso)
    app.add_url_rule('/dashboard', view_func=dashboard)
    app.add_url_rule('/computadores', view_func=listar_computadores)
    app.add_url_rule('/computador/editar/<uid>', view_func=editar_computador, methods=['GET','POST'])
    app.add_url_rule('/computador/deletar/<uid>', view_func=deletar_computador)
    app.add_url_rule('/api/data', view_func=receber_dados, methods=['POST'])
    
#filtro de data para templates
    @app.template_filter('datetimeformat')
    def datetimeformat(value):
        import datetime
        return datetime.datetime.fromtimestamp(value).strftime('%d/%m/%Y %H:%M:%S')
    
    return app


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash("Faça login para acessar esta página.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def get_next_computer_id():
#colocar o contador de computadores no firebase
    try:
        ref = db.reference('metadata/computer_id_counter')
        def transaction(current):
            return 1 if current is None else current + 1
        result = ref.transaction(transaction)
        if isinstance(result, int):
            return result
        elif hasattr(result, 'snapshot'):
            return result.snapshot.val()
        return ref.get()
    except Exception as e:
        print(f"Erro ao gerar ID sequencial: {e}")
        return None


#rotas convencionais

def index_redirect():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))

def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash("Preencha email e senha.", "error")
            return render_template('login.html')
        try:
            user = auth.get_user_by_email(email)  #simular a autentificacao
            session['user_id'] = user.uid
            session['user_email'] = user.email
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for('dashboard'))
        except firebase_admin.exceptions.FirebaseError:
            flash("Credenciais inválidas.", "error")
    return render_template('login.html')

def logout():
    session.clear()
    flash("Logout realizado com sucesso.", "success")
    return redirect(url_for('login'))

def cadastro():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if len(password) < 6:
            flash("Senha deve ter ao menos 6 caracteres.", "error")
            return render_template('cadastro.html')
        try:
            user = auth.create_user(email=email, password=password)
            computer_id = get_next_computer_id()
            if computer_id is not None:
                db.reference(f'computers/{user.uid}').set({
                    'computer_id': computer_id,
                    'email': email,
                    'created_at': time.time()
                })
                session['user_id'] = user.uid
                session['user_email'] = user.email
                flash("Cadastro realizado com sucesso!", "success")
                return redirect(url_for('cadastro_sucesso', id=computer_id))
            else:
                auth.delete_user(user.uid)
                flash("Erro ao gerar ID. Tente novamente.", "error")
        except firebase_admin.exceptions.FirebaseError as e:
            flash("Erro ao cadastrar: " + str(e), "error")
    return render_template('cadastro.html')

@login_required
def cadastro_sucesso(id):
    return render_template('cadastro_sucesso.html', computer_id=id)

@login_required
def dashboard():
    computers_ref = db.reference('computers')
    computers = computers_ref.get() or {}
    return render_template('dashboard.html', email=session.get('user_email','Usuário'), computers=computers)

@login_required
def listar_computadores():
    computers_ref = db.reference('computers')
    computers = computers_ref.get() or {}
    return render_template('computadores_list.html', computers=computers)

@login_required
def editar_computador(uid):
    comp_ref = db.reference(f'computers/{uid}')
    computer = comp_ref.get()
    if request.method == 'POST':
        email = request.form.get('email')
        comp_ref.update({'email': email})
        flash("Alterações salvas.", "success")
        return redirect(url_for('listar_computadores'))
    return render_template('computador_edit.html', computer=computer)

@login_required
def deletar_computador(uid):
    try:
        db.reference(f'computers/{uid}').delete()
        auth.delete_user(uid)
        flash("Computador deletado com sucesso.", "success")
    except Exception as e:
        flash(f"Erro ao deletar computador: {e}", "error")
    return redirect(url_for('listar_computadores'))

def receber_dados():
#receber os dados e atualiza-los 
    data = request.get_json()
    if not data or 'computer_id' not in data:
        return {"message":"Dados inválidos"}, 400
    try:
        ref = db.reference(f'computers')
        for uid, comp in ref.get().items():
            if comp['computer_id'] == data['computer_id']:
                ref.child(uid).update(data)
                return {"message":"Dados atualizados com sucesso!"}, 200
    except Exception as e:
        return {"message": f"Erro: {e}"}, 500
    return {"message":"Computador não encontrado"}, 404


#execucao

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
