from flask import Flask, render_template, url_for, request, redirect, _app_ctx_stack, flash, get_flashed_messages
#Der kan importeres langt mindre
from sqlalchemy import Column, Integer, String, MetaData
from sqlalchemy.orm import scoped_session
from sqlalchemy.sql import exists
from datetime import datetime
from sqlalchconn import engine, LocalSession, Base
from storagemodels import component_lot, device, backupdevice
from datetime import date
import os

def readcomponents():
    componentsfile = open('components.txt','r')
    componentnames = {}
    componentstext = componentsfile.read()
    componentsfile.seek(0)    
    for line in componentsfile:
        key,val = line.split(':')
        componentnames[key] = val.rstrip()
    return componentnames,componentstext

#names er en dict som oversætter art nr til navn. Skal senere være muligt at tilføje on the go
names,namestext = readcomponents()
app = Flask(__name__)
app.secret_key = 'abc'
app.session = scoped_session(LocalSession,_app_ctx_stack.__ident_func__)
@app.route('/',methods=['POST','GET'])
def index():
    if request.method =='POST':
        print('post')         
    else:
        alldevices  = app.session.query(device.devicenr).all()
        alldevices = [ int(x[0]) for x in alldevices ]
        allLOT = app.session.query(component_lot)
        devices = app.session.query(device).get(chosendevicenr)
        return render_template('index.html',products = allLOT,names=names,devicedata=devices,devicenrs = alldevices)

@app.route('/devicemanager/')
def devicemanager():
    alldevices = app.session.query(device).all()
    deleteddevices = app.session.query(backupdevice).all()
    allsum = {}
    for thisdevice in alldevices:
        sumdevice = {}
        for name in names.values():
            print(name)
            n = thisdevice.contents.get(name,{}).values()
            sumdevice[name] = sum(n)
            print(n, sumdevice)
        devicenr = thisdevice.devicenr
        allsum[devicenr] = sumdevice
    return render_template('devicemanager.html',allsum=allsum,names=names,deleteddevices=deleteddevices)

@app.route('/addnew/',methods=['POST','GET'])
def addnew():
    if request.method == 'POST':
        #Data is entered in the newdata dict, and LOT number gets generated. The data is then used to instantiate the LOT shipment object
        newdata = {}
        for input in request.form:
            newdata[input]=request.form[input]
        newdata['lotnr'] = lotgenerator(newdata)
        if len(str(newdata['lotnr'])) != 14:
            #Currently, LOT must contain 6 digits from the date, 4 from article number, and 4 that are generated as the ID.
            flash('There was an error assigning your LOT number')
            return redirect('/')
        if '' in newdata.values():
            flash('Please fill in all the requested variables.')
            return redirect('/addnew/')
        if not newdata['amountinstore'].isdigit():
            flash('Please enter an integer as the amount in stock')
            return redirect('/addnew/')
        if not newdata['articlenr'] in names.keys():
            flash('Article number not recognized. Please try again.')
            return redirect('/addnew/')
        neworder = component_lot(newdata)
        try:
            app.session.add(neworder)
            app.session.commit()
            print('item added')
            flash('Your item was successfully added.')
            return redirect('/')
        except:
            print('There was a issue adding your order')
    else:
        return render_template('addnew.html',namestext=namestext)

@app.route('/delete/<lotnr>')
def delete(lotnr):
    todelete = app.session.query(component_lot).get(lotnr)
    try:
        app.session.delete(todelete)
        app.session.commit()
        flash('The item was successfully deleted.')
        return redirect('/')
    except:
        flash('There was an error deleting your item')
        return redirect('/')

@app.route('/takeone/<lotnr>')
def takefromstock(lotnr,amount=1):
    #Reduces amount in storage by calling reduceamount()
    reduceamount(lotnr,amount)
    return redirect('/')

@app.route('/addtodevice/<lotnr>',methods=["POST"])
def addtodevice(lotnr):
    #Moves LOT components from storage to the selected device
    try:
        if request.form['amounttoadd'] == '':
            amount = 1
        else:
            amount = int((request.form.get('amounttoadd',1)))
    except ValueError:
        flash('The input amount was not an integer.')
        return redirect('/')
    component = app.session.query(component_lot).get(lotnr)
    objecttype = names[component.articlenr]
    try:
        reduceamount(lotnr,amount)
        deviceadder(chosendevicenr,objecttype,lotnr,amount)
        flash('Successfully added item to device')
        return redirect('/')
    except:
        flash('There was an error adding to device')
        return redirect('/')

@app.route('/selectdevice/<devnr>')
def selectdevice(devnr):
    global chosendevicenr
    chosendevicenr = int(devnr)
    return redirect ('/')

