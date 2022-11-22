# Hafiza Ramzah Rehman
# Jainam Mitul Parikh
# Date Nov 12, 2022

# imported the socket library
import copy
import socket
import argparse
# Import threading module
import threading
from threading import *
import subprocess
from time import sleep

# type is zero for seller and one for client. These variables track what kind of thread we have, seller, or buyer
SELLER = 0
BUYER = 1


##got from https://stackoverflow.com/questions/20691258/is-it-possible-in-python-to-kill-process-that-is-listening-on-specific-port-for to kill a process using the port the server needs to use
def kill_process_using_port(port):
    pid = subprocess.run(
        ['lsof', '-t', f'-i:{port}'], text=True, capture_output=True
    ).stdout.strip()
    if pid:
        if subprocess.run(['kill', '-TERM', pid]).returncode != 0:
            subprocess.run(['kill', '-KILL', pid], check=True)
        sleep(1)  # Give OS time to free up the PORT usage

class AutionServer:

    def __init__(self, server_port):
        # the server is waiting for seller
        print("Auctioneer is ready for hosting auctions!\n")
        #kill_process_using_port(server_port)
        self.status = 0
        self.buyerThreads = []
        # key value pair, key is buyer thread and value is the bid amount
        self.buyerBids = dict()
        self.seller_thread = None
        self.server_port = server_port
        self.total_bids = -1
        self.auc_type = 0
        self.min_price = -1
        self.item_name = ""
        self.biddingThread = None
        self.all_bids_received_event = Event()
        self.auction_finished_event = Event()
        self.winner_number = -1
        self.actual_payment = -1
        #! Added two variables here:
        self.seller_ip = ""
        self.winner_ip = ""

    def reinitialize(self,server_port):
        # the server is waiting for seller
        print("Auctioneer is ready for hosting auctions!\n")
        self.status = 0
        self.buyerThreads = []
        # key value pair, key is buyer thread and value is the bid amount
        self.buyerBids = dict()
        self.seller_thread = None
        self.server_port = server_port
        self.total_bids = -1
        self.auc_type = 0
        self.min_price = -1
        self.item_name = ""
        self.biddingThread = None
        self.all_bids_received_event = Event()
        self.auction_finished_event = Event()
        self.winner_number = -1
        self.actual_payment = -1
        #! Added two variables here:
        self.seller_ip = ""
        self.winner_ip = ""

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

            # case (1)
            # If the status is zero and there is no seller thread, then accept this client and make this a seller.
            if self.status == 0 and self.seller_thread == None:
                self.reinitialize(self.server_port)
                print("Seller is connected from " + str(client_ip) + ":" + str(client_port))
                #! Assigning client_ip to seller_ip
                self.seller_ip = client_ip
                print(">> New Seller Thread spawned")
                self.seller_thread = self.ClientThread(client_ip, client_port, clientsock, SELLER, self)
                self.seller_thread.start()
            # case (2)
            # if seller exists but auction request not received
            elif self.status == 0:
                # send a Server busy! message to the buyer. encoding to send byte type.
                clientsock.send('Server is busy. Try to connect again later.'.encode())
                # Close the connection with the buyer
                clientsock.close()
            # if seller exists and the auction request is received
            else:
                # case 3 and 4
                if len(self.buyerThreads) + 1 <= self.total_bids:
                    buyer_thread = self.ClientThread(client_ip, client_port, clientsock, BUYER, self,
                                                     len(self.buyerThreads) + 1)
                    self.buyerThreads.append(buyer_thread)
                    print("Buyer " + str(len(self.buyerThreads)) + " is connected from " + str(client_ip) + ":" + str(
                        client_port))

                    if len(self.buyerThreads) < self.total_bids:
                        # informs the client that the server is currently waiting for other Buyers
                        clientsock.send(
                            'Your role is: [Buyer]\nThe Auctioneer is still waiting for other Buyers to connect...\n'.encode())
                    else:
                        clientsock.send('Your role is: [Buyer]\n'.encode())
                        print("Requested number of bids arrived. Let's start bidding!")
                        self.biddingThread = self.BiddingThread(self)
                        self.biddingThread.start()
                # case 5
                else:
                    # send a Bidding on-going! message to the buyer. encoding to send byte type.
                    clientsock.send('Server is busy. Try to connect again later.'.encode())
                    # Close the connection with the buyer
                    clientsock.close()

    # Got the basic structure of bidding threads from this accepted answer at stackoverflow https://stackoverflow.com/questions/17453212/multi-threaded-tcp-server-in-python
    class BiddingThread(threading.Thread):
        def __init__(self, auction_server):
            threading.Thread.__init__(self)
            self.auction_server = auction_server
        def run(self):

            print("New Bidding Thread spawned")
            # inform all buyers that bidding has started
            for buyer_thread in self.auction_server.buyerThreads:
                buyer_thread.socket.send('The Bidding has Started!\nPlease submit your bid:\n'.encode())

            # set the event so it's only cleared when all bids arrive.
            # used https://dotnettutorials.net/lesson/inter-thread-communication-in-python/ for reference to undertsand how to do inter-thread communication in python

            # start the threads for buyer
            for buyer_thread in self.auction_server.buyerThreads:
                buyer_thread.start()

            # wait for all bids to come
            self.auction_server.all_bids_received_event.wait()

            # all bids have arrived
            winner, highest_bid = sorted(self.auction_server.buyerBids.items(),key=lambda x: x[1], reverse=True)[0]
            if self.auction_server.auc_type == 1:
                # get highest bid
                actual_payment = highest_bid
            elif self.auction_server.auc_type == 2:
                all_bids = self.auction_server.buyerBids.copy()
                # include sellers price in
                all_bids[self.auction_server.seller_thread] = self.auction_server.min_price
                # Get the second highest bid
                _, actual_payment =sorted(all_bids.items(),key=lambda x: x[1], reverse=True)[1]

            if actual_payment >= self.auction_server.min_price:
                self.auction_server.winner_number = winner.client_number
                #! Assigning client_ip to winner_ip
                self.auction_server.winner_ip = winner.ip
                self.auction_server.actual_payment = actual_payment
                print("Item sold! The highest bid is $" + str(highest_bid) + ". The actual payment is $" + str(
                    self.auction_server.actual_payment)+"\n")
            else:
                print("The item is not sold. The auction is finished.")
            # indicate buyers and sellers threads that the auction has finished
            self.auction_server.auction_finished_event.set()

            #wait for buyer and seller threads to terminate
            for buyer_thread in self.auction_server.buyerThreads:
                buyer_thread.join()
            #all threads have terminated, now change the status of aution_server to zero again.
            self.auction_server.status=0
            self.auction_server.seller_thread=None

    # Got the basic structure of client threads from this accepted answer at stackoverflow https://stackoverflow.com/questions/17453212/multi-threaded-tcp-server-in-python
    class ClientThread(threading.Thread):

        def __init__(self, ip, port, socket, type, aution_server, client_number=0):
            threading.Thread.__init__(self)
            # set client IP, port and client socket
            self.ip = ip
            self.port = port
            self.socket = socket
            self.auction_server = aution_server
            # type is zero for seller and one for client.
            self.type = type
            self.client_number = client_number

        def run(self):
            # if client is a seller
            if self.type == SELLER:
                self.socket.send('Your role is: [Seller]\nPlease submit auction request:\n'.encode())
                is_auc_request_correct = False
                # Keep getting auction requests until auction requests are not correct
                while not is_auc_request_correct:
                    # receive the auction request from the seller
                    auc_request = (self.socket.recv(1024).decode())
                    auc_type, min_price, number_bids, item_name = auc_request.split(" ")
                    # check if the auction request is correct
                    # print(auc_type, min_price, number_bids, item_name)

                    if (auc_type == '1' or auc_type == '2') and (str.isdigit(min_price) and int(min_price) > 0) and (
                            str.isdigit(number_bids) and 0 < int(number_bids) < 10) and len(item_name) <= 255:
                        # Inform seller that action request is statred now since auction request was correct.
                        self.socket.send('Server: Auction Start\n'.encode())
                        is_auc_request_correct = True

                        auc_type, min_price, number_bids = int(auc_type), int(min_price), int(number_bids)
                        self.auction_server.total_bids = number_bids
                        self.auction_server.auc_type = auc_type
                        self.auction_server.min_price = min_price
                        self.auction_server.item_name = item_name

                    # Request seller for auction request again if auction request is not correct
                    else:
                        self.socket.send('Server: Invalid Auction Request!\nPlease submit auction request:\n'.encode())

                print("Auction request received. Now waiting for Buyer.")

                # switch the status to 1 to wait for buyers
                self.auction_server.status = 1
                # wait for all bids to arrive
                self.auction_server.all_bids_received_event.wait()
                # wait for aution to finish
                self.auction_server.auction_finished_event.wait()
                # auction finished
                if self.auction_server.winner_number != -1:
                    #message = 'Auction Finished!\nSuccess! Your item ' + str(
                    #    self.auction_server.item_name) + ' has been sold for $' + str(
                    #    self.auction_server.actual_payment) + "\n"
                    #! added self.auction_server.winner_ip here
                    message = 'Auction Finished!\nSuccess! Your item ' + str(
                        self.auction_server.item_name) + ' has been sold for $' + str(
                        self.auction_server.actual_payment) + '. Buyer IP: ' + str(self.auction_server.winner_ip) + "\n"
                else:
                    message = 'Auction Finished!\nFailure! Unfortunately, your item was not sold in the auction.\n'
                self.socket.send(message.encode())
                self.socket.close()

            # if client is a buyer
            elif self.type == BUYER:
                # case (4) all buyers have connected
                # handeling case 4
                # receive bid
                isBidCorrect = False
                while not isBidCorrect:
                    bid = (self.socket.recv(1024).decode())
                    if (str.isdigit(bid) and int(bid) > 0):
                        self.socket.send('Server: Bid received. Please wait...\n'.encode())
                        print("Buyer " + str(self.client_number) + " bid $" + str(bid))
                        self.auction_server.buyerBids[self] = int(bid)
                        isBidCorrect = True
                    else:
                        self.socket.send(
                            'Server: Invalid bid. Please submit a positive integer!\nPlease submit your bid:\n'.encode())
                # correct bid has been received for this buyer

                # wait for all bids to arrive.
                if not self.auction_server.all_bids_received_event.is_set():
                    if (len(self.auction_server.buyerBids) == len(self.auction_server.buyerThreads)):
                        self.auction_server.all_bids_received_event.set()
                self.auction_server.all_bids_received_event.wait()

                # all bids have arrived now wait for auction to finish
                self.auction_server.auction_finished_event.wait()
                # auction has finished

                if self.auction_server.winner_number == self.client_number:
                    #message = 'Auction Finished!\nYou won this item ' \
                    #          + self.auction_server.item_name + '! Your payment due is $' \
                    #          + str(self.auction_server.actual_payment) + "\n"
                    #! add self.auction_server.seller_ip here
                    message = 'Auction Finished!\nYou won this item ' \
                              + self.auction_server.item_name + '! Your payment due is $' \
                              + str(self.auction_server.actual_payment) + '. Seller IP: ' + str(self.auction_server.seller_ip) +"\n"
                else:
                    message = 'Auction Finished!\nUnfortunately you did not win in the last round.\n'
                self.socket.send(message.encode())
                self.socket.close()
                # Close the connection with the client
                self.socket.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sp = parser.add_argument(dest='server_port', type=int)
    args = parser.parse_args()

    auction_server = AutionServer(args.server_port)
    auction_server.handle_auction()
