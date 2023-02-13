#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy import func
import sys
from datetime import datetime

from models import setup_db, db, Artist, Venue, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
setup_db(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

def get_venue_by_city(venues, city):
  filtered_venues = list(filter(lambda venue: venue.city == city, venues))

  formatted_venues = list(map(lambda venue: {
    "id": venue.id,
    "name": venue.name,
    "num_upcoming_shows": len(list(filter(lambda show: show.start_time > datetime.now(), venue.shows))),
  }, filtered_venues))

  return formatted_venues

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  cities = db.session.query(Venue.city,
   func.count(Venue.city)
   ).group_by(Venue.city)
  venues = db.session.query(Venue).all()

  formatted_venues = [{
    'city': city[0],
    'venues': get_venue_by_city(venues, city[0])
  } for city in cities]

  data=[{
    "city": "San Francisco",
    "state": "CA",
    "venues": [{
      "id": 1,
      "name": "The Musical Hop",
      "num_upcoming_shows": 0,
    }, {
      "id": 3,
      "name": "Park Square Live Music & Coffee",
      "num_upcoming_shows": 1,
    }]
  }, {
    "city": "New York",
    "state": "NY",
    "venues": [{
      "id": 2,
      "name": "The Dueling Pianos Bar",
      "num_upcoming_shows": 0,
    }]
  }]
  return render_template('pages/venues.html', areas=formatted_venues);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search = request.form.get('search_term', '')

  try:
    selection = Venue.query.filter(
      Venue.name.ilike('%{}%'.format(search))
    ).all()

    formatted_selection = list(map(lambda venue: {
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': len(list(filter(lambda show: show.start_time > datetime.now(), venue.shows)))
    }, selection))

    formatted_data = {
      'count': len(selection),
      'data': formatted_selection,
    }

    return render_template('pages/search_venues.html', results=formatted_data, search_term=request.form.get('search_term', ''))
  except:
    abort(422)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  error_id = 500

  try:
    venue = Venue.query.get(venue_id)
    upcoming_shows = list(filter(lambda show: show.start_time > datetime.now(), venue.shows))
    past_shows = list(filter(lambda show: show.start_time <= datetime.now(), venue.shows))

    venue.upcoming_shows = list(map(lambda show: {
    'artist_id': show.artist.id,
    'artist_name': show.artist.name,
    'artist_image_link': show.artist.image_link,
    'start_time': show.start_time.strftime("%Y-%m-%dT%X"),
    }, upcoming_shows))
    venue.past_shows = list(map(lambda show: {
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%dT%X"),
    }, past_shows))

    if venue is None:
      error_id = 404
      abort(error_id)

    return render_template('pages/show_venue.html', venue=venue)

  except:
    abort(error_id)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  data = request.form

  try:
    name = data['name']
    city = data['city']
    state = data['state']
    address = data['address']
    phone = data['phone']
    image_link = data['image_link']
    facebook_link = data['facebook_link']
    genres = ','.join(data.getlist('genres'))
    website_link = data['website_link']
    seeking_talent = 'seeking_talent' in data
    seeking_description = data['seeking_description']

    venue = Venue(
      name = name, 
      city = city, 
      state = state, 
      address = address, 
      phone = phone, 
      image_link = image_link, 
      facebook_link = facebook_link, 
      genres = genres, 
      website = website_link, 
      seeking_talent = seeking_talent, 
      seeking_description = seeking_description
    )

    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/delete', methods=['POST'])
def delete_venue(venue_id):
  print(venue_id)

  venue = Venue.query.get(venue_id)

  if venue is None:
    abort(404)

  try:
    db.session.delete(venue)
    db.session.commit()
  except:
    print(sys.exc_info())
    db.session.rollback()
    abort(422)
  
  flash('Venue was successfully deleted.')
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = db.session.query(Artist).with_entities(Artist.id, Artist.name).order_by(Artist.id).all()
  formatted_response = [{'id': artist[0], 'name': artist[1]} for artist in artists]
  
  return render_template('pages/artists.html', artists=formatted_response)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search = request.form.get('search_term', '')

  response={
    "count": 1,
    "data": [{
      "id": 4,
      "name": "Guns N Petals",
      "num_upcoming_shows": 0,
    }]
  }

  try:
    selection = Artist.query.filter(
      Artist.name.ilike('%{}%'.format(search))
    ).all()

    formatted_selection = list(map(lambda artist: {
      'id': artist.id,
      'name': artist.name,
      'num_upcoming_shows': len(list(filter(lambda show: show.start_time > datetime.now(), artist.shows)))
    }, selection))
    
    # print(upcoming_shows)
    formatted_data = {
      'count': len(selection),
      'data': formatted_selection,
    }

    print(formatted_data)

    return render_template('pages/search_artists.html', results=formatted_data, search_term=request.form.get('search_term', ''))
  except:
    abort(422)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  upcoming_shows = list(filter(lambda show: show.start_time > datetime.now(), artist.shows))
  past_shows = list(filter(lambda show: show.start_time <= datetime.now(), artist.shows))

  artist.upcoming_shows = list(map(lambda show: {
    'venue_id': show.venue.id,
    'venue_name': show.venue.name,
    'venue_image_link': show.venue.image_link,
    'start_time': show.start_time.strftime("%Y-%m-%dT%X"),
  }, upcoming_shows))
  artist.past_shows = list(map(lambda show: {
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%dT%X"),
    }, past_shows))

  data1={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "past_shows": [{
      "venue_id": 1,
      "venue_name": "The Musical Hop",
      "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
      "start_time": "2019-05-21T21:30:00.000Z"
    }],
    "upcoming_shows": [],
    "past_shows_count": 1,
    "upcoming_shows_count": 0,
  }
  data2={
    "id": 5,
    "name": "Matt Quevedo",
    "genres": ["Jazz"],
    "city": "New York",
    "state": "NY",
    "phone": "300-400-5000",
    "facebook_link": "https://www.facebook.com/mattquevedo923251523",
    "seeking_venue": False,
    "image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "past_shows": [{
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2019-06-15T23:00:00.000Z"
    }],
    "upcoming_shows": [],
    "past_shows_count": 1,
    "upcoming_shows_count": 0,
  }
  data3={
    "id": 6,
    "name": "The Wild Sax Band",
    "genres": ["Jazz", "Classical"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "432-325-5432",
    "seeking_venue": False,
    "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "past_shows": [],
    "upcoming_shows": [{
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2035-04-01T20:00:00.000Z"
    }, {
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2035-04-08T20:00:00.000Z"
    }, {
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2035-04-15T20:00:00.000Z"
    }],
    "past_shows_count": 0,
    "upcoming_shows_count": 3,
  }
  # data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  if artist is None:
    abort(404)

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  data = request.form
  artist = Artist.query.get(artist_id)

  if artist is None:
    abort(404)

  try:
    artist.name = data['name']
    artist.city = data['city']
    artist.state = data['state']
    artist.phone = data['phone']
    artist.genres = ','.join(data.getlist('genres'))
    artist.facebook_link = data['facebook_link']
    artist.image_link = data['image_link']
    artist.website_link = data['website_link']
    artist.seeking_venue = 'seeking_venue' in data
    artist.seeking_description = data['seeking_description']

    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  if error:
    flash('An error occures. Couldn\'t update' + artist.name + '!')
  else:
    flash(artist.name + ' was successfully updated!')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  if venue is None:
    abort(404)

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  data = request.form
  venue = Venue.query.get(venue_id)

  if venue is None:
    abort(404)

  try:
    venue.name = data['name']
    venue.city = data['city']
    venue.state = data['state']
    venue.phone = data['phone']
    venue.genres = ','.join(data.getlist('genres'))
    venue.facebook_link = data['facebook_link']
    venue.image_link = data['image_link']
    venue.website = data['website_link']
    venue.seeking_talent = 'seeking_talent' in data
    venue.seeking_description = data['seeking_description']

    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  if error:
    flash('An error occures. Couldn\'t update' + venue.name + '!')
  else:
    flash(venue.name + ' was successfully updated!')

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  form = ArtistForm()
  data = request.form

  try:
    name = data['name']
    city = data['city']
    state = data['state']
    phone = data['phone']
    genres = ','.join(data.getlist('genres'))
    facebook_link = data['facebook_link']
    image_link = data['image_link']
    website_link = data['website_link']
    seeking_venue = 'seeking_venue' in data
    seeking_description=data['seeking_description']

    artist = Artist(name=name,
      city=city,
      state=state,
      phone=phone,
      genres=genres,
      facebook_link=facebook_link,
      image_link=image_link,
      website_link=website_link,
      seeking_venue=seeking_venue,
      seeking_description=seeking_description
    )

    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    flash('An error occurred. ', request.form['name'] + ' could not be added!')
    return render_template('forms/new_artist.html', form=form)
  else:
    flash(request.form['name'] + ' was successfully added!')
    return render_template('forms/new_artist.html', form=form)

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.all()

  formatted_data = [
    {
      'venue_id': show.venue.id,
      'venue_name': show.venue.name,
      'artist_id': show.artist.id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time.strftime("%Y-%m-%dT%X"),
    } for show in shows 
  ]

  data=[{
    "venue_id": 1,
    "venue_name": "The Musical Hop",
    "artist_id": 4,
    "artist_name": "Guns N Petals",
    "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "start_time": "2019-05-21T21:30:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 5,
    "artist_name": "Matt Quevedo",
    "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "start_time": "2019-06-15T23:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-01T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-08T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-15T20:00:00.000Z"
  }]
  return render_template('pages/shows.html', shows=formatted_data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  data = request.form

  try:
    artist_id = data['artist_id']
    venue_id = data['venue_id']
    start_time = data['start_time']

    artist = Artist.query.get(artist_id)
    venue = Venue.query.get(venue_id)

    if artist is None or venue is None:
      error = True
      db.session.rollback()
      abort()

    show = Show(
      artist_id = artist_id,
      venue_id = venue_id,
      start_time = start_time,
    )

    db.session.add(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    flash('An error occurred. Show could not be listed.')
    return render_template('pages/home.html')
  else:
    flash('Show was successfully listed!')
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
