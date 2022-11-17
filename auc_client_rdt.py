#Hafiza Ramzah Rehman
#Jainam Mitul Parikh
#Date Oct 22, 2022

#import argparse
import argparse
# Import socket module
import socket
import re
import time
import os
from datetime import datetime
import numpy
import pickle

#Got the basic skeleton of TCP client from https://www.geeksforgeeks.org/socket-programming-python/.
def handle_client(server_IP='',server_port='',udpRDT_port='',packet_loss_rate=0.0):

    # Create a socket object
    s = socket.socket()
    # connect to the server on local computer
    s.connect((server_IP, server_port))
    print("Connected to the Auctioneer server.\n")

    # receive data from the server and decoding to get the string.
    new_msg=s.recv(1024).decode()

    # Flags for won and sold and variables for seller-buyer IP
    soldFlag=0
    wonFlag=0
    lossFlag=0
    winnerIP=""
    sellerIP=""

    #if role is seller
    if "Your role is: [Seller]" in new_msg:
        print(new_msg)
        is_auc_request_correct = False
        # Keep sending auction requests until auction requests are not correct
        while not is_auc_request_correct:
            auction_request = (input())
            s.send(auction_request.encode())
            new_msg = s.recv(1024).decode()
            print(new_msg)
            # if auction request is fine
            if "Invalid Auction Request" in new_msg:
                continue
            elif "Auction Start" in new_msg:
                #auction has started
                is_auc_request_correct=True
        # wait for Auction Finished message from the server
        new_msg = s.recv(1024).decode()
        if "Auction Finished" in new_msg:
            # Change to print only message and not ip
            print(new_msg)
            #set sold flag to 1 and set winner IP
            if "Success" in new_msg:
                soldFlag=1
                winner = re.findall(r"IP:\s(.*)", new_msg, re.MULTILINE)
                winnerIP = winner[0]
        print("Disconnecting from the Auctioneer server. Auction is over!")

        #UDP LOGIC
        if soldFlag==1:
            localPort=udpRDT_port
            UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            UDPServerSocket.bind((winnerIP, localPort))
            print("UDP socket open for RDT")
            bytesAddressPair = UDPServerSocket.recvfrom(1024)
            address = bytesAddressPair[1]

            nmLoss = 0

            print("Start sending file.")
            # start the file transfer
            file = 'serverSent/test_1.txt'
            if os.path.isfile(file):  # if file is found on the server           
                # get the file size
                size = os.path.getsize(file)

                #random loss
                nmLoss=numpy.random.binomial(n=1, p=packet_loss_rate)
                #nmLoss = (nmLoss+1) % 2
                seq_num = 0
                reTrans=0
                while True:
                    #nmLoss = (nmLoss+1) % 2
                    ctlPkt = packetHeader(reTrans=reTrans, seq_num=seq_num, fileSize=size, typeOfPacket=0, ctl="start")
                    lossFlag = sendPacket(ctlPkt, address, UDPServerSocket, nmLoss)

                    if lossFlag == 1:
                        #print("\tfrom start")
                        print("Msg re-sent", ctlPkt.__get__('seq_num'))
                        reTrans += 1
                        continue
                    else:
                        break

                #toggling between 0 and 1 seq num
                seq_num = (seq_num + 1) % 2

                f = open(file=file, mode='rb')
                # read file in segments of 2000 bytes
                data = f.read(3)
                dataRead = len(data)
                reTrans=0
                while data:
                    #nmLoss = (nmLoss+1) % 2
                    # Build packet
                    pkt = packetHeader(reTrans=reTrans, data=data, seq_num=seq_num, chunk=dataRead, fileSize=size)
                    
                    lossFlag = sendPacket(pkt, address, UDPServerSocket, nmLoss)
                    #print(lossFlag)
                    if lossFlag == 1:
                        #print("\tfrom data")
                        print("Msg re-sent: ", seq_num)
                        reTrans += 1
                        continue

                    seq_num = (seq_num + 1) % 2
                    data = f.read(3)
                    dataRead += len(data)
                    reTrans=0

                #send fin ctl packet to signal end of transmission
                reTrans=0
                while True:
                    #nmLoss = (nmLoss+1) % 2
                    ctlPkt = packetHeader(reTrans=reTrans, seq_num=seq_num, fileSize=size, typeOfPacket=0, ctl="fin")
                    lossFlag = sendPacket(ctlPkt, address, UDPServerSocket, nmLoss)

                    if lossFlag == 1:
                        print("\tfrom fin")
                        print("Msg re-sent", ctlPkt.__get__('seq_num'))
                        reTrans += 1
                        continue
                    else:
                        break

    elif "Your role is: [Buyer]" in new_msg:
        print(new_msg)
        #wait for bidding has started message from the Auctioneer.
        new_msg = s.recv(1024).decode()
        if "Bidding has Started" in new_msg:
            print(new_msg)
            is_bid_correct=False
            while not is_bid_correct:
                bid = (input())
                s.send(bid.encode())
                new_msg = s.recv(1024).decode()
                print(new_msg)
                if "Invalid bid" in new_msg:
                    pass
                elif "Bid received" in new_msg:
                    is_bid_correct=True
            #correct bit has been received
            # wait for Auction Finished message from the server
            new_msg = s.recv(1024).decode()
            if "Auction Finished" in new_msg:
                print(new_msg)
                #set winner flag and get IP of seller
                if "won" in new_msg:
                    wonFlag=1
                    seller = re.findall(r"IP:\s(.*)", new_msg, re.MULTILINE)
                    sellerIP = seller[0]
            print("Disconnecting from the Auctioneer server. Auction is over!")

        # Checking the Win Flag and start connect to the UDP Socket
        if wonFlag==1:
            time.sleep(2)

            #make UDP socket
            UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            serverAddressPort = (sellerIP, udpRDT_port)
            msgFromClient = ""
            bytesToSend = str.encode(msgFromClient)
            UDPClientSocket.sendto(bytesToSend, serverAddressPort)

            print("UDP socket open for RDT")
            received_file = 'clientReceived/' + 'test_1.txt'
            open(file=received_file, mode='wb').close()
            f = open(file=received_file, mode='ab')
            tct = datetime.now()

            print("Start receiving file.")
            dataWritten = 0
            i=0
            res = bytes("", 'utf-8')
            nmLoss=0
            expSeqN=0

            while True:
                try:
                    nmLoss=numpy.random.binomial(n=1, p=packet_loss_rate)
                    #nmLoss = (nmLoss+1) % 2
                    
                    # AS recvfrom receives in tuple, we need just the message
                    res = UDPClientSocket.recvfrom(4000)[0]
                    # To serialize the data
                    pkt = packetHeader(pickled=res)
                    
                    if str(expSeqN) == pkt.__get__('seq_num'):
                        #print("nmLoss:", nmLoss)
                        if nmLoss != 1:
                            #stopping condition upon encountering fin
                            if pkt.__get__('typeOfPacket') == '0':
                                #sending ack for fin
                                ack = packetHeader(seq_num=pkt.__get__('seq_num'), ack='+')
                                UDPClientSocket.sendto(ack.__serialize__(),serverAddressPort)
                                print("\t\t\tExpected Seq:", expSeqN)
                                pkt.__print__()
                                if pkt.__get__('ctl') == "fin":
                                    f.close()
                                    UDPClientSocket.close()
                                    break
                                elif pkt.__get__('ctl') == "start":
                                    expSeqN = (expSeqN + 1) % 2
                                    continue
                            else:
                                print("\t\t\tExpected Seq:", expSeqN)
                                pkt.__print__()
                                #writing data to file
                                f.write(pkt.__get__('data'))
                                dataWritten += len(pkt.__get__('data'))
                                print('Received data seq ' + pkt.__get__('seq_num') + ": " + str(dataWritten) + ' / ' + pkt.__get__('fileSize'))
                                expSeqN = (expSeqN + 1) % 2

                                # Sending ack
                                ack = packetHeader(seq_num=pkt.__get__('seq_num'), ack='+')
                                UDPClientSocket.sendto(ack.__serialize__(),serverAddressPort)

                        else:
                            print("Pkt dropped", pkt.__get__('seq_num'))
                    else:
                        print("Msg received with mismatched sequence number", pkt.__get__('seq_num'),". Expecting", expSeqN)
                        print("Ack re-sent:", pkt.__get__('seq_num'))
                        #ack = packetHeader(seq_num=pkt.__get__('seq_num'), ack='+')
                        #  UDPClientSocket.sendto(ack.__serialize__(),serverAddressPort)

                except Exception as e:
                    print("Exception in Receiver:", e)
                    break

            tct = (datetime.now() - tct).total_seconds()
            with open('log.txt', 'a') as log:
                metrics = '\'\'^||^\'\'' + '\n'
                metrics += 'THROUGHPUT=' + str(dataWritten/tct) + '\n'
                log.write(metrics)

            #writing the time taken and rate
            print('Transmission finished: ' + str(dataWritten) + ' bytes / ' + str(tct) + ' secs = ' + str((dataWritten/tct)) + ' bps')
            #TODO

    elif "Server is busy" in new_msg:
        print(new_msg)

    # close the connection
    s.close()

