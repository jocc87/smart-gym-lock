# Smart Gym Lock Analytics System

A self-service access and analytics system designed for a private gym, using smart lock integration (TTLock API).  
The goal is to support autonomous operation of the gym, where members enter using access codes and view visit patterns.

## Features

- Smart lock integration via TTLock API
- ETL pipeline in Python for log extraction and transformation
- PostgreSQL database with warehouse-style tables
- Visit statistics (daily distribution, frequency, active users)
- Web-based admin interface built with Flask
- Basic REST API endpoints for sync and stats

## Tech Stack

- Python (ETL, logic, API)
- Flask (web interface)
- Pandas, Matplotlib (analysis & visualization)
- PostgreSQL (storage)
- HTML, CSS, JavaScript (admin UI)

## Project Structure

├── app.py # Main Flask app
├── db_handler.py # DB access and logic
├── api_handler.py # TTLock API wrapper
├── etl_dw_loader.py # ETL logic to load logs into DW
├── dw_plot.py # Visualization code
├── templates/ # HTML pages
├── static/ # JS, CSS, generated charts
└── log_sync_job.py # Scheduled sync logic


## ⚠️ Notes

- `config.py` contains credentials and is excluded from the repository.
- This is a work-in-progress project, started as a university assignment and evolved into a real-world pilot.
- A short **demo video** will be added soon to showcase the workflow.

##  Demo

run_example.jpg can show the running in 2025.07.19. Downloaded a new data from the lock, 
process it to the DW and created a new statistic pictures to static folder.
