from asyncio.windows_events import NULL
import slack
import os
import shutil
import time
import threading
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter

#load the environment variables that have tokens and signing secrets
Environment_path = Path('.')/'.ENV'
load_dotenv(dotenv_path = Environment_path)

#initialize the webserver
app = Flask(__name__)

slack_event_handler = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)
#Intialize the client with OAUTH_TOKEN
Slack_Client = slack.WebClient(token = os.environ['OAUTH_TOKEN'])
BOT_ID = Slack_Client.api_call("auth.test")["user_id"]
current_path                = os.getcwd()

DOWNLOAD_PATH               = "C:/Users/sm185553/Downloads/"
SIMPUMPS_ADDITIONAL_PATH    = "simpumps/master/4.1.48/"

VAGRANT_MSI                 = "vagrant_2.2.5_x86_64.msi"
SIMPUMPS_MSI                = "SimPumps_4.1.48.msi"

VAGRANT = "vagrant"
SIMPUMPS = "simpumps"

SIMPUMPS_DOWNLOAD_COMMAND  = "jfrog rt dl cfr-generic-group/simpumps/master/4.1.48/SimPumps_4.1.48.msi " 
VAGRANT_DOWNLOAD_COMMAND   = "start https://releases.hashicorp.com/vagrant/2.2.5/vagrant_2.2.5_x86_64.msi"


def download__(command,channel_id,software):
    print("command received to run on thread is " + command)
    os.system(command)
    Slack_Client.chat_postMessage(channel=channel_id,text = "* Downloading "+ software + " Completed*")

def install_app(path,name,channel_id,software):
    print("Install app with path = " + path  + " and name = " + name)
    os.chdir(path)
    os.system("msiexec /i "+ name)
    Slack_Client.chat_postMessage(channel=channel_id,text = "*"+software + " Installation Completed*")

def file_exists(application):
    if(SIMPUMPS == application):
        return (os.path.isfile( DOWNLOAD_PATH + SIMPUMPS_ADDITIONAL_PATH + SIMPUMPS_MSI) == True)
    elif(VAGRANT == application):
        return (os.path.isfile(DOWNLOAD_PATH + VAGRANT_MSI) == True)
    return False


@slack_event_handler.on('message')
def message(payload):
    event = payload.get('event',{})
    user_id = event.get('user')
    channel_id = event.get('channel')
    text = event.get('text')
    if BOT_ID != user_id:
        Slack_Client.chat_postMessage(channel = channel_id,text = text)


@app.route('/download', methods = ['POST'])
def download():
    data = request.form
    software = ""
    channel_id = data.get('channel_id')

    if(data.get('text') == ''):
        Slack_Client.chat_postMessage(channel=channel_id,text = "please specify the Software")
        return Response(), 200
    
    software = data.get('text')
    Slack_Client.chat_postMessage(channel=channel_id,text = "Downloading "+software + ", please wait...")

    command = ""   
    if(SIMPUMPS == software):
        command = SIMPUMPS_DOWNLOAD_COMMAND + DOWNLOAD_PATH

    elif(VAGRANT == software):
        command = VAGRANT_DOWNLOAD_COMMAND
            
    t1 = threading.Thread(target=download__,args=(command,channel_id,software,))
    t1.start()
    return Response(), 200


@app.route('/install', methods = ['POST'])
def installation_references():
    data = request.form
    print(data)
    channel_id = data.get('channel_id')
    Slack_Client.chat_postMessage(channel=channel_id,text = "Installing, Please wait...")
    
    if(data.get('text') == ''):
        Slack_Client.chat_postMessage(channel=channel_id,text = "Please specify the software")   
        return Response(), 200
    
    software = data.get('text')
    commnad = ""
    
    if(file_exists(software) == False):
        Slack_Client.chat_postMessage(channel=channel_id,text = "Please use download command before installation")
        return Response(), 200

    msi_path = ""
    msi_name = ""
    print("everything is fine")
    if( SIMPUMPS == software):
        msi_path = DOWNLOAD_PATH+SIMPUMPS_ADDITIONAL_PATH
        msi_name = SIMPUMPS_MSI
    elif(VAGRANT == software):
        msi_path = DOWNLOAD_PATH
        msi_name = VAGRANT_MSI


    t1 = threading.Thread(target=install_app,args=(msi_path,msi_name,channel_id,software,))
    t1.start()
    return Response(), 200
   

@app.route('/help', methods = ['POST'])
def help():
    data = request.form
    channel_id = data.get('channel_id')
    Slack_Client.chat_postMessage(channel=channel_id,text = "*/new* - use it if you are new to fuel team.\n*/download <application name>* - use it to download a specific software from artifactory\n*/install <application name>* - use it to install a specific software in local machine")
    return Response(), 200

@app.route('/new', methods = ['POST'])
def new():
    data = request.form
    channel_id = data.get('channel_id')
    Slack_Client.chat_postMessage(channel=channel_id,text = "Hi, *Welcome to Fuel Team* \n please go through the page to start setting developer environment \n https://confluence.ncr.com/pages/viewpage.action?spaceKey=pcrfuel&title=Fuel+New+Hire+Checklist+-+Developer+Specific \n *List of softwares need to be installed : *\n1. Vagrant\n2. Simpumps\nTo downlaod an application please use */download <application name>* \nTo Install an application, please use */Install <application name>*")
    return Response(), 200


if __name__ == '__main__':
    app.run(debug=True)