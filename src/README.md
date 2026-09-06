# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign in as a teacher to register students
- Display scheduled, database-backed school announcements
- Create, edit, and delete announcements from the web interface

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                     | Description                                                        |
| ------ | -------------------------------------------- | ------------------------------------------------------------------ |
| GET    | `/activities`                                | Get activities, with optional day and time filters                 |
| POST   | `/activities/{activity_name}/signup`         | Register a student; requires a teacher username                    |
| POST   | `/activities/{activity_name}/unregister`     | Unregister a student; requires a teacher username                  |
| POST   | `/auth/login`                                | Sign in and receive a session token                                |
| GET    | `/auth/check-session`                        | Validate the token supplied in the `X-Session-Token` header        |
| POST   | `/auth/logout`                               | Invalidate the token supplied in the `X-Session-Token` header      |
| GET    | `/announcements`                             | Get announcements active on the current date                      |
| GET    | `/announcements/manage`                     | Get all announcements; requires `X-Session-Token`                  |
| POST   | `/announcements`                             | Create an announcement; requires `X-Session-Token`                 |
| PUT    | `/announcements/{announcement_id}`           | Update an announcement; requires `X-Session-Token`                 |
| DELETE | `/announcements/{announcement_id}`           | Delete an announcement; requires `X-Session-Token`                 |

Announcement create and update requests use this JSON shape:

```json
{
   "message": "The library will close at 4 PM on Friday.",
   "start_date": "2026-09-07",
   "expiration_date": "2026-09-11"
}
```

`expiration_date` is required. `start_date` is optional and may be `null`.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Teachers** - Uses username as identifier:
   - Display name
   - Password hash
   - Role

3. **Announcements** - Uses a MongoDB object identifier:
   - Message
   - Optional start date
   - Required expiration date

Data is stored in the local `mergington_high` MongoDB database.
