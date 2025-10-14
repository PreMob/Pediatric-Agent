# 👶 Pediatric Agent

A comprehensive pediatric health monitoring system with growth tracking, nutrition logging, and health analytics for parents and healthcare providers.

## 🚀 Features

- **User Management**: Secure registration, login, and profile management with JWT authentication
- **Child Profiles**: Complete CRUD operations for managing child information
- **Growth Tracking**: Monitor height, weight, and head circumference with trend analysis
- **Nutrition Logging**: Detailed meal tracking with macronutrient analysis and recommendations
- **Health Analytics**: Growth percentiles, nutrition summaries, and personalized insights
- **Secure Access**: Parent-child relationship authorization and data protection

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: Async ORM with MySQL database support
- **JWT Authentication**: Secure token-based authentication
- **Pydantic**: Data validation and serialization
- **Poetry**: Dependency management and packaging
- **Uvicorn**: ASGI server for production-ready deployment

### Database
- **MySQL**: Primary database for structured data
- **MongoDB**: Document storage for flexible data (configured but optional)

## 📋 Prerequisites

- Python 3.10 or higher
- Poetry (for dependency management)
- MySQL server (local or remote)
- Git

## 🔧 Backend Setup

### 1. Clone the Repository
```bash
git clone https://github.com/PreMob/Pediatric-Agent.git
cd Pediatric-Agent/Backend
```

### 2. Install Poetry (if not installed)
```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -
```

### 3. Install Dependencies
```bash
poetry install
```

### 4. Environment Configuration
Create a `.env` file in the Backend directory:
```env
# Database Configuration
MYSQL_USER=your_mysql_username
MYSQL_PASSWORD=your_mysql_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=pediatric_agent_db

# MongoDB Configuration (Optional)
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=pediatric_agent_mongo

# JWT Configuration
SECRET_KEY=your-super-secret-jwt-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=info
```

### 5. Database Setup
Ensure your MySQL server is running and create the database:
```sql
CREATE DATABASE pediatric_agent_db;
```

### 6. Start Development Server
```bash
cd Backend
poetry run poe dev
```

The API will be available at:
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints

### Authentication & Users
- `POST /api/v1/users/register` - Register new user
- `POST /api/v1/users/login` - User login
- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/update` - Update user info

### Child Management
- `POST /api/v1/children/` - Add child
- `GET /api/v1/children/` - List user's children
- `GET /api/v1/children/{child_id}` - Get child details
- `PUT /api/v1/children/{child_id}` - Update child info
- `DELETE /api/v1/children/{child_id}` - Remove child

### Growth Tracking
- `POST /api/v1/growth/` - Add growth measurement
- `GET /api/v1/growth/{child_id}` - Get growth history
- `GET /api/v1/growth/stats/{child_id}` - Growth analysis & trends

### Nutrition Logging
- `POST /api/v1/nutrition/` - Log meal
- `GET /api/v1/nutrition/{child_id}` - Get nutrition history
- `GET /api/v1/nutrition/summary/{child_id}` - Nutrition analysis & recommendations

## 🔍 Development Commands

```bash
# Start development server with auto-reload
poetry run poe dev

# Install new dependencies
poetry add package-name

# View dependency tree
poetry show --tree

# Enter virtual environment
poetry shell
```

## 📊 Database Schema

The system automatically creates the following tables:
- `users` - User accounts and authentication
- `children` - Child profiles linked to parents
- `growth_logs` - Height, weight, head circumference tracking
- `nutrition_logs` - Meal logging with nutritional data

## 🔐 Security Features

- **JWT Token Authentication**: Secure API access
- **Password Hashing**: Bcrypt encryption
- **Parent Authorization**: Children data access control
- **Input Validation**: Pydantic data validation
- **Error Handling**: Comprehensive error management

## 🚦 Getting Started

1. **Set up the backend** following the installation steps above
2. **Register a new user** via `/api/v1/users/register`
3. **Login** to get your JWT token via `/api/v1/users/login`
4. **Add a child** profile via `/api/v1/children/`
5. **Start tracking** growth and nutrition data

## 📈 Data Analytics

The system provides:
- **Growth Percentiles**: WHO growth chart comparisons
- **Trend Analysis**: Growth pattern tracking
- **Nutrition Goals**: Age-appropriate dietary recommendations
- **Daily Summaries**: Comprehensive nutrition reports
- **Health Insights**: Personalized recommendations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the API documentation at `/docs` when running locally
- Review the error logs in the `Backend/logs/` directory