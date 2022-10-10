import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(dest='server_IP', type=str)
    parser.add_argument(dest='server_port', type=int)
    args = parser.parse_args()

    print(args.server_IP)
    print(args.server_port)

