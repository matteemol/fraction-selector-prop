# Importing required functions
import pandas
from poolify import *
from fpdf import FPDF, table
from flask import Flask, flash, render_template, request, abort, send_from_directory, send_file
from fileinput import filename

# Flask constructor
app = Flask(__name__)


# Index page
@app.route('/')
def index():
	return render_template('index.html')


# Link to download the template to complete with data
@app.route("/download")
def download():
  return send_file("fraction-sheet-template.xlsx")


# Upload function endpoint
@app.post('/upload')
def upload():
  # Read the File
  file = request.files['file']
  # save file in local directory
  file.save(file.filename)

  # Parse the data as a Pandas DataFrame type (1st row - Sample Info)
  sampleInfo = pandas.read_excel(file, sheet_name=0, header=None, nrows=1)

  # Select data from DataFrame (1st row - Sample Info)
  Br_num = sampleInfo[1][0]
  Col_num = int(sampleInfo[4][0])
  total_fractions_an = sampleInfo[7][0]

  # Pack sample info to be passed later to doit() function
  sample = (Br_num, Col_num, total_fractions_an)

# Parse the data as a Pandas DataFrame type (table with fractions information)
  tableData = pandas.read_excel(file, sheet_name=0, header=None,
                                    usecols='A:C', skiprows=2,
                                    nrows=total_fractions_an)
  fractionData = tableData.transpose()

# Create blank lists that will be populated with experimental data,
# that must be passed to doit()
  hu_list = []    # HU: Handling Unit = Fraction no.
  aper_list = []  # aper: Area Percent
  atot_list = []  # atot: Total Area
  input_data = [] # all the data transformed into a list

# Populate the lists with the experimental data from the imported pandas dataframe
  i = 0
  while i < total_fractions_an:
    hu_list.append(int(fractionData[i][0]))
    aper_list.append(float(fractionData[i][1]))
    atot_list.append(float(fractionData[i][2]))
    input_data.append([int(fractionData[i][0]), fractionData[i][1], fractionData[i][2]])
    i +=1

# Run the main function doit(), from poolify.py module
  try:
    doit(sample, hu_list, aper_list, atot_list, input_data)
  except:
    abort(404)

  return send_file("bulletin.pdf")


# Custom 404 Not Found page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# Main Driver Function
if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0')