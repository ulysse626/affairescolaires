import os
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'une_cle_secrete_pour_les_messages'  # Nécessaire pour utiliser flash()

# Une petite liste de test pour stocker les objets de troc en mémoire
objets_troc = [
    {"id": 1, "titre": "Livre de Maths 4ème", "categorie": "Livres", "contact": "eleve1@ecole.fr"},
    {"id": 2, "titre": "Calculatrice scientifique", "categorie": "Matériel", "contact": "eleve2@ecole.fr"}
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/objets')
def liste_objets():
    return render_template('objets.html', objets=objets_troc)

@app.route('/ajouter', methods=['GET', 'POST'])
def ajouter_objet():
    if request.method == 'POST':
        titre = request.form.get('titre')
        categorie = request.form.get('categorie')
        contact = request.form.get('contact')
        
        if titre and categorie and contact:
            nouveau_id = len(objets_troc) + 1
            objets_troc.append({
                "id": nouveau_id,
                "titre": titre,
                "categorie": categorie,
                "contact": contact
            })
            flash("Objet ajouté avec succès pour le troc !", "success")
            return redirect(url_for('liste_objets'))
        else:
            flash("Veuillez remplir tous les champs.", "danger")
            
    return render_template('ajouter.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'troc_secret_key_super_securisee'

# Configuration pour le téléversement d'images
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Bases de données en mémoire
# users: username -> dict(password, balance, ref_code, referral_count, has_pass)
users = {}        
# listings: list of dict(id, title, category, price, seller, description, image_url, status)
listings = []     
# messages: list of dict(sender, receiver, item_title, text)
messages = []     
# ref_codes: ref_code -> username
ref_codes = {}    

listing_id_counter = 3

# Comptes de démo
users['Alex'] = {
    'password': generate_password_hash('123456'),
    'balance': 2.5,
    'ref_code': 'ALEX123',
    'referral_count': 10,
    'has_pass': True  # Privilégié pour la démo !
}
users['Sophie'] = {
    'password': generate_password_hash('123456'),
    'balance': 1.0,
    'ref_code': 'SOPHIE45',
    'referral_count': 3,
    'has_pass': False
}
ref_codes['ALEX123'] = 'Alex'
ref_codes['SOPHIE45'] = 'Sophie'

# Annonces de démo
listings.append({
    'id': 1,
    'title': 'Manuel de Mathématiques 4ème (Sésamath)',
    'category': 'Manuels scolaires',
    'price': 1.0,
    'seller': 'Alex',
    'description': 'Livre en très bon état, parfait pour le programme de 4ème.',
    'image_url': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500&q=80',
    'status': 'Disponible'
})
listings.append({
    'id': 2,
    'title': 'Manga Naruto Tome 1',
    'category': 'Mangas & Livres',
    'price': 0.5,
    'seller': 'Sophie',
    'description': 'Lu une seule fois, comme neuf !',
    'image_url': 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=500&q=80',
    'status': 'Disponible'
})

@app.route('/')
def home():
    user = None
    if 'username' in session:
        user = users.get(session['username'])

    # Tri des annonces : 
    # 1. Les annonces des vendeurs avec "has_pass" (Pass Privilégié) apparaissent EN HAUT.
    # 2. Les annonces les plus récentes ensuite.
    def sort_key(item):
        seller_data = users.get(item['seller'], {})
        is_privileged = seller_data.get('has_pass', False)
        return (not is_privileged, -item['id'])

    sorted_listings = sorted(listings, key=sort_key)
    return render_template('index.html', listings=sorted_listings, user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        sponsor_code = request.form.get('sponsor_code', '').strip().upper()

        if not username or not password:
            flash("Veuillez remplir tous les champs obligatoires.", "danger")
            return redirect(url_for('register'))

        if username in users:
            flash("Ce nom d'utilisateur est déjà pris.", "danger")
            return redirect(url_for('register'))

        user_ref_code = username.upper() + "123"
        new_user = {
            'password': generate_password_hash(password),
            'balance': 1.0,
            'ref_code': user_ref_code,
            'referral_count': 0,
            'has_pass': False
        }

        # Traitement du parrainage
        if sponsor_code:
            if sponsor_code in ref_codes:
                parrain_name = ref_codes[sponsor_code]
                parrain = users[parrain_name]
                
                # Bonus de jeton au parrain
                parrain['balance'] += 0.3
                parrain['referral_count'] += 1
                
                # Vérification du Pass Privilégié (10 parrainages)
                if parrain['referral_count'] >= 10 and not parrain['has_pass']:
                    parrain['has_pass'] = True
                    flash(f"Compte créé ! Votre parrain {parrain_name} a atteint 10 parrainages et débloqué le Pass Privilégié !", "success")
                else:
                    flash(f"Compte créé ! Votre parrain {parrain_name} a reçu +0.3 jeton ({parrain['referral_count']}/10 amism).", "success")
            else:
                flash("Code de parrainage invalide, mais votre compte est créé avec 1 jeton offert !", "warning")
        else:
            flash("Compte créé avec succès ! 1 jeton offert pour démarrer.", "success")

        users[username] = new_user
        ref_codes[user_ref_code] = username
        session['username'] = username
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = users.get(username)
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            flash(f"Ravi de vous revoir, {username} !", "success")
            return redirect(url_for('home'))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for('home'))

@app.route('/add_listing', methods=['GET', 'POST'])
def add_listing():
    if 'username' not in session:
        flash("Vous devez être connecté pour publier une annonce.", "warning")
        return redirect(url_for('login'))

    global listing_id_counter
    if request.method == 'POST':
        title = request.form['title'].strip()
        category = request.form['category']
        price = float(request.form['price'])
        description = request.form['description'].strip()

        image_url = 'https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=500&q=80'
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                image_url = url_for('static', filename='uploads/' + filename)

        listing_id_counter += 1
        new_item = {
            'id': listing_id_counter,
            'title': title,
            'category': category,
            'price': price,
            'seller': session['username'],
            'description': description,
            'image_url': image_url,
            'status': 'Disponible'
        }
        listings.append(new_item)
        flash("Votre annonce a été publiée avec succès !", "success")
        return redirect(url_for('home'))

    return render_template('add_listing.html')

@app.route('/buy/<int:item_id>')
def buy(item_id):
    if 'username' not in session:
        flash("Vous devez être connecté pour effectuer un échange.", "warning")
        return redirect(url_for('login'))

    buyer_name = session['username']
    buyer = users[buyer_name]
    item = next((i for i in listings if i['id'] == item_id), None)

    if not item or item['status'] != 'Disponible':
        flash("Cet objet n'est plus disponible.", "warning")
        return redirect(url_for('home'))

    if item['seller'] == buyer_name:
        flash("Vous ne pouvez pas réserver votre propre objet !", "warning")
        return redirect(url_for('home'))

    if buyer['balance'] < item['price']:
        flash(f"Solde insuffisant ! Il vous faut {item['price']} jeton(s).", "danger")
        return redirect(url_for('home'))

    # Transaction
    buyer['balance'] -= item['price']
    users[item['seller']]['balance'] += item['price']
    item['status'] = 'Réservé / Vendu'

    # Message automatique
    messages.append({
        'sender': buyer_name,
        'receiver': item['seller'],
        'item_title': item['title'],
        'text': f"Bonjour {item['seller']} ! Je viens de réserver votre objet '{item['title']}'. Quand pouvons-nous nous rencontrer ?"
    })

    flash(f"Réservation réussie ! Un message a été envoyé à {item['seller']}.", "success")
    return redirect(url_for('messages_page'))

@app.route('/messages', methods=['GET', 'POST'])
def messages_page():
    if 'username' not in session:
        flash("Connectez-vous pour accéder à la messagerie.", "warning")
        return redirect(url_for('login'))

    current_user = session['username']

    if request.method == 'POST':
        receiver = request.form['receiver'].strip()
        text = request.form['text'].strip()
        item_title = request.form.get('item_title', 'Échange Général')

        if receiver in users and text:
            messages.append({
                'sender': current_user,
                'receiver': receiver,
                'item_title': item_title,
                'text': text
            })
            flash("Message envoyé !", "success")
        else:
            flash("Destinataire introuvable ou message vide.", "danger")
        return redirect(url_for('messages_page'))

    user_messages = [m for m in messages if m['sender'] == current_user or m['receiver'] == current_user]
    return render_template('messages.html', user_messages=user_messages, user=users[current_user])

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
