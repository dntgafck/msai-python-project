# Dutch Language Learning Service

A Python application for Dutch language learning that extracts unfamiliar Dutch nouns from text and generates English definitions with Dutch examples and translations. The system combines natural language processing with AI-powered definition generation and database persistence.

## Features

- **Dutch NLP Processing**: Extracts unfamiliar Dutch nouns using spaCy's Dutch model
- **AI Definition Generation**: Uses OpenAI to generate English definitions for Dutch words
- **Dutch Examples with Translations**: Provides Dutch example sentences with English translations
- **Semantic Categories**: Includes relevant categories for each word
- **Database Persistence**: SQLite-based storage for words and definitions
- **Web Interface**: User-friendly Streamlit frontend for interactive usage
- **REST API**: FastAPI-based API for programmatic access
- **Batch Processing**: Efficient AI API usage with configurable batch sizes
- **Structured Output**: Uses OpenAI's structured output with Pydantic models
- **Pure Components**: Standalone services without database dependencies
- **Docker Support**: Complete containerization with spaCy model verification

## Project Structure

```
msai-python-project/
├── api/                    # REST API interface
│   ├── __init__.py
│   └── rest_api.py        # FastAPI implementation
├── database/              # Database layer
│   ├── __init__.py
│   ├── connection.py      # Database connection management
│   └── schema.py          # Database schema and table creation
├── models/                # Data models
│   ├── __init__.py
│   └── entities.py        # Dataclass entities
├── repositories/          # Data access layer
│   ├── __init__.py
│   ├── user_repository.py
│   ├── word_repository.py
│   ├── definition_repository.py
│   └── vocabulary_repository.py
├── services/              # Business logic
│   ├── __init__.py
│   ├── nlp_service.py     # Dutch NLP service
│   ├── ai_service.py      # AI definition generation
│   └── vocabulary_service.py # Vocabulary management
├── streamlit_app.py       # Streamlit web frontend
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker containerization
├── docker-compose.yml    # Docker Compose configuration
├── env.example           # Environment variables template
└── README.md             # This file
```

## Installation

### Option 1: Local Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd msai-python-project
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Dutch spaCy model**:
   ```bash
   python -m spacy download nl_core_news_lg
   ```

5. **Verify spaCy installation** (optional but recommended):
   ```bash
   python verify_spacy.py
   ```

6. **Set up OpenAI API key**:
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```

### Option 2: Docker Installation (Recommended)

The easiest way to run the application is using Docker, which automatically handles all dependencies including the spaCy model.

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd msai-python-project
   ```

2. **Set up environment file**:
   ```bash
   cp env.example .env
   # Edit .env file and add your OpenAI API key
   ```

3. **Deploy with Docker**:
   ```bash
   # Make the deployment script executable
   chmod +x deploy.sh
   
   # Run the deployment script
   ./deploy.sh
   ```

   The deployment script will:
   - Build the Docker image
   - Verify spaCy model installation
   - Start the application
   - Perform health checks
   - Provide access information

4. **Access the application**:
   - Web interface: http://localhost:8501
   - Health check: http://localhost:8501/_stcore/health

#### Docker Commands

```bash
# Build the image
docker build -t dutch-learning-app .

# Run with docker-compose
docker-compose up -d

# Run with docker directly
docker run -d \
  --name dutch-learning-app \
  --env-file .env \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  dutch-learning-app

# View logs
docker logs -f dutch-learning-app

# Stop the application
docker stop dutch-learning-app

# Remove the container
docker rm -f dutch-learning-app
```

#### Docker Features

- **Automatic spaCy Model Installation**: The Docker image automatically downloads and verifies the Dutch spaCy model
- **Health Checks**: Built-in health monitoring for the application
- **Volume Mounting**: Persistent storage for data and logs
- **Security**: Runs as non-root user
- **Resource Limits**: Memory and CPU constraints for stability
- **Environment Management**: Easy configuration via .env file

## Quick Start

### Web Interface (Recommended)

The easiest way to use the system is through the Streamlit web interface:

```bash
# Start the Streamlit application
streamlit run streamlit_app.py
```

The web interface provides:
- **Text Processing**: Upload or paste Dutch text to extract unfamiliar nouns
- **AI Features**: Generate definitions for Dutch words
- **Vocabulary Management**: Browse and search your stored vocabulary
- **Interactive UI**: User-friendly interface with real-time feedback

### Dutch NLP Service (No Database)

```python
from services.nlp_service import NLPService

# Initialize Dutch NLP service
nlp_service = NLPService()

# Process Dutch text
dutch_text = "De computer verwerkt complexe algoritmes."
known_words = {"computer", "algoritme"}

results = nlp_service.process_text(dutch_text, known_words)
print(f"Found {len(results)} unfamiliar Dutch words")
```

### AI Definition Service (No Database)

```python
from services.ai_service import AIService

# Initialize AI service
ai_service = AIService()

# Generate definitions for Dutch words
dutch_words = ["algoritme", "computer", "systeem"]
definitions = ai_service.generate_definitions(dutch_words)

for definition in definitions:
    print(f"Word: {definition.lemma}")
    print(f"Definition: {definition.definition}")
    print(f"Dutch Example: {definition.example}")
    print(f"English Translation: {definition.english_translation}")
```

### Complete System with Database

