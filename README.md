# RecallEngine 🔍

**An all-in-one retrieval, indexing, and ingestion tool for RAG and database applications**


## 🎯 Vision

RecallEngine aims to be a comprehensive, production-ready toolkit that simplifies the entire data pipeline for Retrieval-Augmented Generation (RAG) systems and modern database applications. It will provide:

- **🔄 Ingestion**: Flexible data connectors for various sources (documents, APIs, databases)
- **📊 Indexing**: Multiple indexing strategies (inverted index, vector embeddings, hybrid search)
- **🔍 Retrieval**: Advanced search capabilities (keyword, semantic, hybrid) with ranking algorithms
- **⚡ Performance**: Optimized for speed and scalability
- **🛠️ Developer-Friendly**: Simple APIs and CLI tools for rapid integration

---

## 📈 Current Status

RecallEngine is in **active development** (v0.1.0). The foundational components are being built to establish a solid base for the complete system.

### ✅ Implemented Features

- **Text Normalization Pipeline**
  - Lowercase conversion
  - Punctuation removal
  - Tokenization
  - Stop word filtering
  - Porter Stemming algorithm

- **Keyword-Based Search**
  - Query-to-document matching
  - Case-insensitive search
  - Token-based matching

- **CLI Interface**
  - Movie dataset search (proof of concept)
  - Command-line query interface

- **Testing Infrastructure**
  - Unit tests with pytest
  - Integration tests
  - Code coverage reporting

### 🚧 In Progress

- **Indexer Module**: Building inverted index structures for efficient retrieval
- **BM25 Ranking**: Implementation of probabilistic ranking algorithm
- **Data Connectors**: Expanding beyond movie dataset to support multiple formats

---

## 🚀 Getting Started

### Prerequisites

- Python ≥ 3.12
- [Poetry](https://python-poetry.org/) (for dependency management)

### Installation

```bash
# Clone the repository
git clone https://github.com/Shub3am/RecallEngine
cd RecallEngine

# Install dependencies
poetry install --with dev
```

### Quick Start

```bash
# Search the movie dataset
poetry run python recall_engine/cli/keyword_search_cli.py search "action hero"
```

---

## 📖 Usage Examples

### Basic Search

```bash
poetry run python recall_engine/cli/keyword_search_cli.py search "romantic comedy"
```

### Programmatic Usage (Coming Soon)

```python
from recall_engine import RecallEngine

# Initialize engine
engine = RecallEngine()

# Index documents
engine.index_documents(documents)

# Perform search
results = engine.search("query", method="hybrid", top_k=10)
```

---

## 🗺️ Roadmap

### Phase 1: Core Indexing (Current)
- [x] Text normalization pipeline
- [x] Basic keyword search
- [ ] Complete inverted index implementation
- [ ] BM25 ranking algorithm
- [ ] TF-IDF scoring

### Phase 2: Advanced Retrieval
- [ ] Vector embeddings integration
- [ ] Semantic search capabilities
- [ ] Hybrid search (keyword + semantic)
- [ ] Re-ranking algorithms
- [ ] Query expansion

### Phase 3: Ingestion Pipeline
- [ ] Document parsers (PDF, DOCX, HTML, Markdown)
- [ ] Batch processing
- [ ] Streaming ingestion
- [ ] Data validation and cleaning
- [ ] Multiple data source connectors

### Phase 4: Production Features
- [ ] Persistent storage backends
- [ ] Distributed indexing
- [ ] API server (REST/GraphQL)
- [ ] Caching layer
- [ ] Monitoring and analytics

### Phase 5: RAG Integration
- [ ] LLM context preparation
- [ ] Prompt engineering utilities
- [ ] Context window optimization
- [ ] Citation tracking
- [ ] Response grounding

---

## 🏗️ Architecture

```
RecallEngine/
├── recall_engine/
│   ├── cli/               # Command-line interfaces
│   │   ├── keyword_search_cli.py
│   │   ├── misc.py
│   │   └── indexer.py
│   ├── helper/            # Helper utilities
│   │   └── stop_words.txt
│   ├── ingestion/         # [Planned] Data ingestion modules
│   ├── indexing/          # [Planned] Index structures
│   ├── retrieval/         # [Planned] Search algorithms
│   └── embeddings/        # [Planned] Vector operations
├── tests/                 # Test suite
└── data/                  # Sample datasets
```

---

## 🧪 Testing

```bash
# Run all tests
poetry run pytest -v

# Run with coverage
poetry run pytest --cov=recall_engine --cov-report=term-missing

# Generate HTML coverage report
poetry run pytest --cov=recall_engine --cov-report=html
open htmlcov/index.html
```

---

## 🤝 Contributing

Contributions are welcome! RecallEngine is being built to solve real-world retrieval challenges, and your input can help shape its future.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Ensure all tests pass (`poetry run pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for detailed development instructions.

---

## 📝 Documentation

- [Developer Guide](DEVELOPER_GUIDE.md) - Detailed development instructions and conventions
- API Documentation (Coming Soon)
- Tutorials (Coming Soon)

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- NLTK for natural language processing tools
- The information retrieval research community
- All contributors and users of RecallEngine

---

## 📬 Contact

For questions, suggestions, or discussions:

- GitHub Issues: [Report a bug or request a feature](https://github.com/Shub3am/RecallEngine/issues)
- Maintainer: [@Shub3am](https://github.com/Shub3am)

---

**Note**: RecallEngine is under active development. APIs and features may change as the project evolves. Star ⭐ the repository to stay updated!