# Logic to send packet
def sendPacket(packet, client, UDPServerSocket, loss):
    seq_num = packet.__get__('seq_num')
    typeOfPacket = packet.__get__('typeOfPacket')
    fileSize = packet.__get__('fileSize')
    chunk = packet.__get__('chunk')
    ctl = packet.__get__('ctl')
    reTrans = packet.__get__('reTrans')
    lossFlag = 0

    UDPServerSocket.sendto(packet.__serialize__(), client)

    if reTrans == '0':
        if typeOfPacket == '0':
            if ctl == 'fin':
                print('Sending control seq ' + seq_num + ': ' + ctl)        
            elif ctl == 'start':
                print('Sending control seq ' + seq_num + ': start ' + fileSize)
        else:
            print('Sending data seq ' + seq_num + ': ' + chunk + ' / ' + fileSize)

    try:
        UDPServerSocket.settimeout(2)
        res = UDPServerSocket.recvfrom(4000)[0]
        pkt = packetHeader(pickled=res)
        #print("\t\tfrom timeout part")
        #pkt.__print__()

        #!!!!!!!!!!!!!!!!
        #print("Loss:ss", loss)
        if loss == 0:
            #print("loss:", loss)
            pkt = packetHeader(pickled=res)
            pkt.__print__()
        else:
            print("Ack dropped", pkt.__get('seq_num'))
            lossFlag=1
    except:
        lossFlag=1
        #print("in except:", lossFlag)

    return lossFlag

