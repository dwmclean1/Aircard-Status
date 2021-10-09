from logging import log
import time
import dotenv
from flask.helpers import url_for

from aircardstatus import *
from atcommands import *
from flask import Flask, render_template, request, flash
from werkzeug.utils import redirect
from rich.console import Console 
from rich.logging import RichHandler

app = Flask(__name__)

# Log Formatting
logging.basicConfig(level=logging.DEBUG, format='%(message)s', handlers=[RichHandler()])
console = Console()

# LOAD MODEM ADDRESS
env_path = Path('.')/'.env'
dotenv.load_dotenv(dotenv_path=env_path)

# SET MODEM ADDRESS
@app.route("/settings", methods=['POST'])
def settings():
    if request.method == "POST":

        os.environ['HOST'] = request.form['host']
        os.environ['PORT'] = request.form['port']

        dotenv.set_key('.env', 'HOST', os.environ['HOST'])
        dotenv.set_key('.env', 'PORT', os.environ['PORT'])

        return redirect(url_for("index"))

# -- SET BANDMASK 
@app.route("/setBandmask", methods=['POST'])
def setBandmask():

    if request.method == "POST":

        new_bandmask = request.form.getlist('band')
        command = encode_bandmask(new_bandmask)
        
        s = modemSession()
        s.connect()
        s.sendCommand(command) 
        s.close()
        
        time.sleep(2)

        return redirect(url_for("index"))

    
# -- POWER MODES
@app.route("/power", methods=['POST'])
def power():

    if request.method == "POST":
        
        command = request.form.get('power')

        s = modemSession()
        s.connect()
        s.sendCommand(PWRMODE[command]) 
        s.close()

        if command == "reboot":
            time.sleep(60)
            return redirect(url_for("index"))

        time.sleep(2)

        return

# -- INDEX 
@app.route("/", methods=["GET"])
def index():

    if request.method == "GET":

        endpoint = {"host": os.environ['HOST'], "port": os.environ['PORT']}

        s = modemSession()
        result = s.connect()
    
        if isinstance(result, Exception) is True:
            return render_template("error.html", error=result, endpoint=endpoint)

        make = s.sendCommand(MAKE)
        make = parse(make) 
        model = s.sendCommand(MODEL)
        model = parse(model) 
         
        # Modem status
        status = s.sendCommand(STATUS) 
        status = parse(status)

        # Signal Bars
        bars = s.sendCommand(SIGNALQ)
        bars = signalBars(bars)

        # Bandmask info
        bandmask = s.sendCommand(BANDMASK)
        bandmask = parse(bandmask)

        s.close()

        logData(status.connection_data)

        return render_template('table.html', bandmask=bandmask, status=status, make=make, model=model, bars=bars, endpoint=endpoint)
    