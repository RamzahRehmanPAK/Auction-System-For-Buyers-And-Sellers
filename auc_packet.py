#Hafiza Ramzah Rehman
#Jainam Mitul Parikh
#Date Oct 22, 2022

import pickle
from hashlib import sha1

#Got the basic skeleton of packet structure from https://github.com/islamnabil/UDPy
class auc_packet:
    def __init__(self, pickled=None, seq_num=0, data=b'',
                 ack='', file='', status='', typeOfPacket=1, fileSize='', batch='', ctl=''):
        if pickled is not None:
            self.packet = pickle.loads(pickled)
        else:
            self.packet = {
                "status": status,
                "file": file,
                "ack": ack,
                "seq_num": seq_num,
                "checksum": sha1(data).hexdigest() if data else '',
                "data": data,
                "typeOfPacket": typeOfPacket,
                "fileSize": fileSize,
                "batch": batch,
                "ctl": ctl
            }

    #this function serializes packet data and returns it as bytes
    def __serialize__(self):
        return pickle.dumps(self.packet)

    # this function gets and returns requested fields
    def __get__(self, field):
        if field == 'seq_num' or field == 'fileSize' or field == 'batch' or field == 'typeOfPacket':
            return str(self.packet[field])
        else:
            return self.packet[field]

    # for printing details
    def __print__(self):
        status = self.__get__('status')
        file = self.__get__('file')
        ack = self.__get__('ack')
        seq_num = self.__get__('seq_num')
        typeOfPacket = self.__get__('typeOfPacket')
        fileSize = self.__get__('fileSize')
        batch = self.__get__('batch')
        ctl = self.__get__('ctl')
       
        if ack == '+':
            print('Ack received: ' + seq_num)
            #print(colored('Ack received: ' + seq_num, color='green'))
        elif ack == '-':
            print('Negative Ack ' + seq_num)
            #print(colored('Negative Ack ' + seq_num, color='red'))
        else:
            if ctl == 'fin' and typeOfPacket == '0':
                print('All data received! Exiting...')
            else:
                print('Msg received ' + seq_num)
                print('Ack Sent: ' + seq_num)
                #print(colored('Received Packet ' + seq_num, color='yellow'))
    
    def __check__(self):
        return self.packet['checksum'] == sha1(self.packet['data']).hexdigest()