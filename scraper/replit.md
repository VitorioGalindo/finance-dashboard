# Overview

This is a comprehensive Brazilian financial market API that provides complete access to all Brazilian financial market data. The system implements all 13 data points from the official specification, collecting historical data since 2012 for ~400 companies with active B3 tickers.

**MAJOR UPDATE (2025-07-28):** Complete implementation of all 13 data collection points with systematic CVM/RAD scraping, extended database models, and comprehensive API documentation. The system now provides complete historical financial data collection since 2012 for all B3-listed companies, with interactive dashboard frontend allowing users to select any of the ~120 companies and view all scraped data for testing and validation.

**NEW FEATURES:**
- B3 Company Filter: Reduced from 800+ to ~400 companies with active tickers
- Complete CVM/RAD Scraper: Implementation of all 13 data points from specification since 2012
- Extended Database Models: 13 specialized tables for comprehensive data storage
- Professional API Documentation: Complete REST API documentation with all endpoints
- Historical Data Collection: Systematic collection from 2012 to present for all B3 companies
- Interactive Testing Dashboard: Frontend interface allowing selection of any B3 company to view and test all 13 data points collected by the scraping system
- Real-time Data Integration: Live connection between scraped data, database, and frontend dashboard

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular Flask architecture with clear separation of concerns:

### Backend Framework
- **Flask**: Main web framework with extensions for CORS, rate limiting, and WebSocket support
- **SQLAlchemy**: ORM for database operations with declarative base models
- **Flask-SocketIO**: Real-time WebSocket communication for streaming market data
- **Redis**: Used for caching, rate limiting storage, and session management

### Database Design
- **SQLite/PostgreSQL**: Primary database (configurable via DATABASE_URL)
- **Models**: Company, Quote, FinancialStatement, APIKey, and related financial entities
- **Relationships**: Proper foreign key relationships between companies, tickers, and financial data

### API Structure
- **RESTful Design**: 7 main modules (companies, market, macroeconomics, news, technical analysis, calendar, streaming)
- **Rate Limiting**: Redis-based rate limiting with different tiers (basic, professional, enterprise)
- **Authentication**: API key-based authentication with hashed storage
- **Response Format**: Standardized JSON responses with consistent error handling

## Key Components

### Authentication & Authorization
- **API Key System**: Secure API key generation and validation using SHA-256 hashing
- **Rate Limiting**: Tiered rate limiting (1K-100K requests/hour) based on subscription plans
- **JWT Support**: Optional JWT tokens for enhanced security

### Data Services
- **External API Integration**: Integration with Brazilian financial data providers (brapi.dev, Partnr, DadosDeMercado)
- **Caching Layer**: Redis-based caching with configurable TTL for different data types
- **Data Fetching**: Centralized data fetching service with error handling and fallbacks

### Real-time Features
- **WebSocket Streaming**: Real-time market data streaming with subscription management
- **Connection Management**: Active connection tracking and subscription room management
- **Authentication**: WebSocket authentication using API keys

### Financial Calculations
- **Technical Indicators**: SMA, EMA, RSI, MACD, Bollinger Bands calculations
- **Financial Ratios**: Comprehensive liquidity, profitability, leverage, and efficiency ratios
- **Sentiment Analysis**: Brazilian Portuguese sentiment analysis for news and market data

## Data Flow

1. **API Requests**: Client requests come through Flask routes with API key validation
2. **Rate Limiting**: Redis checks request limits before processing
3. **Caching Check**: System checks Redis cache for existing data
4. **External APIs**: If cache miss, fetch from external financial data providers
5. **Data Processing**: Apply calculations, transformations, and sentiment analysis
6. **Response**: Return standardized JSON response with appropriate headers
7. **WebSocket Updates**: Real-time data pushed to subscribed clients

## External Dependencies

### Financial Data Providers
- **brapi.dev**: Brazilian stock quotes and company data
- **Partnr.ai**: Advanced financial statements and company reports
- **DadosDeMercado**: Macroeconomic indicators and market data
- **Yahoo Finance**: Supplementary international market data

### Third-party Services
- **Redis**: Caching and rate limiting (localhost:6379)
- **TextBlob**: Sentiment analysis for Portuguese text
- **NumPy/Pandas**: Financial calculations and data analysis

### Frontend Technologies
- **Bootstrap 5**: UI framework for responsive design
- **Chart.js**: Interactive financial charts and visualizations
- **Font Awesome**: Icon library for UI elements
- **WebSocket Client**: Real-time data consumption

## Deployment Strategy

### Environment Configuration
- **Development**: SQLite database with debug mode enabled
- **Production**: PostgreSQL database with optimized connection pooling
- **Environment Variables**: Secure API key storage and configuration management

### Scalability Considerations
- **Database Pooling**: SQLAlchemy connection pooling for concurrent requests
- **Redis Clustering**: Scalable caching and rate limiting infrastructure
- **WebSocket Scaling**: SocketIO namespace support for horizontal scaling

### Security Measures
- **API Key Hashing**: Secure storage of API keys using SHA-256
- **Rate Limiting**: Prevent API abuse with Redis-based limiting
- **CORS Configuration**: Controlled cross-origin resource sharing
- **Proxy Fix**: Proper handling of reverse proxy headers

### Monitoring & Logging
- **Comprehensive Logging**: Structured logging for debugging and monitoring
- **Error Handling**: Graceful error handling with standardized error responses
- **Health Checks**: API endpoints for system health monitoring