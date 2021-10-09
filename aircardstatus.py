import socket
import time
import os
import datetime
import json
import logging
import dotenv
from pathlib import Path
from atcommands import *


class modem_data:
    def __init__(self):
        self.status = {}
        self.connection_data = {}

class modemSession:

    socket.setdefaulttimeout(5)
    session = None

    def __init__(self):
        self.host = os.environ['HOST']
        self.port = int(os.environ['PORT'])
        
    def connect(self, sock=None, retries=3, ):

        attempts = 0

        if sock == None:
            self.session = socket.socket()
        else:
            self.session = sock
        
        logging.info('Trying to connect to modem...')

        while attempts < retries:
            try:
                self.session.connect((self.host, self.port))
                attempts+=1
            except socket.timeout as e:
                if attempts == retries:
                    return e
                else:
                    logging.info('Connection attempt timed out. Retrying...')
                    self.close()
                    self.session = socket.socket()
                    continue
            except socket.error as e:
                    return e                  
            else:
                logging.info(f'Connected to modem @ {self.host}:{self.port}')
                break
            

    def sendCommand(self, command):
        
        response = ''

        try:
            self.session.sendall(f'{command}\r\n'.encode('ascii'))
            logging.info(f'Command "{command}" sent to modem')
            while True:
                try:
                    data = self.session.recv(2048)
                except Exception as e:
                    return e
                else:
                    response += data.decode('ascii')

                    # End of message
                    if 'OK' in data.decode('ascii'):    
                        logging.info('Response received from modem')
                        logging.info(response)
                        return response
                        
        except Exception as e:
            return e
                    

    def close(self):
        try:
            self.session.shutdown(socket.SHUT_RDWR)
        except OSError as e:
            return
        else:
            self.session.close()
        
# Log connection data as JSON object 
def logData(data):

    log_data = data.copy()
    log_data.update({'Time': datetime.datetime.now().strftime("%X")})
    json_str = json.dumps(log_data)

    try:
        with open('connection.log', 'x') as log:
            log.write(json_str)
    except FileExistsError:
        with open('connection.log', 'a') as log:
            log.write(',')
            log.write(json_str)
    except Exception as e:
        logging.warning(e)
        logging.warning('Error logging to local database')
    finally:
        logging.info('Data logged to local database')

def signalBars(response):

    for index, char in enumerate(response):
        if char == ' ':
            start = index
        elif char == ',':
            end = index
    
    signal = int(response[start:end])

    if signal == 99:
        return 0
    elif signal == 0:
        return 1
    elif signal == 1:
        return 2
    elif signal >=2 and signal <=30:
        return 3
    elif signal == 31:
        return 4

# --- PARSE RAW DATA
def parse(response):

    # General processing
    data = []
    start = 0
    
    data_split = response.split('\r\n')

    for index, line in enumerate(data_split):
        if line == '':
            block = data_split[start:index]
            if block:
                data.append(data_split[start:index])
            start = index + 1
        if line == 'OK':                                   
                break

    for block in data:
        for index, line in enumerate(block):
            if '\t' in line:
                split_list = line.split('\t')
                block.pop(index)

                for item in split_list:
                    if item:
                        block.insert(index, item)
                        index += 1

            if '\r' in line:
                block[index] = block[index].strip('\r')


    if STATUS in data[0][0]:
        return parse_status(data)
    
    if BANDMASK in data[0][0]:
        return decode_bandmask(data[0][1])

    if MAKE in data[0][0]:
        return data[0][1]
    
    if MODEL in data[0][0]:
         return data[0][1]
    else:
        return data