```python
from database.connection import DatabaseConnection
from database.schema import create_tables
from services.nlp_service import NLPService
from services.ai_service import AIService

# Initialize database
db_connection = DatabaseConnection()
create_tables(db_connection)

# Initialize services
nlp_service = NLPService()
ai_service = AIService()

# Process Dutch text
dutch_text = "De computer verwerkt complexe algoritmes."
results = nlp_service.process_text(dutch_text)

# Generate definitions for Dutch lemmas
lemmas = [result['lemma'] for result in results]
definitions = ai_service.generate_definitions(lemmas)

for definition in definitions:
    print(f"{definition.lemma}:")
    print(f"  Definition: {definition.definition}")
    print(f"  Example: {definition.example}")
    print(f"  Translation: {definition.english_translation}")
    print(f"  Categories: {', '.join(definition.category)}")
```

## Usage

### 1. Streamlit Web Interface

The Streamlit frontend provides an intuitive web interface for all features:

**Features**:
- **Text Processing Tab**: Process Dutch text and extract unfamiliar nouns
- **Vocabulary Tab**: Browse and search stored words and definitions
- **Vocabulary Decks Tab**: Create and manage vocabulary decks with Anki export

**Usage**:
1. Start the application: `streamlit run streamlit_app.py`
2. Open your browser to `http://localhost:8501`
3. Use the tabs to access different features
4. Enter Dutch text or words in the text areas
5. Click buttons to process and generate results

**Key Benefits**:
- No command line knowledge required
- Real-time feedback and progress indicators
- Interactive word cards with expandable details
- Easy known words management
- Visual search and filtering
- Responsive design for different screen sizes

### 2. Dutch NLP Service

The `NLPService` class provides Dutch text processing:

```python
from services.nlp_service import NLPService

nlp_service = NLPService()

# Basic Dutch text processing
results = nlp_service.process_text("De computer verwerkt algoritmes.")

# With known words filtering
known_words = {"computer", "algoritme"}
results = nlp_service.process_text("De computer verwerkt algoritmes.", known_words)
```

**Key Features**:
- Uses spaCy's Dutch model (`nl_core_news_lg`)
- Filters Dutch stopwords automatically
- Validates Dutch words (including accented characters)
- Accepts optional `known_words` parameter for additional filtering
- Returns lemmas with surface forms and frequency counts
- Sorts results by frequency (descending) then alphabetically
- No database dependencies

### 3. AI Definition Service

The `AIService` class generates English definitions for Dutch words:

```python
from services.ai_service import AIService

# Initialize AI service
ai_service = AIService()

# Generate definitions for Dutch words
dutch_words = ["algoritme", "computer", "systeem"]
definitions = ai_service.generate_definitions(dutch_words)
```

### 4. REST API

Start the API server:
```bash
python api/rest_api.py
```

Or with uvicorn:
```bash
uvicorn api.rest_api:app --host 0.0.0.0 --port 8000 --reload
```

**Available Endpoints**:

- `POST /process` - Process Dutch text and return unfamiliar nouns
- `POST /generate-definitions` - Generate English definitions for Dutch words
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

**Example API Usage**:
```bash
# Process Dutch text
curl -X POST "http://localhost:8000/process" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "De computer verwerkt algoritmes.",
       "known_words": ["computer", "algoritme"]
     }'

# Generate definitions
curl -X POST "http://localhost:8000/generate-definitions" \
     -H "Content-Type: application/json" \
     -d '{
       "lemmas": ["algoritme", "computer"]
     }'
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required for AI features)
- `OPENAI_MODEL`: OpenAI model to use (default: `gpt-4o-mini`)

### AI Service Configuration

The AI service can be configured with:

```python
ai_service = AIService(
    api_key="your-api-key",  # Optional, defaults to OPENAI_API_KEY env var
    model="gpt-4o-mini",     # Optional, defaults to gpt-4o-mini
    batch_size=20            # Optional, defaults to 20
)
```

## API Reference

### NLPService

```python
class NLPService:
    def __init__(self, model_name: str = "nl_core_news_lg")
    
    def process_text(self, text: str, known_words: Optional[Set[str]] = None) -> List[Dict]
```

### AIService

```python
class AIService:
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini", batch_size: int = 20)
    
    def generate_definitions(self, lemmas: List[str]) -> List[DefinitionItem]
```

### DefinitionItem (Pydantic Model)

```python
class DefinitionItem(BaseModel):
    lemma: str                    # The Dutch word
    definition: str               # English definition
    example: str                  # Dutch example sentence
    english_translation: str      # English translation of example
    category: List[str]           # Semantic categories
```

## Troubleshooting

### Common Issues

1. **spaCy model not found**:
   ```bash
   python -m spacy download nl_core_news_lg
   ```

2. **OpenAI API key not set**:
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```

3. **Database connection issues**:
   - Check file permissions for `app.db`
   - Ensure SQLite is available

4. **AI service errors**:
   - Verify OpenAI API key is valid
   - Check API quota and rate limits
   - Ensure internet connection

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or use the debug script:

```bash
python debug_ai_response.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## TODO

### User Management Features

The application currently operates as a single-user demo system with hardcoded `user_id = 1`. Future enhancements could include:

- **User Authentication**: Add login/register functionality using the existing `User` entity and `UserRepository`
- **Multi-User Support**: Enable multiple users to have their own vocabulary decks and known words
- **User-Specific Known Words**: Implement persistent storage of user's known words using the prepared `user_known_word` table structure
- **User Profiles**: Add user profile management with preferences and learning statistics
- **Session Management**: Implement proper session handling and user state persistence
- **Access Control**: Add role-based access control for different user types (students, teachers, etc.)

### Technical Implementation Notes

The infrastructure for user management is already prepared:
- `User` entity in `models/entities.py`
- `UserRepository` in `repositories/user_repository.py`
- `user` table schema in `database/schema.py`
- Foreign key relationships in `vocabulary_deck` table

## License

This project is licensed under the MIT License - see the LICENSE file for details.