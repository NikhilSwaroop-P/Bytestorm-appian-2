# Product Recommendation Web Interface

This is a web interface for the Product Recommendation system that processes image and text queries to provide relevant product recommendations.

## Features

- Two-column layout: products view on the left, chatbot interface on the right
- Upload images or provide text queries (or both)
- Interactive chatbot for user communication
- Dynamic product display based on search results
- Mobile-responsive design

## Running the Application

1. Make sure all dependencies are installed:

```
pip install -r requirements.txt
```

2. Run the Flask application:

```
python src/frontend/run.py
```

3. Open your browser and navigate to:

```
http://localhost:5000
```

## How It Works

The web interface communicates with the backend recommendation system via a Flask API:

1. When the user uploads an image or submits a text query, the input is sent to the API
2. The main_pipeline processes the request using visual and text analysis
3. Results are ranked and returned to the interface
4. Products are displayed in the left column

## Technical Details

- Built with Flask for the backend
- Uses plain JavaScript, HTML and CSS for the frontend
- Leverages the project's main_pipeline module for recommendation logic
- Handles both image and text inputs 