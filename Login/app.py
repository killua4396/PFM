
from useradmin import create_app
if __name__ == "__main__":
    app = create_app('default')
    app.run(debug=True, port=8080)