@app.route('/devicemanager/createnew/')
def createnew():
    highestnumbers = app.session.query(device.devicenr).order_by(device.devicenr.desc()).first()
    if highestnumbers == None:
        latestnumber = 0
    else:
        latestnumber = int(highestnumbers[0])
    #Find list of used device nr in backup, to ensure no identical device numbers exist:
    checklist = [x[0] for x in app.session.query(backupdevice.devicenr).all()]
    newnumber = determinevalidnumber(latestnumber,checklist)
    contents = {}
    for name in names.values():
        contents[name] = {}
    newdev = device(contents,newnumber)
    app.session.add(newdev)
    app.session.commit()
    return redirect('/devicemanager/')

def determinevalidnumber(latestnumber,backupnumbers):
    #Ensures that no two devices have the same device number, in the case of old devices being stored in the backup table
    newnumber = latestnumber + 1
    if newnumber in backupnumbers:
        return determinevalidnumber(newnumber,backupnumbers)
    else:
        return newnumber

@app.route('/devicemanager/deletedevice/<devicenumber>')
def deletedevice(devicenumber):
    todelete =  app.session.query(device).get(devicenumber)
    backup = backupdevice(todelete)
    app.session.add(backup)
    Base.metadata.create_all()
    app.session.delete(todelete)
    app.session.commit()
    flash('Device successfully deleted. It can still be found in the backup table.')
    return redirect('/devicemanager/')

@app.route('/devicemanager/restoredevice/<devicenumber>')
def restoredevice(devicenumber):
    torestore = app.session.query(backupdevice).get(devicenumber)
    restoreddevice = device(torestore.contents,torestore.devicenr)
    app.session.add(restoreddevice)
    app.session.delete(torestore)
    app.session.commit()
    flash('Device was restored.')
    return redirect('/devicemanager/')

def lotgenerator(dataset):
    #Generates LOT from current date and articlenumber. 
    todaydate = str(date.today().strftime('%d%m%y'))
    artnr = dataset['articlenr']
    #Check for other LOT numbers with the same date and articlenumber, and increments the last 4 digits if it is found:
    similar = app.session.query(component_lot.lotnr).filter(component_lot.lotnr.like("%{}%".format(todaydate+artnr))).order_by(component_lot.lotnr.desc()).first()
    if similar is not None:
        lastfour = int(similar[0][-4:])
        lastfour += 1
        lastfour = str(lastfour).zfill(4)
    else:
        lastfour = '0001'
    newlot = todaydate+artnr+str(lastfour)
    return int(newlot)

def reduceamount(lotnr,amount=1):
    #Reduces the stored amount. If the amount becomes 0, the LOT is deleted.
    toreduce = app.session.query(component_lot).get(lotnr)
    try:
        amount = int(amount)
    except ValueError:
        flash('Failed removing from storage - the requested amount was not an integer.')
        return redirect('/')
    if toreduce.amountinstore < amount:
        flash('Error removing from stock - the requested amount was not available.')
        return redirect('/')
    try:
        toreduce.amountinstore -= int(amount)
        if toreduce.amountinstore == 0:
            flash('The selected LOT has been emptied and deleted')
            app.session.delete(toreduce)
        app.session.commit()
        flash('Successfully removed from stock')
    except:
        flash('There was an issue removing one from stock')
        return redirect('/')

def deviceadder(selecteddevicenr,objecttype,LOT,amount=1):
    try:
        #Data from device is read, and gets modified. Then, a new device is added with the combined old and new device data, and the old device gets deleted.
        storeddata = app.session.query(device).get(selecteddevicenr)
        data = storeddata.contents
        currentamount = data.get(objecttype,{}).get(LOT,0)
        data[objecttype][LOT] = currentamount + int(amount)
        newdevice = device(data,selecteddevicenr)
        app.session.delete(storeddata)
        app.session.add(newdevice)
        #This is inefficient. The old device object gets deleted and a new one is created every time it is edited.
        #SQLAlchemy can't track the changes made to a dict, so I need to work around this with a custom MutableDict class.
        #https://docs.sqlalchemy.org/en/14/orm/extensions/mutable.html
    except:
        print('Error in deviceadder')
        flash("Error adding to device")
        return redirect('/')
    app.session.flush()
    app.session.commit()
    return 'Ignore - flask requires a return value'

def emptyall(a,b):
    #Use to delete all devices with device numbers in range a,b
    for n in range(a,b):
        try:
            devicetodelete = app.session.query(device).get(n)
            app.session.delete(devicetodelete)
        except:
            print('Failed to delete ',n)
    app.session.commit()

def setup():
    component_lot.__table__.create(bind=engine)
    device.__table__.create(bind=engine)
    backupdevice.__table__.create(bind=engine)
    Base.metadata.create_all()
    app.session.commit()

#To reset the devices, run emptyall(0,100)

if __name__ == '__main__':
    #When running for the first time, setup is called.
    #setup()
    global chosendevicenr 
    chosendevicenr = 1
    app.run(host=os.getenv('IP', '0.0.0.0'),port=int(os.getenv('PORT', 4444)))
