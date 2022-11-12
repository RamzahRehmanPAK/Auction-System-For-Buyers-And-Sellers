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
from auc_packet import auc_packet
from socket import timeout
from random import randint
from datetime import datetime
import numpy


#Got the basic skeleton of TCP client from https://www.geeksforgeeks.org/socket-programming-python/.
def handle_client(server_IP='',server_port='',udpRDT_port='',packet_loss_rate=0):

    # Create a socket object
    s = socket.socket()

    # connect to the server on local computer
    s.connect((server_IP, server_port))
    print("Connected to the Auctioneer server.\n")

    # receive data from the server and decoding to get the string.
    new_msg=s.recv(1024).decode()

    # Flags for won and sold
    soldFlag=0
    wonFlag=0
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
        print("Start sending file.")

        #UDP LOGIC some parts referred from https://github.com/islamnabil/UDPy
        if soldFlag==1:
            localPort=udpRDT_port
            UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            UDPServerSocket.bind((winnerIP, localPort))
            print("UDP socket open for RDT")

            bytesAddressPair = UDPServerSocket.recvfrom(1024)
            address = bytesAddressPair[1]

            transTime = datetime.now()
            #pkt = timeOutCheck(address, UDPServerSocket)
            #if not pkt:
            #    return 1

            # start the file transfer
            file = 'serverSent/test_1.pdf'
            if os.path.isfile(file):  # if file is found on the server           
                # get the file size
                size = os.path.getsize(file)

                #random loss
                nmLoss=numpy.random.binomial(n=1, p=packet_loss_rate)
                seq_num = 0
                ctlPkt = auc_packet(seq_num=seq_num, fileSize=size, typeOfPacket=0, ctl="start "+str(size))
                #toggling between 0 and 1 seq num
                seq_num = (seq_num + 1) % 2
                send_packet(ctlPkt, address, UDPServerSocket, nmLoss)

                dataRead = 0
                f = open(file=file, mode='rb')
                # read file in segments of 2000 bytes
                data = f.read(2000)
                while data:
                    dataRead += len(data)
                    # Build packet
                    pkt = auc_packet(data=data, seq_num=seq_num, batch=dataRead, fileSize=size)
                    #oldPkt = pkt
                    # send packet
                    #timeOutCheck(address, UDPServerSocket, oldPkt, pkt, nmLoss)
                    
                    send_packet(pkt, address, UDPServerSocket, nmLoss)

                    seq_num = (seq_num + 1) % 2
                    data = f.read(2000)

                #send fin ctl packet to signal end of transmission
                ctlPkt = auc_packet(seq_num=seq_num, fileSize=size, typeOfPacket=0, ctl="fin")
                send_packet(ctlPkt, address, UDPServerSocket, nmLoss)

                #Calculate time taken
                transTime = (datetime.now() - transTime).total_seconds()

                #log for plotting
                with open('log.txt', 'a') as log:
                    metrics = '\'\'^||^\'\'' + '\n'
                    metrics += 'THROUGHPUT=' + str(dataRead / transTime) + '\n'
                    log.write(metrics)

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

        if wonFlag==1:
            time.sleep(5)

            #make UDP socket
            UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            serverAddressPort = (sellerIP, udpRDT_port)
            msgFromClient = "Hello Seller"
            bytesToSend = str.encode(msgFromClient)
            UDPClientSocket.sendto(bytesToSend, serverAddressPort)

            received_file = 'clientReceived/' + 'test_1.pdf'
            open(file=received_file, mode='wb').close()
            f = open(file=received_file, mode='ab')
            recTime = datetime.now()

            dataWritten = 0
            while True:
                try:
                    res = UDPClientSocket.recvfrom(4000)[0]
                    pkt = auc_packet(pickled=res)
                    #stopping condition upon encountering fin
                    if pkt.__get__('ctl') == "fin":
                        #sending ack for fin
                        ack = auc_packet(seq_num=pkt.__get__('seq_num'), ack='+')
                        UDPClientSocket.sendto(ack.__serialize__(),serverAddressPort)
                        break

                    pkt.__print__()

                    #! Simulating packet corruption
                    #if randint(1, 100) > nmLoss:
                    #    f.write(pkt.__get__('data'))
                    #    # Send positive ack
                    #    ack = auc_packet(seq_num=pkt.__get__('seq_num'), ack='+')
                    #    UDPClientSocket.sendto(ack.__serialize__(),serverAddressPort)
                    #else:  # Send negative ack
                    #    print('Simulating packet corruption (Negative Ack): ' + pkt.__get__('seq_num'))
                    #    ack = auc_packet(seq_num=pkt.__get__('seq_num'), ack='-')
                    #    UDPClientSocket.sendto(ack.__serialize__(),serverAddressPort)
                    #! Sim complete

                    #writing data to file
                    f.write(pkt.__get__('data'))
                    dataWritten += len(pkt.__get__('data'))
                    print('Received data: ' + str(dataWritten)+ ' / ' + pkt.__get__('fileSize'))

                    # Sending ack
                    ack = auc_packet(seq_num=pkt.__get__('seq_num'), ack='+')
                    UDPClientSocket.sendto(ack.__serialize__(),serverAddressPort)
                except Exception as e:
                    print(e)
                    break

            f.close()
            UDPClientSocket.close()

            #writing the time taken and rate
            recTime = (datetime.now() - recTime).total_seconds()
            print('Transmission finished: ' + str(dataWritten) + ' bytes / ' +
                str(recTime) + ' secs = ' + str((dataWritten/recTime)) + ' bps')
            #TODO

    elif "Server is busy" in new_msg:
        print(new_msg)
    # elif role is Buyer
    # elif "Your role is: [Buyer]" in new_msg:

    # close the connection
    s.close()

# Logic to send packet
def send_packet(packet, client, UDPServerSocket, loss):
    seq_num = packet.__get__('seq_num')
    typeOfPacket = packet.__get__('typeOfPacket')
    fileSize = packet.__get__('fileSize')
    batch = packet.__get__('batch')
    ctl = packet.__get__('ctl')

    UDPServerSocket.sendto(packet.__serialize__(), client)
    if ctl == 'fin':
        UDPServerSocket.sendto(bytes(ctl, 'utf-8'), client)
        if typeOfPacket == '0':
            print('Sending control seq ' + seq_num + ': ' + ctl)
    else:
        if typeOfPacket == '0':
            print('Sending control seq ' + seq_num + ': start ' + fileSize)
        else:
            print('Sending data seq ' + seq_num + ': ' + batch + ' / ' + fileSize)

    res = UDPServerSocket.recvfrom(4000)[0]
    pkt = auc_packet(pickled=res)
    pkt.__print__()
    if pkt.__get__('ack') == '+':
        return 1
    else:
        print('Negative ack, resending : ' + seq_num)

    return 0

def timeOutCheck(address, UDPServerSocket, oldPacket, packet, nmLoss):
    clientTimeout = 2
    while clientTimeout:
        try:
            if not send_packet(packet, address, UDPServerSocket, nmLoss):
                break
            else:
                send_packet(oldPacket, address, UDPServerSocket, nmLoss)
                break
        except timeout:
            clientTimeout -= 1
    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(dest='server_IP', type=str)
    parser.add_argument(dest='server_port', type=int)
    parser.add_argument(dest='udpRDT_port', type=int)
    parser.add_argument(dest='packet_loss_rate', nargs='?', default=0, type=float)
    args = parser.parse_args()

    handle_client(args.server_IP,args.server_port,args.udpRDT_port,args.packet_loss_rate)