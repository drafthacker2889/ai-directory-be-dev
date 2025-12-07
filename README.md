# COM661: Full Stack Strategies - Coursework 1

## AI Device Directory API

This project is a comprehensive, secure, and modular RESTful API built with Flask and MongoDB, as required for the COM661 Coursework 1.

It provides full, role-based CRUD (Create, Read, Update, Delete) operations for AI devices, user-written reviews, and user accounts. It is built to 1st Class standards, featuring advanced database queries (aggregation, text search, geo-location) and a robust, multi-level authentication system using JWTs and Blueprints.

### Features

  * **Full CRUD:** Complete, 4-operation CRUD on all 3 resources: Devices, Reviews, and Users.
  * **Role-Based Authentication:** Secure JWT-based system with two distinct roles:
      * `Admin`: Full control over all devices and can delete any user/review.
      * `User`: Can manage their own profile and reviews, but cannot modify other users' data.
  * **Advanced Aggregation:** 3 separate aggregation endpoints:
      * `GET /devices/stats/average-latency` (Avg stats per category).
      * `GET /devices/<id>/stats` (Avg rating for one device).
      * `GET /auth/myreviews` (Lists all reviews for the logged-in user).
  * **Advanced Search:**
      * **Full-Text Search:** `GET /devices/search?q=...`
      * **Geo-location Search:** `GET /devices/nearme?lat=...&lon=...`
  * **Advanced Filtering & Pagination:** `GET /devices/` supports dynamic multi-field filtering (e.g., `?category=...&ram_gb=...`) and full pagination (`?pn=...&ps=...`).
  * **Professional Structure:** Fully modularized using Flask Blueprints for `auth`, `devices`, and `reviews`.
  * **Robust Validation:** All endpoints feature strong validation for required fields, data types, value ranges (e.g., `rating 1-5`), and permissions, returning correct HTTP status codes (`400`, `401`, `403`, `404`, `409`).

-----

###  Setup and Installation

**1. Prerequisites:**

  * Python 3.10+
  * MongoDB Server (running locally on `mongodb://127.0.0.1:27017`)

**2. Create and Activate Virtual Environment:**

```bash
# 1. Create the environment
python -m venv venv

# 2. Activate it (Windows)
venv\Scripts\activate
```

**3. Install Dependencies:**

```bash
# 3. Install all required packages
pip install -r requirements.txt
```

**4. Prepare the Database (One-Time Setup):**
You must run these 2 scripts *in order* to set up the database.

```bash
# 4. Create the 'admin' and 'user' accounts
python create_users.py

# 5. Create the text index for searching
python create_text_index.py

# 6. Add random location data and the 2dsphere index
python add_locations.py
```

**5. Run the Server:**

```bash
# 7. Run the application
python app.py
```

The API will now be running on `http://127.0.0.1:5000`.

-----

### Test Accounts

Use these accounts in Postman (Basic Auth) to test the `GET /api/v1.0/auth/login` endpoint.

| Role | Username | Password |
| :--- | :--- | :--- |
| **Admin** | `admin` | `admin_pass` |
| **User** | `user` | `user_pass` |

-----

### API Endpoint Overview (23 Endpoints)

#### Authentication Endpoints (`/api/v1.0/auth`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/register` | Public | Creates a new **User** account. |
| `GET` | `/login` | Public | Logs in (Basic Auth), returns a JWT. |
| `GET` | `/logout` | **User** | Logs out (blacklists the JWT). |
| `GET` | `/profile` | **User** | Reads the logged-in user's profile. |
| `PUT` | `/profile` | **User** | Updates the logged-in user's profile. |
| `DELETE`| `/profile` | **User** | Deletes the logged-in user's account. |
| `GET` | `/myreviews` | **User** | Aggregates all reviews by the current user. |
| `GET` | `/admin/users` | **Admin** |  Gets a list of all users. |
| `DELETE`| `/admin/users/delete/<id>` | **Admin** |  Deletes a specific user. |

 Device Endpoints (`/api/v1.0/devices`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Public |  Gets all devices. Supports filtering (`?category=...`, `?ram_gb=...`) and pagination (`?pn=...&ps=...`). |
| `POST` | `/add` | **Admin** | Creates a new device. |
| `GET` | `/<id>` | Public | Gets a single device by its ID. |
| `PUT` | `/update/<id>` | **Admin** | Updates a device's details. |
| `DELETE`| `/delete/<id>` | **Admin** | Deletes a device. |
| `GET` | `/stats/average-latency` | Public |  Aggregates average latency by category. |
| `GET` | `/search` | Public |  Full-text search. (e.g., `?q=NVIDIA`) |
| `GET` |	`/stats/top-rated-by-manufacturer` |	Public |	Aggregates top-rated manufacturers by review score. |
| `GET` | `/nearme` | Public |  Geo-location search. (e.g., `?lat=...&lon=...`) |

#### Review Endpoints (`/api/v1.0/devices`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/<id>/reviews/` | Public | Gets all reviews for a specific device. |
| `POST` | `/<id>/reviews/add` | **User** | Adds a new review to a device. |
| `PUT` | `/<id>/reviews/update/<review_id>` | **Author/Admin** | Updates one's own review (Admins can override). |
| `DELETE`| `/<id>/reviews/delete/<review_id>` | **Author/Admin** | Deletes one's own review (Admins can override). |
| `GET` | `/<id>/stats` | Public |  Gets avg rating and count for one device. |"# ai-directory-be-dev" 
