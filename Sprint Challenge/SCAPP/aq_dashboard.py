from flask import Flask, render_template, request
import requests
import openaq
from .models import DB, Record

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    DB.init_app(app)

    api = openaq.OpenAQ()

    @app.route('/')
    def root():
        """Base view."""
        records=Record.query.filter(Record.value >= 10).all()
        return render_template('base.html', measurements=records)

    def get_measurements():
        measurements = []
        try:
            status, body = api.measurements(city='Los Angeles', parameter='pm25')
            for x in body['results']:
                measurements.append((x['date']['utc'], x['value']))
        except Exception as e:
            print('Failed to get measurements: {}'.format(e))
        return measurements

    @app.route('/refresh')
    def refresh():
        """Pull fresh data from Open AQ and replace existing data."""
        DB.drop_all()
        DB.create_all()
        measurements = get_measurements()
        for x, id in zip(measurements, range(0,len(measurements))):
            DB.session.add(Record(id=id, datetime=x[0], value=x[1]))
        DB.session.commit()
        return render_template('refresh.html')
    
    return app