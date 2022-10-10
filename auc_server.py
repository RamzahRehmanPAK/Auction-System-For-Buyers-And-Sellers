import argparse
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sp = parser.add_argument(dest='server_port',type=int)
    args = parser.parse_args()


    print(args.server_port)
    status = 0
    print ("Auctioneer is ready for hosting auctions.")