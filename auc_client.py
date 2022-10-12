#Hafiza Ramzah Rehman
#Jainam Parikh
#Date Oct 12, 2022

#import argparse
import argparse
# Import socket module
import socket

#Got the basic skeleton of TCP client from https://www.geeksforgeeks.org/socket-programming-python/.
def handle_client(server_IP,server_port):

    # Create a socket object
    s = socket.socket()

    # connect to the server on local computer
    s.connect((server_IP, server_port))
    print("Connected to the Auctioneer server.\n")

    # receive data from the server and decoding to get the string.
    new_msg=s.recv(1024).decode()

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
            print(new_msg)
        print("Disconnecting from the Auctioneer server. Auction is over!")

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
            print("Disconnecting from the Auctioneer server. Auction is over!")

    elif "Server is busy" in new_msg:
        print(new_msg)
    # elif role is Buyer
    # elif "Your role is: [Buyer]" in new_msg:

    # close the connection
    s.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(dest='server_IP', type=str)
    parser.add_argument(dest='server_port', type=int)
    args = parser.parse_args()

    handle_client(args.server_IP,args.server_port)

