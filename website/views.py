from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, send_file, session
from flask_login import login_required, current_user
from .models import Note, File
from . import db
import json
import os
from werkzeug.utils import secure_filename, safe_join
import io
import speech_recognition as sr
import moviepy.editor as mp
import magic
import tempfile
import shutil



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

ALLOWED_EXTENSIONS = {'mp4'}
def allowed_file(filename):
    secure_filename_str = secure_filename(filename)
    return '.' in secure_filename_str and secure_filename_str.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_by_id(file_id):
    return File.query.get(file_id)


@views.route("/files", methods=['POST'])
@login_required
def transcribe():
    if request.method == 'POST':
        file_id = request.form.get('file_id')

        if file_id is None:
            flash('File ID is missing.', category='error')
            return redirect(url_for('views.transcribe'))  # Redirect to the appropriate page

        else:
            # Retrieve the file with file_id from your database or wherever you store file information
            file = get_file_by_id(file_id)

            if file is None:
                flash('File not found!', category='error')
            elif not allowed_file(file.filename):
                flash('File type not allowed. Please upload an .mp4 file.', category='error')
            else:
                flash('Transcription Complete!', category='success')
                return transcribe_video(file)
            
    
    return redirect(url_for('views.transcribe'))

def transcribe_video(file):
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    try:
        # Generate temporary paths for video and audio files
        temp_video_path = os.path.join(temp_dir, "temp_video.mp4")
        temp_audio_path = os.path.join(temp_dir, "temp_audio.wav")

        # Save the video data to a temporary file
        with open(temp_video_path, 'wb') as temp_video_file:
            temp_video_file.write(file.data)

        # Convert the video to audio
        video = mp.VideoFileClip(temp_video_path)
        audio_file = video.audio
        audio_file.write_audiofile(temp_audio_path)

        # Transcribe the audio
        r = sr.Recognizer()
        with sr.AudioFile(temp_audio_path) as source:
            data = r.record(source)
        text = r.recognize_google(data)

        # Save the transcribed text to a file
        transcript_file_path = os.path.join(temp_dir, "transcription.txt")
        with open(transcript_file_path, 'w') as transcript_file:
            transcript_file.write(text)


        return send_file(
            transcript_file_path,
            as_attachment=True,
            download_name="transcription.txt",
            mimetype="text/plain"
        )
    
    finally:
        # Clean up: Delete the temporary directory and its contents
        shutil.rmtree(temp_dir)