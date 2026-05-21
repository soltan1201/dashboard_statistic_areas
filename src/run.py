# run.py
from app import create_app
import warnings
warnings.filterwarnings("ignore", message="This is a development server.")

app = create_app()

if __name__ == '__main__':
    import os
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)