# Packet header class with the packet header fields (Like seq num, ack, ctl messages and type of messages, and data)
# [Took some reference fro packet structure from https://github.com/islamnabil/UDPy]
class packetHeader:
    def __init__(self, pickled=None, seq_num=0, data=b'',
                 ack='', file='', typeOfPacket=1, fileSize='', chunk='', ctl='', reTrans=0):
        if pickled is not None:
            self.packet = pickle.loads(pickled)
        else:
            self.packet = {
                "file": file,
                "ack": ack,
                "seq_num": seq_num,
                "data": data,
                "typeOfPacket": typeOfPacket,
                "fileSize": fileSize,
                "chunk": chunk,
                "ctl": ctl,
                "reTrans": reTrans
            }

    #this function serializes packet data and returns it as bytes
    def __serialize__(self):
        return pickle.dumps(self.packet)

    # this function gets and returns requested fields
    def __get__(self, field):
        getData = self.packet[field]
        if field == 'seq_num' or field == 'fileSize' or field == 'chunk' or field == 'typeOfPacket'or field == 'reTrans':
            return str(getData)
        else:
            return getData

    # for printing details
    def __print__(self):
        ack = self.__get__('ack')
        seq_num = self.__get__('seq_num')
        typeOfPacket = self.__get__('typeOfPacket')
        ctl = self.__get__('ctl')
       
        if ack == '+':
            print('Ack received: ' + seq_num)
        elif ack == '-':
            print('Negative Ack ' + seq_num)
        else:
            print('Msg received ' + seq_num)
            print('Ack Sent: ' + seq_num)
            if ctl == 'fin' and typeOfPacket == '0':
                print('All data received! Exiting...')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(dest='server_IP', type=str)
    parser.add_argument(dest='server_port', type=int)
    parser.add_argument(dest='udpRDT_port', type=int)
    parser.add_argument(dest='packet_loss_rate', nargs='?', default=0, type=float)
    args = parser.parse_args()

    handle_client(args.server_IP,args.server_port,args.udpRDT_port,args.packet_loss_rate)