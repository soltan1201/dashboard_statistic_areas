# run.py
from app import create_app
import warnings
warnings.filterwarnings("ignore", message="This is a development server.")

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=True)