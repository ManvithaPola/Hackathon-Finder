from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

@app.route('/')
def index():
    # Read hackathon data
    df = pd.read_csv('hackathons_final.csv')

    # Ensure Date and ScrapedAt are in string format
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').astype(str)
    if 'ScrapedAt' in df.columns:
        df['ScrapedAt'] = pd.to_datetime(df['ScrapedAt'], errors='coerce').astype(str)
    else:
        df['ScrapedAt'] = ''

    # Fill missing columns
    for col in ['Location','Mode','Source','Title','Link']:
        if col not in df.columns:
            df[col] = 'Unknown'

    # Convert dataframe to list of dicts for template
    hackathons = df.to_dict(orient='records')

    return render_template('index.html', hackathons=hackathons)

if __name__ == '__main__':
    app.run(debug=True)
