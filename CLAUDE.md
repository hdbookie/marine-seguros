# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the Application
```bash
# Main application
streamlit run app_refactored.py

# Docker development mode (with live code editing)
./scripts/docker-dev.sh

# Docker production mode
./scripts/docker-prod.sh

# Docker rebuild
./scripts/docker-rebuild.sh
```

### Testing
```bash
# Run specific test files (various test scripts available)
python test_hierarchy.py
python test_viagens_extraction.py
python test_minimal.py
# Note: No unified test runner configured - tests are run individually
```

### Database Management
```bash
# Admin database operations
python admin_db.py
```

## High-Level Architecture

### Core System Design
The application is a **Streamlit-based financial analytics dashboard** with three main architectural layers:

1. **Data Processing Layer** (`core/`)
   - **Financial Extractors**: Hierarchical extraction system with base class `BaseHierarchicalExtractor` that all specific extractors inherit from (revenue, costs, taxes, etc.)
   - **Unified Extractor**: `UnifiedFinancialExtractor` coordinates all extractors to process Excel files
   - **Group Hierarchy Processor**: Handles parent-child relationships in financial line items
   - **Database Manager**: SQLite-based persistence for extracted data and auth

2. **UI Layer** (`ui/tabs/`)
   - **Tab-based Architecture**: Each major feature is a separate tab module
   - **Micro Analysis V2**: Advanced visualization system with time series, pattern analysis, and smart comparisons
   - **Legacy Support**: Maintains backward compatibility with original dashboard tabs

3. **AI Integration** (`ai/`, `core/ai_analyzer.py`)
   - **Google Gemini API**: Powers AI insights and chat features
   - **Chat Assistant**: Interactive financial analysis assistant

### Data Flow
1. **Excel Upload** → Processed through extractors that identify hierarchical financial structures
2. **Extraction** → Each extractor specializes in specific financial categories (revenue, fixed costs, variable costs, etc.)
3. **Hierarchical Processing** → Parent-child relationships are preserved for drill-down analysis
4. **Storage** → Extracted data stored in SQLite databases (`dashboard.db`, `auth.db`)
5. **Visualization** → Plotly-based interactive charts with multiple analysis views

### Key Architectural Decisions
- **Hierarchical Data Model**: Financial line items maintain parent-child relationships for detailed analysis
- **Extractor Pattern**: Each financial category has its own extractor for modularity
- **Session State Management**: Streamlit session state manages user data and filters
- **Dual Database System**: Separate databases for application data and authentication

### Authentication System
- JWT-based authentication with bcrypt password hashing
- Admin panel for user management
- Session management through Streamlit

### Environment Configuration
Required environment variables in `.env`:
- `GEMINI_API_KEY`: Google Gemini API key for AI features
- `MAKE_WEBHOOK_URL`: Optional webhook for integrations