# Parse status
def parse_status(data_split):

    output = modem_data()

    # Process data list into dict in blocks
    for block in data_split:

        block_dict = {}
        signal_quality = {}

        for line in block:
            
            if ':' in line:
                split_dict = line.split(':')

                # Add to current block dict
                if len(split_dict) > 1:
                    key = split_dict[0].strip()
                    value = split_dict[1].strip()
                    block_dict[key] = value 

                    # Determine quality scale for signal levels
                    if 'dB' in key:
                        quality = quality_scale({key: value})
                        if quality:
                            signal_quality.update({key: quality})
                            

        # Block is modem info    
        if data_split.index(block) == 0:                                                               
            block_dict.pop(list(block_dict)[0])                             
            output.status['Mode'] = block_dict['Mode']
            output.status['Uptime'] = uptime_format(block_dict['Current Time'])
            
        else:
            key = list(block_dict)[0]                                       
            signal_quality.update({ 'Band': block_dict['LTE band'] })
            output.connection_data[key] = signal_quality
        
    return output


# --- SIGNAL QUALITY
def quality_scale(num):

    measures = {
        'RSSI': {'Excellent': -70, 'Good': -85, 'Fair': -100},
        'RSRP': {'Excellent': -90, 'Good': -105, 'Fair': -120}, 
        'RSRQ': {'Excellent': -9, 'Good': -12}, 
        'RSSNR': {'Excellent': 10, 'Good': 6, 'Fair': 0}
        }
  
    quality = 'Poor'
    
    for measure, signal_level in num.items():

        if signal_level == '':
            return None

        signal_level = float(signal_level)
        
        # Strip out excess
        for index, char in enumerate(measure):
            if char == ' ':
                measure = measure[:index]
                break

    
    for item in measures.items():
        if measure == item[0]:
            for key, value in item[1].items(): 
                if signal_level >= value:
                    quality = key
                    return quality
        
    return quality


# --- FORMAT UPTIME
def uptime_format(i):
    
    seconds = int(i)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)

    hr = 'hours'
    min = 'minutes'

    if h == 1:
        hr = 'hour'
    
    if m == 1:
        min = 'minute'

    uptime = '{hours} {hr} {minutes} {min}'.format(
        
                hours=h if h > 0 else '', 
                hr=hr if h > 0 else '', 
                minutes=m, 
                min=min)
    
    return uptime
    
# -- SET BANDMASK 
def encode_bandmask(bandmask):

    high = [0] * 64
    low = [0] * 64

    for band in bandmask:
        band_int = int(band)
        if band_int > 44:
            high[64 - band_int] = 1
        else:
            low[64 - band_int] = 1
    
    high_mask = bit2hex(high)
    low_mask = bit2hex(low)

    return f'at!gband={high_mask},{low_mask}\r\n'

# -- Convert bit mask to hex mask
def bit2hex(bit_mask):

    byte = []
    hex_mask = ''

    if sum(bit_mask) == 0:
        return '0' * 16

    for bit in bit_mask:
            byte.append(str(bit))
            if len(byte) == 4:

                # Convert byte list to string
                byte_string = ''.join(byte)

                # Convert byte string to hex
                num = format(int(byte_string), 'x')[-1:]

                # Append to mask
                hex_mask = f'{hex_mask}{num}'
                byte = []

    return hex_mask
    

# -- DECODE BANDMASK 
def decode_bandmask(mask):

    bandmask = {    1: False, 
                    3: False, 
                    7: False, 
                    28: False, 
                    40: False  }

    bin_masks = []

    mask = mask.split(',')
    mask.pop(0)
    
    for elem in mask:
        bin_mask = ''
        for digit in reversed(elem.strip()):
            byte = format(int(digit), 'b').zfill(4)
            bin_mask = f'{byte}{bin_mask}'

        bin_masks.append(bin_mask)
    
    for mask in bin_masks:
        for index, digit in enumerate(reversed(mask)):
            if digit == '1' and index+1 in bandmask.keys():
                bandmask[index+1] = True
    
    return bandmask


def pingLoop():
    s = socket.socket()
    timeout = 30
    host = os.environ['HOST']
    port = int(os.environ['PORT'])
    while True:
        try:
            s.connect((host,port))
        except Exception as e:
            print(e)
            timeout-=1

            if timeout == 0:
                return "timed out"
            else:
                time.sleep(3)
                continue
        else:
            s.close()
            return True 

    



    
