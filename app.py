import os
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'une_cle_secrete_pour_tendance'

# Liste de test pour stocker les objets de troc
objets_troc = [
    {"id": 1, "titre": "Livre de Maths 4ème", "categorie": "Livres", "contact": "eleve1@ecole.fr"},
    {"id": 2, "titre": "Calculatrice scientifique", "categorie": "Matériel", "contact": "eleve2@ecole.fr"}
]

messages = []
users = {"eleve1": "Élève 1", "eleve2": "Élève 2"}
current_user = "eleve1"

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

@app.route('/messages', methods=['GET', 'POST'])
def messages_page():
    global current_user
    if request.method == 'POST':
        receiver = request.form.get('receiver')
        text = request.form.get('text', '').strip()
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
    return render_template('messages.html', user_messages=user_messages, user=users.get(current_user, "Utilisateur"))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
