from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, send_file
from flask_login import login_required, current_user
from .models import Note, File
from . import db
import json
import os
from werkzeug.utils import secure_filename, safe_join
import io



views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')

        if note is None or len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)

@views.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
            
    return jsonify({})

@views.route("/upload", methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')

        if file is None or file.filename == '':
            flash('You must upload a file to use this feature.', category='error')
        else:
            filename = secure_filename(file.filename)
            file_data = file.read()
            new_file = File(data=file_data, filename=filename, user_id=current_user.id)
            db.session.add(new_file)
            db.session.commit()
            print("File has been uploaded")
            flash('File Uploaded!', category='success')


    return render_template('upload.html', user=current_user)

@views.route('/files', methods=['GET'])
@login_required
def view_files():
    user_files = File.query.filter_by(user_id=current_user.id).all()
    return render_template('files.html', user=current_user, files=user_files)


@views.route("/open_file/<int:file_id>", methods=['GET'])
@login_required
def open_file(file_id):
    file = File.query.get(file_id)

    if file and file.user_id == current_user.id:
        # Save the file to a temporary location
        temp_filepath = safe_join('/tmp', file.filename)
        with open(temp_filepath, 'wb') as temp_file:
            temp_file.write(file.data)

        # Send the file as a response
        return send_file(
            temp_filepath,
            as_attachment=True,
            download_name=file.filename
        )
    else:
        flash('File not found or you do not have permission to access it.', category='error')
        return redirect(url_for('views.view_files'))

@views.route("/delete-file", methods=['POST'])
def delete_file():
    file_data = json.loads(request.data)
    file_id = file_data['fileId']
    file = File.query.get(file_id)
    if file:
        if file.user_id == current_user.id:
            db.session.delete(file)
            db.session.commit()
    
    return jsonify({})