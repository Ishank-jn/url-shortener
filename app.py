from flask import Flask, render_template, request, redirect
import random
import string
import redis
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# Redis or Memcached configuration
cache = redis.Redis(host='localhost', port=6379, db=0)

# SQLite database configuration
conn = sqlite3.connect('url_mappings.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS url_mappings
             (short_url TEXT PRIMARY KEY, long_url TEXT, created_at TIMESTAMP)''')

# Function to generate a short URL
def generate_short_url():
    characters = string.ascii_letters + string.digits
    short_url = ''.join(random.choice(characters) for _ in range(6))
    return short_url

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        long_url = request.form['long_url']
        short_url = generate_short_url()
        url_mappings[short_url] = long_url
        cache.set(short_url, long_url)
        c.execute("INSERT INTO url_mappings (short_url, long_url, created_at) VALUES (?, ?, ?)", (short_url, long_url, datetime.now()))
        conn.commit()
        return render_template('index.html', short_url=request.host_url + short_url)
    return render_template('index.html')

@app.route('/<short_url>')
def redirect_short_url(short_url):
    long_url = cache.get(short_url)
    if long_url:
        return redirect(long_url)
    else:
        c.execute("SELECT long_url FROM url_mappings WHERE short_url=?", (short_url,))
        result = c.fetchone()
        if result:
            long_url = result[0]
            cache.set(short_url, long_url)
            return redirect(long_url)
        else:
            return "URL not found"

# Function to delete old URLs
def delete_old_urls(hours):
    cutoff_time = datetime.now() - timedelta(hours=hours)
    c.execute("DELETE FROM url_mappings WHERE created_at < ?", (cutoff_time,))
    conn.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    # Delete URLs that haven't been used for 24 hours
    delete_old_urls(24)