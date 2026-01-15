from app import app as application
from multiprocessing import set_start_method

if __name__ == "__main__":
    set_start_method('spawn')
    application.run()
