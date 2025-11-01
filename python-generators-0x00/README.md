## 🎯 Project Overview

The project sets up a MySQL database `ALX_prodev` with a `user_data` table and implements generators that stream database rows efficiently without loading all data into memory at once.

## 📊 Database Schema

### Table: `user_data`
- `user_id` (VARCHAR(36), PRIMARY KEY, Indexed) - UUID format
- `name` (VARCHAR(255), NOT NULL)
- `email` (VARCHAR(255), NOT NULL) 
- `age` (DECIMAL(3,0), NOT NULL)

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.6+
- MySQL Server
- MySQL Connector/Python

### Install Dependencies
```bash
pip install mysql-connector-python faker
