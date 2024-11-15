#Harmonix python file

from flask import Flask, render_template, request, redirect, url_for, session, jsonify,flash
from sqlalchemy import or_,func,distinct,desc
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.secret_key = "this_is_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///DB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Song model
class Song(db.Model):
    __tablename__ = 'songs'
    song_id = db.Column(db.Integer, primary_key=True)
    genre = db.Column(db.String(50))
    song_name = db.Column(db.String(100))
    duration = db.Column(db.String(20))
    lyrics = db.Column(db.Text)
    creator_name = db.Column(db.String(100))
    song_path = db.Column(db.String(200))
    image_path = db.Column(db.Text(200))
    avg_rating = db.Column(db.Float)

# Creator model
class Creator(db.Model):
    __tablename__ = 'creator'
    creatorid = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    creatorname = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

# User model
class User(db.Model):
    __tablename__ = 'user'
    userid = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Playlist model
class Playlist(db.Model):
    __tablename__ = 'playlist'
    playlistid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer)
    playlistname = db.Column(db.Text)
    song_name = db.Column(db.Text, nullable=False)
    creator_name = db.Column(db.Text, nullable=False)

with app.app_context():
    db.create_all()


@app.route('/creator_login', methods=['GET', 'POST'])
def creator_login():
    if request.method == 'POST':
        creator_username = request.form['creatorUsername']
        creator_password = request.form['creatorPassword']
        creator = Creator.query.filter_by(creatorname=creator_username, password=creator_password).first()

        if creator:
            session['creator_id'] = creator.creatorid
            session['creator_name'] = creator.creatorname
            return redirect(url_for('creator'))
        else:
            return render_template('creator_login.html', error='Invalid creator credentials. Please try again.')

    return render_template('creator_login.html')

@app.route('/creator')
def creator():
    if 'creator_id' in session:
        creator_name = session['creator_name']

        total_songs = Song.query.filter_by(creator_name=creator_name).count()
        genre = Song.query.filter_by(creator_name=creator_name).first().genre
        avg_rating = Song.query.filter_by(creator_name=creator_name).with_entities(func.avg(Song.avg_rating)).scalar()
        avg_rating = avg_rating if avg_rating else 0
        songs = Song.query.filter_by(creator_name=creator_name).all()

        return render_template('creator.html', creator_name=creator_name, total_songs=total_songs, genre=genre, avg_rating=avg_rating, songs=songs)
    else:
        return redirect(url_for('creator_login'))

    
@app.route('/get_lyrics/<int:song_id>')
def get_lyrics(song_id):
    song = Song.query.get(song_id)
    if song:
        return song.lyrics
    else:
        return 'Lyrics not found'
    
@app.route('/add_song', methods=['POST'])
def add_song():
    if 'creator_id' in session:

        creator_name = session['creator_name']
        song_name = request.form['song_name']
        genre = request.form['genre']
        duration = request.form['duration']
        lyrics = request.form['lyrics']
        song_path = request.form['song_path']
        image_path = request.form['image_path']
        avg_rating = request.form['avg_rating']

        new_song = Song(
            genre=genre,
            song_name=song_name,
            duration=duration,
            lyrics=lyrics,
            creator_name=creator_name,
            song_path=song_path,
            image_path=image_path,
            avg_rating=avg_rating
        )

        db.session.add(new_song)
        db.session.commit()

        return redirect(url_for('creator'))
    else:
        return redirect(url_for('creator_login'))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip().lower()
    
    if query:
        search_results = Song.query.filter(
            (func.lower(Song.song_name).contains(query)) |
             func.lower(Song.genre).contains(query) |
             func.lower(Song.creator_name).contains(query) |
             func.cast(Song.avg_rating, db.String).contains(query)
        ).all()

        return render_template('user.html', songs=search_results, query=query)
    else:
        songs = Song.query.all()
        return render_template('user.html', songs=songs)
    
    
@app.route('/search_songs', methods=['GET'])
def search_songs():
    query = request.args.get('query', '').strip().lower()

    if query:
        search_results = Song.query.filter(func.lower(Song.song_name).contains(query)).all()

        return render_template('songs.html', search_results=search_results, query=query)
    else:
        all_songs = Song.query.all()
        return render_template('songs.html', songs=all_songs)
    
@app.route('/update_lyrics/<int:song_id>', methods=['POST'])
def update_lyrics(song_id):
    if 'creator_id' in session:
        creator_name = session['creator_name']
        edited_lyrics = request.json.get('lyrics')
        song = Song.query.filter_by(song_id=song_id, creator_name=creator_name).first()

        if song:
            song.lyrics = edited_lyrics
            db.session.commit()

            return jsonify({'message': 'Lyrics updated successfully'})
        else:
            return jsonify({'message': 'Song not found'}), 404
    else:
        return jsonify({'message': 'Not authorized'}), 403
    
