import os
from dotenv import load_dotenv

# Loads variables from .env into os.environ before anything else
load_dotenv()

from flask_app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=os.environ.get("PORT", 5000))
