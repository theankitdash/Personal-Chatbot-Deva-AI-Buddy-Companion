from db import setup_tables
from gradio_app import launch_app

if __name__ == "__main__":
    setup_tables()
    launch_app()