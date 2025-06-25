# 🏛️ Data Governance API - Enterprise Solution

## 📋 Overview

Enterprise-grade Data Governance API built following **SOLID principles** and **Clean Architecture**. This API provides comprehensive data governance capabilities including data objects management, quality metrics, lineage tracking, access policies, and compliance monitoring.

## 🎯 Key Features

### ✅ **Complete SOLID Implementation**
- **Single Responsibility Principle (SRP)**: Each class has one reason to change
- **Open/Closed Principle (OCP)**: Open for extension, closed for modification
- **Liskov Substitution Principle (LSP)**: Derived classes are substitutable
- **Interface Segregation Principle (ISP)**: Clients depend only on interfaces they use
- **Dependency Inversion Principle (DIP)**: Depend on abstractions, not concretions

### ✅ **Comprehensive Endpoints**
- **Data Objects**: Complete CRUD operations with advanced filtering
- **Data Contracts**: Define and manage data contracts
- **Quality Metrics**: Monitor and track data quality
- **Data Lineage**: Track data flow and dependencies
- **Access Policies**: Manage data access and security
- **Analytics & Reporting**: Governance dashboards and insights

### ✅ **Enterprise Features**
- **Structured Error Handling**: Hierarchical exception system
- **Authentication & Authorization**: JWT-based with role-based access
- **Audit Logging**: Complete audit trail for all operations
- **Pagination**: Efficient data pagination
- **Validation**: Comprehensive input validation
- **Documentation**: Interactive OpenAPI/Swagger documentation

## 🏗️ Architecture

### **Project Structure**
```
data-governance-api-fixed/
├── src/
│   └── app/
│       ├── config/              # Configuration management
│       │   └── global_config.py
│       ├── models/              # Data models (SQLAlchemy)
│       │   └── data_models.py
│       ├── resources/           # API endpoints and routers
│       │   ├── routers.py
│       │   └── endpoints/
│       │       └── data_objects.py
│       ├── services/            # Business logic services
│       │   ├── interfaces.py
│       │   └── data_objects_service.py
│       └── utils/               # Utilities and helpers
│           ├── database.py
│           ├── exceptions.py
│           ├── pagination.py
│           └── auth.py
├── tests/                       # Test suite
├── docs/                        # Documentation
├── scripts/                     # Automation scripts
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container configuration
├── docker-compose.yml           # Multi-container setup
└── README.md                    # This file
```

### **Clean Architecture Layers**
1. **Presentation Layer** (`resources/`): FastAPI endpoints and routers
2. **Application Layer** (`services/`): Business logic and use cases
3. **Domain Layer** (`models/`): Core business entities
4. **Infrastructure Layer** (`utils/`): External concerns (database, auth, etc.)

## 🚀 Quick Start

### **Prerequisites**
- Python 3.11+
- PostgreSQL (optional, SQLite by default)
- Docker (optional)

### **Installation**

1. **Clone and Setup**
```bash
git clone <repository>
cd data-governance-api-fixed
```

2. **Install Dependencies**
```bash
pip install --user -r requirements.txt
export PATH=$PATH:~/.local/bin
```

3. **Run Application**
```bash
python main.py
```

4. **Access Documentation**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

### **Docker Setup**
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t data-governance-api .
docker run -p 8000:8000 data-governance-api
```

## 📊 API Endpoints

### **Core Endpoints**

#### **Data Objects**
- `GET /api/v1/data-objects/` - List data objects with filtering
- `POST /api/v1/data-objects/` - Create new data object
- `GET /api/v1/data-objects/{id}` - Get specific data object
- `PUT /api/v1/data-objects/{id}` - Update data object
- `DELETE /api/v1/data-objects/{id}` - Delete data object
- `POST /api/v1/data-objects/{id}/schema` - Update object schema
- `GET /api/v1/data-objects/{id}/schema` - Get object schema
- `POST /api/v1/data-objects/{id}/classify` - Classify object
- `GET /api/v1/data-objects/{id}/usage` - Get usage statistics
- `GET /api/v1/data-objects/{id}/popularity` - Get popularity metrics

#### **Health & Monitoring**
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /metrics` - Application metrics

