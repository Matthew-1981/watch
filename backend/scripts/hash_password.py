import argparse

from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('password', type=str)
    args = parser.parse_args()

    print(hash_password(args.password))


if __name__ == '__main__':
    main()
