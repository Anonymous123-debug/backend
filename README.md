# Calendar Sync Backend

A FastAPI-based backend service for two-way synchronization between a custom application and Google Calendar. This service enables users to manage calendar events that stay in sync across both platforms.

## Features

- 🔐 **Google OAuth Authentication** - Secure user authentication via Google OAuth 2.0
- 📅 **Two-Way Sync** - Bidirectional synchronization between app and Google Calendar
- 🔄 **Real-time Updates** - Webhook-based event notifications from Google Calendar
- 🕐 **Fixed Slots Management** - Create and manage recurring time slots
- 🔒 **Loop Prevention** - Built-in safeguards against infinite sync loops
- 📊 **Database Persistence** - SQLAlchemy-based data management with Alembic migrations

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLAlchemy with PostgreSQL/SQLite support
- **Google APIs**: Google Calendar API, OAuth 2.0
- **Migrations**: Alembic
- **Background Jobs**: APScheduler
- **Validation**: Pydantic

## Prerequisites

- Python 3.8+
- PostgreSQL (or SQLite for development)
- Google Cloud Project with Calendar API enabled
- Google OAuth 2.0 credentials

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd backend
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your credentials:
   - Google OAuth credentials from Google Cloud Console
   - Database URL
   - Webhook base URL (use ngrok for local development)
   - Secret key for sessions

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the server**
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`

## Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/auth/google/callback`
5. Copy the Client ID and Client Secret to your `.env` file

## Configuration

Key environment variables in `.env`:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Database connection string |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret |
| `OAUTH_REDIRECT_URI` | OAuth callback URL |
| `WEBHOOK_BASE_URL` | Base URL for Google webhook notifications |
| `SECRET_KEY` | Secret key for session management |

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

#### Authentication
- `POST /auth/users` - Create a new user
- `GET /auth/google/authorize` - Start Google OAuth flow
- `GET /auth/google/callback` - OAuth callback handler

#### Slots Management
- `POST /slots` - Create a fixed slot
- `GET /slots/{user_id}` - Get all slots for a user
- `PUT /slots/{slot_id}` - Update a slot
- `DELETE /slots/{slot_id}` - Delete a slot

#### Webhooks
- `POST /webhooks/google` - Handle Google Calendar webhook notifications
- `POST /webhooks/google/watch/{user_id}` - Set up Google Calendar watch

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── alembic/               # Database migrations
│   └── env.py
├── api/                   # API route handlers
│   ├── auth.py           # Authentication endpoints
│   ├── slots.py          # Slots management endpoints
│   └── webhooks.py       # Webhook handlers
├── persistence/          # Database layer
│   ├── database.py       # Database configuration
│   ├── models.py         # SQLAlchemy models
│   └── repositories/     # Data access layer
│       ├── user_repository.py
│       ├── fixed_slot_repository.py
│       └── sync_state_repository.py
├── services/             # Business logic
│   ├── google_oauth.py   # Google OAuth service
│   ├── calendar_service.py # Google Calendar operations
│   └── sync_engine.py    # Two-way sync logic
└── schemas/              # Pydantic schemas
    └── slot_schemas.py
```

## Development

### Running in Development Mode

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Creating Database Migrations

```bash
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Testing with ngrok

For webhook testing in development:

```bash
ngrok http 8000
```

Update `WEBHOOK_BASE_URL` in `.env` with the ngrok URL.

## Usage Example

1. **Create a user and authenticate**:
   ```bash
   curl -X POST http://localhost:8000/auth/users \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com"}'
   ```

2. **Complete OAuth flow**:
   Visit the authorization URL returned in the response.

3. **Create a fixed slot**:
   ```bash
   curl -X POST http://localhost:8000/slots \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": 1,
       "title": "Morning Standup",
       "google_start_datetime": "2026-02-10T09:00:00Z",
       "google_end_datetime": "2026-02-10T09:30:00Z"
     }'
   ```

## Sync Logic

The sync engine implements bidirectional synchronization with loop prevention:

- **App → Google**: Changes made in the app are pushed to Google Calendar
- **Google → App**: Changes from Google Calendar are pulled via webhooks
- **Loop Prevention**: Circuit breaker pattern prevents infinite sync loops
- **Conflict Resolution**: Last-write-wins strategy with source tracking

## Security Considerations

- Never commit `.env` file with sensitive credentials
- Use environment variables for all secrets
- Implement rate limiting for production deployments
- Enable HTTPS for production
- Regularly rotate OAuth tokens and secret keys
- Review and restrict CORS origins for production

## Troubleshooting

### Common Issues

1. **OAuth callback errors**: Ensure redirect URI matches exactly in Google Cloud Console
2. **Database connection errors**: Check DATABASE_URL format and database server status
3. **Webhook not receiving events**: Verify ngrok/webhook URL is accessible and properly configured
4. **Sync loops**: Check last_updated_source values and circuit breaker settings

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions, please open an issue on GitHub.