### **Advanced Features**
- **Filtering**: Filter by type, catalog, database, classification, etc.
- **Pagination**: Efficient pagination with metadata
- **Search**: Full-text search across objects
- **Sorting**: Sort by various fields
- **Include Options**: Include related data (lineage, quality, contracts, policies)

## 🔧 Configuration

### **Environment Variables**
```bash
# Database
DATABASE_URL=sqlite:///./data_governance.db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_ECHO=false

# Server
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_HOURS=24
ALGORITHM=HS256

# Logging
LOG_LEVEL=INFO

# CORS
ALLOWED_HOSTS=["*"]
```

### **Database Models**
The API includes comprehensive data models for:
- **DataObject**: Core data object entity
- **DataContract**: Data contract definitions
- **QualityMetric**: Quality measurement results
- **DataLineage**: Data flow relationships
- **AccessPolicy**: Access control policies
- **AuditLog**: Audit trail records
- **User**: User management

## 🧪 Testing

### **Run Tests**
```bash
# Install test dependencies
pip install --user pytest pytest-asyncio pytest-cov

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_data_objects.py
```

### **API Testing**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test data objects endpoint (requires authentication)
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/data-objects/
```

## 📚 Documentation

### **Interactive Documentation**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### **OpenAPI Specification**
- **JSON**: http://localhost:8000/openapi.json

### **Code Documentation**
All code follows comprehensive documentation standards:
- **Docstrings**: Every function and class documented
- **Type Hints**: Full type annotation coverage
- **SOLID Principles**: Documented in code comments
- **Architecture Decisions**: Explained in implementation

## 🔒 Security

### **Authentication**
- **JWT Tokens**: Secure token-based authentication
- **Role-Based Access**: Granular permission system
- **Token Expiration**: Configurable token lifetime

### **Authorization**
- **Role Checking**: Endpoint-level role requirements
- **Resource Access**: Object-level access control
- **Audit Logging**: Complete access audit trail

### **Data Protection**
- **Input Validation**: Comprehensive input sanitization
- **SQL Injection Prevention**: Parameterized queries
- **CORS Configuration**: Configurable cross-origin policies

## 🚀 Deployment

### **Production Deployment**
1. **Environment Setup**
```bash
export ENVIRONMENT=production
export DATABASE_URL=postgresql://user:pass@host:port/db
export SECRET_KEY=your-production-secret
```

2. **Database Migration**
```bash
# Create tables
python -c "from src.app.utils.database import create_tables; create_tables()"
```

3. **Run with Gunicorn**
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### **Docker Production**
```bash
# Build production image
docker build -t data-governance-api:prod .

# Run with environment variables
docker run -d \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL=postgresql://... \
  data-governance-api:prod
```

## 🔍 Monitoring

### **Health Checks**
- **Application Health**: `/health` endpoint
- **Database Connectivity**: Included in health check
- **Dependency Status**: Service availability monitoring

### **Metrics**
- **Request Metrics**: Request count, response time
- **Error Tracking**: Error rates and types
- **Performance Monitoring**: Resource usage tracking

### **Logging**
- **Structured Logging**: JSON-formatted logs
- **Audit Trail**: Complete operation logging
- **Error Tracking**: Detailed error information

## 🤝 Contributing

### **Development Setup**
1. **Fork and Clone**
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Run Tests**: `pytest`
4. **Follow SOLID Principles**: Maintain architectural integrity
5. **Add Tests**: Ensure comprehensive test coverage
6. **Update Documentation**: Keep docs current

### **Code Standards**
- **SOLID Principles**: Strictly enforced
- **Type Hints**: Required for all functions
- **Docstrings**: Required for all public methods
- **Error Handling**: Use custom exception hierarchy
- **Testing**: Minimum 90% coverage required

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Support

For support and questions:
- **Documentation**: Check the interactive API docs
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub discussions for questions

---

**Built with ❤️ following SOLID principles and Clean Architecture**

