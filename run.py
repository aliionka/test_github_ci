from app import create_app
from app.config import config_dict

app = create_app(config_dict["development"])

if __name__ == "__main__":
    app.run(debug=True)
