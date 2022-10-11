#Hafiza Ramzah Rehman
#Jainam Parikh

#imported the socket library
import socket
import argparse
# Import threading module
import threading
import subprocess
from time import sleep

#type is zero for seller and one for client. These variables track what kind of thread we have, seller, or buyer
SELLER=0
BUYER=1

#got from https://stackoverflow.com/questions/20691258/is-it-possible-in-python-to-kill-process-that-is-listening-on-specific-port-for to kill a process using the port the server needs to use
def kill_process_using_port(port):
    pid = subprocess.run(
        ['lsof', '-t', f'-i:{port}'], text=True, capture_output=True
    ).stdout.strip()
    if pid:
        if subprocess.run(['kill', '-TERM', pid]).returncode != 0:
            subprocess.run(['kill', '-KILL', pid], check=True)
        sleep(1)  # Give OS time to free up the PORT usage

class AutionServer:

    def __init__(self,server_port):
        #the server is waiting for seller
        print("Auctioneer is ready for hosting auctions!\n")
        kill_process_using_port(server_port)
        self.status=0
        self.buyerThreads=[]
        self.seller_thread=None
        self.server_port=server_port
        self.total_bids=-1
        self.auc_type=0
        self.min_price=-1
        self.item_name=""

    # Got the basic skeleton of TCP server from https://www.geeksforgeeks.org/socket-programming-python/.
    def handle_auction(self):

        # next create a socket object
        s = socket.socket()

        # Next bind to the port
        # we have not typed any ip in the ip field
        # instead we have inputted an empty string
        # this makes the server listen to requests
        # coming from other computers on the network
        s.bind(('', self.server_port))

        # put the socket into listening mode.
        s.listen(5)

        # a forever loop until we interrupt it or
        # an error occurs
        while True:
            # Establish connection with client. #(ip, port) is the tuple of IP and port of the client
            (clientsock, (client_ip, client_port)) = s.accept()

            # we can have diffirent cases:
            # (1) seller doesn't exist
            # (2) seller exists but auction request not received yet
            # (3) auction request exists and still waiting for all buyers to connect
            # (4) all buyers have connected
            # (5) new client trying to take part in bidding while bidding is going on

            #case (1)
            #If the status is zero and there is no seller thread, then accept this client and make this a seller.
            if self.status==0 and self.seller_thread==None:
                print("Seller is connected from "+str(client_ip)+":"+str(client_port))
                print(">> New Seller Thread spawned")
                self.seller_thread = self.ClientThread(client_ip, client_port, clientsock,SELLER,self)
                self.seller_thread.start()
            #case (2)
            #if seller exists but auction request not received
            elif self.status==0:
                # send a Server busy! message to the buyer. encoding to send byte type.
                clientsock.send('Server is busy. Try to connect again later.'.encode())
                # Close the connection with the buyer
                clientsock.socket.close()
            #if seller exists and the auction request is received
            else:
                #case 3 and 4
                if len(self.buyerThreads) + 1 <= self.total_bids:
                    buyer_thread = self.ClientThread(client_ip, client_port, clientsock, BUYER, self)
                    self.buyerThreads.append(buyer_thread)
                    print("Buyer "+str(len(self.buyerThreads))+"is connected from "+str(client_ip)+":"+str(client_port))

                    if len(self.buyerThreads) + 1 < self.total_bids:
                        # informs the client that the server is currently waiting for other Buyers
                        clientsock.send('Your role is: [Buyer]\nThe Auctioneer is still waiting for other Buyers to connect...\n'.encode())
                    else:
                        clientsock.send('Your role is: [Buyer]')
                        print("Requested number of bids arrived. Let's start bidding!")
                        print("New Bidding Thread spawned")
                        #self.socket.send('The Bidding has Started!\nPlease submit your bid:\n'.encode())
                        # buyer_thread.start()
                #case 5
                else:
                    # send a Bidding on-going! message to the buyer. encoding to send byte type.
                    clientsock.send('Bidding on-going! Server is busy. Try to connect again later.'.encode())
                    # Close the connection with the buyer
                    clientsock.socket.close()

    # Got the basic structure of client threads from this accepted answer at stackoverflow https://stackoverflow.com/questions/17453212/multi-threaded-tcp-server-in-python
    class ClientThread(threading.Thread):

        def __init__(self, ip, port, socket,type,aution_server):
            threading.Thread.__init__(self)
            # set client IP, port and client socket
            self.ip = ip
            self.port = port
            self.socket = socket
            self.auction_server=aution_server
            #type is zero for seller and one for client.
            self.type=type

        def run(self):
            #if client is a seller
            if self.type==SELLER:
                self.socket.send('Your role is: [Seller]\nPlease submit auction request:\n'.encode())
                is_auc_request_correct=False
                # Keep getting auction requests until auction requests are not correct
                while not is_auc_request_correct:
                    #receive the auction request from the seller
                    auc_request = (self.socket.recv(1024).decode())
                    auc_type, min_price, number_bids, item_name=auc_request.split(" ")
                    #check if the auction request is correct
                    #print(auc_type, min_price, number_bids, item_name)

                    if (auc_type=='1' or auc_type=='2') and (str.isdigit(min_price) and int(min_price)>0) and (str.isdigit(number_bids) and 0<int(number_bids)<10) and len(item_name)<=255:
                        #Inform seller that action request is statred now since auction request was correct.
                        self.socket.send('Server: Auction Start\n'.encode())
                        is_auc_request_correct=True

                        auc_type,min_price,number_bids=int(auc_type),int(min_price),int(number_bids)
                        self.auction_server.total_bids=number_bids
                        self.auction_server.auc_type=auc_type
                        self.auction_server.min_price=min_price
                        self.auction_server.item_name=item_name

                    # Request seller for auction request again if auction request is not correct
                    else:
                        self.socket.send('Server: Invalid Auction Request!\nPlease submit auction request:\n'.encode())

                print("Auction request received. Now waiting for Buyer.")

                #switch the status to 1 to wait for buyers
                self.auction_server.status = 1
                while True:
                    pass
                self.socket.close()

            #if client is a buyer
            elif self.type==BUYER:

                # case (3) auction request exists and still waiting for all buyers to connect
                #  case (4) all buyers have connected

                #handeling case 3
                if len(self.buyerThreads) + 1 < self.total_bids:
                    pass
                elif len(self.buyerThreads) + 1 == self.total_bids:
                    pass


                #print('Got connection from', (self.ip, self.port))
                # Close the connection with the client
                #self.socket.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sp = parser.add_argument(dest='server_port',type=int)
    args = parser.parse_args()

    aution_server=AutionServer(args.server_port)
    aution_server.handle_auction()