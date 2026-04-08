# AlphaDash - MT5 Trading Performance Analytics Dashboard

A professional single-page application (SPA) for centralizing, analyzing, and visualizing performance metrics from multiple MetaTrader 5 (MT5) accounts, with support for strategy tracking via Magic Numbers.

## Features

- **Multi-Account Support**: Manage multiple MT5 accounts (Real, Demo, Prop)
- **Real-Time Metrics**: Win Rate, Profit Factor, Expectancy, Recovery Factor
- **Risk Analysis**: Max Drawdown (Balance/Equity), Sharpe Ratio, Sortino Ratio
- **Temporal Analysis**: Profit by session (hourly), day of week, and monthly
- **Strategy Tracking**: Automatic grouping by Magic Number
- **Interactive Visualizations**: Equity curves, heatmaps, and charts
- **Trade Journal**: Advanced filtering and sorting with TanStack Table
- **Dark Mode Professional UI**: Minimalist design with emerald/coral accents

## Tech Stack

### Backend
- **Python 3.10+** with FastAPI
- **SQLite** with SQLAlchemy ORM
- **Pandas** for financial calculations
- **Alembic** for database migrations

### Frontend
- **React 18** with Vite
- **Tailwind CSS** with Shadcn/UI components
- **Recharts** for visualizations
- **TanStack Table** for data tables
- **Axios** for API communication

## Project Structure

```
alphadash/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry
│   │   ├── config.py            # Configuration settings
│   │   ├── database.py          # Database connection
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routers/             # API endpoints
│   │   ├── services/            # Business logic
│   │   └── utils/               # Utility functions
│   ├── requirements.txt
│   └── run.py                   # Development server
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Page components
│   │   ├── hooks/               # Custom hooks
│   │   ├── lib/                 # Utilities and API
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python run.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The app will be available at `http://localhost:5173`

## API Endpoints

### Accounts
- `GET /api/accounts/` - List all accounts
- `GET /api/accounts/{id}` - Get account by ID
- `POST /api/accounts/` - Create new account
- `PATCH /api/accounts/{id}` - Update account
- `DELETE /api/accounts/{id}` - Delete account

### Trades
- `GET /api/trades/` - List trades with filters
- `GET /api/trades/{id}` - Get trade by ID
- `GET /api/trades/symbols/list` - Get all traded symbols
- `GET /api/trades/magic-numbers/list` - Get all magic numbers

### Metrics
- `GET /api/metrics/global` - Portfolio-wide metrics
- `GET /api/metrics/account/{id}` - Account-specific metrics
- `GET /api/metrics/strategy/{magic_number}` - Strategy metrics
- `GET /api/metrics/equity-curve` - Equity curve data
- `GET /api/metrics/heatmap` - Daily profit heatmap
- `GET /api/metrics/temporal` - Hourly/daily/monthly breakdown

### Ingestion
- `POST /api/ingest/` - Ingest single trade from MT5 EA
- `POST /api/ingest/batch` - Batch ingest multiple trades
- `POST /api/ingest/upload-csv` - Upload MT5 CSV history

## MT5 Integration

### Configuration
Add the API URL to MT5's allowed WebRequest URLs:
1. Open MT5
2. Go to Tools → Options → Expert Advisors
3. Add `http://localhost:8000` to "Allow WebRequest for the following URLs"

### Include the Library
Copy `SendTradeToDash.mqh` to your MT5 `Include` folder.

### Usage in EA

```mql5
#include <SendTradeToDash.mqh>

int OnInit()
{
    AlphaDash_Init();
    return INIT_SUCCEEDED;
}

void OnTradeTransaction(const MqlTradeTransaction& trans,
                        const MqlTradeRequest& request,
                        const MqlTradeResult& result)
{
    if(trans.type == TRADE_TRANSACTION_DEAL_ADD)
    {
        ENUM_DEAL_ENTRY entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
        if(entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_OUT_BY)
        {
            SendTradeToDash(trans.deal);
        }
    }
}
```

## Environment Variables

Create a `.env` file in the backend directory:

```env
DATABASE_URL=sqlite+aiosqlite:///./alphadash.db
API_PREFIX=/api
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
DEBUG=true
```

## Database Migrations

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

## Screenshots

### Dashboard
- Equity curve with cumulative profit visualization
- KPI cards showing core metrics
- Daily performance heatmap calendar
- Strategy performance summary
- Risk metrics panel

### Strategies
- Bar charts for profit by strategy
- Win rate comparison
- Detailed strategy table with symbols

### Journal
- Advanced filtering (symbol, strategy, result)
- Sortable columns
- Trade statistics summary

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For issues and feature requests, please use the GitHub Issues page.