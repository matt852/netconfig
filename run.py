#!flask/bin/python
from app import app
app.run(host='127.0.0.1', port=5000, debug=True)
#app.run(debug=False, host='0.0.0.0', port=80)