@app.route('/user')
def user():
    songs = Song.query.all()
    return render_template('user.html', songs=songs)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['user_id'] = user.userid
            return redirect(url_for('user'))
        else:
            return render_template('login.html', error='Invalid user credentials. Please try again.')
    
    return render_template('login.html')

@app.route('/delete_song/<int:song_id>', methods=['DELETE'])
def delete_song(song_id):
    song = Song.query.get(song_id)

    if song:
        db.session.delete(song)
        db.session.commit()
        return jsonify({'message': 'Song deleted successfully'}), 200
    else:
        return jsonify({'message': 'Song not found'}), 404
    
@app.route('/user_dashboard')
def user_dashboard():
    return 'Welcome to the User Dashboard!'

@app.route('/admin')
def admin():
    num_users = db.session.query(func.count(User.userid)).scalar()
    num_creators = db.session.query(func.count(Creator.creatorid)).scalar()
    num_songs = db.session.query(func.count(Song.song_id)).scalar()
    num_playlists = db.session.query(func.count(distinct(Playlist.playlistname))).scalar()
    num_genres = db.session.query(func.count(Song.genre.distinct())).scalar()

    top_creators = (
        db.session.query(Creator.creatorname, func.avg(Song.avg_rating).label('average_rating'))
        .join(Song, Creator.creatorname == Song.creator_name)
        .group_by(Creator.creatorname)
        .order_by(desc('average_rating'))
        .limit(5)
        .all()
    )

    top_songs = (
        db.session.query(Song.song_name, func.avg(Song.avg_rating).label('average_rating'))
        .group_by(Song.song_name)
        .order_by(desc(func.avg(Song.avg_rating)))
        .limit(5)
        .all()
    )

    top_creators_dict = [{'creatorname': row.creatorname, 'average_rating': row.average_rating} for row in top_creators]
    top_songs_dict = [{'song_name': row.song_name, 'average_rating': row.average_rating} for row in top_songs]

    return render_template('admin.html', num_users=num_users, num_creators=num_creators,
                           num_songs=num_songs, num_playlists=num_playlists, num_genres=num_genres,
                           top_creators=top_creators_dict, top_songs=top_songs_dict)

    

@app.route('/songs')
def songs():
    return render_template('songs.html')


@app.route('/playlist')
def playlist():
    if 'user_id' in session:
        user_id = session['user_id']
        songs = Song.query.all()
        playlists = Playlist.query.filter_by(userid=user_id).distinct(Playlist.playlistname)
        unique_playlists = set(playlist.playlistname for playlist in playlists)

        return render_template('playlist.html', unique_playlists=unique_playlists,songs=songs,user_id=session['user_id'])
    else:
        return redirect(url_for('login')) 



@app.route('/flag_song/<int:song_id>', methods=['POST'])
def flag_song(song_id):
    selected_option = request.form.get('selected_option')
    return jsonify({'message': 'Song flagged successfully'})

@app.route('/create_playlist', methods=['POST'])
def create_playlist():
    if 'user_id' in session:
        user_id = session['user_id']
        playlist_name = request.form.get('playlist_name')

        if playlist_name:

            new_playlist = Playlist(
                userid=user_id,
                playlistname=playlist_name
            )

            db.session.add(new_playlist)
            db.session.commit()

            return redirect(url_for('playlist'))
        else:
            flash('Playlist name cannot be empty.', 'error')
            return redirect(url_for('playlist'))
    else:
        return redirect(url_for('login'))

@app.route('/add_to_playlist/<int:song_id>', methods=['POST'])
def add_to_playlist(song_id):
    if 'user_id' in session:
        user_id = session['user_id']
        playlist_name = request.form.get('playlist_name')

        if playlist_name:
            song = Song.query.get(song_id)

            if song:
                new_playlist = Playlist(
                    userid=user_id,
                    playlistname=playlist_name,
                    song_name=song.song_name,
                    creator_name=song.creator_name
                )

                db.session.add(new_playlist)
                db.session.commit()

                flash('Song added to playlist successfully.', 'success')
                return redirect(url_for('playlist'))
            else:
                flash('Song not found.', 'error')
                return redirect(url_for('playlist'))
        else:
            flash('Playlist name cannot be empty.', 'error')
            return redirect(url_for('playlist'))
    else:
        return redirect(url_for('login'))

@app.route('/get_songs/<playlist_name>')
def get_songs(playlist_name):
    if 'user_id' in session:
        user_id = session['user_id']
        songs = Playlist.query.filter_by(userid=user_id, playlistname=playlist_name).all()
        return jsonify([{'song_name': song.song_name, 'creator_name': song.creator_name} for song in songs])
    
    else:
        return jsonify({'error': 'User not logged in'}), 401
    
if __name__ == '__main__':
    app.run(debug=True)