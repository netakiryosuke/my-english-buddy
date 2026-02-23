# Test Suite Documentation

This directory contains unit tests for the My English Buddy application, organized according to Domain-Driven Design (DDD) principles.

## Test Structure

The test directory structure mirrors the application's DDD package structure:

```
tests/
├── domain/                 # Domain layer tests
│   └── vo/                # Value objects
│       └── test_chat_message.py
├── application/           # Application layer tests
│   ├── test_conversation_service.py
│   ├── test_conversation_memory.py
│   └── test_errors.py
├── infrastructure/        # Infrastructure layer tests
│   └── openai/           # OpenAI API implementations
│       ├── test_chat_client.py
│       ├── test_speech_to_text.py
│       └── test_text_to_speech.py
├── utils/                # Utility function tests
│   ├── test_text.py
│   ├── test_logger.py
│   ├── test_args.py
│   └── test_env.py
├── test_config.py        # Configuration tests
└── conftest.py           # Shared fixtures and test configuration
```

## Running Tests

Run all tests:
```bash
pytest
```

Run tests with verbose output:
```bash
pytest -v
```

Run a specific test file:
```bash
pytest tests/domain/vo/test_chat_message.py
```

Run tests matching a pattern:
```bash
pytest -k "openai"
```

## Test Coverage

Current test coverage includes:

### Domain Layer (7 tests - NEW)
- **ChatMessage** (7 tests): Value object immutability, equality, and edge cases

### Domain Layer (11 tests - EXISTING)
- **ConversationMemory** (11 tests): Message storage, retrieval, memory limits

### Application Layer (8 tests - NEW)
- **Errors** (8 tests): Custom exception classes and inheritance

### Application Layer (11 tests - EXISTING)
- **ConversationService** (11 tests): Reply logic, system prompts, memory window

### Infrastructure Layer (20 tests - NEW)
- **OpenAI ChatClient** (6 tests): Message completion, error handling
- **OpenAI SpeechToText** (7 tests): Audio transcription, silence detection
- **OpenAI TextToSpeech** (7 tests): Speech synthesis, audio normalization

### Utils (22 tests - NEW)
- **Text utilities** (5 tests): File reading, whitespace handling
- **Logger** (9 tests): Logging, callbacks, file output
- **Args** (4 tests): Argument parsing
- **Env** (4 tests): Environment variable loading

### Configuration (17 tests - NEW)
- **AppConfig** (17 tests): Configuration creation, environment parsing, validation

**Total: 95 tests (74 new + 21 existing)**

## Testing Principles

### 1. Mock External Dependencies
External I/O operations (databases, APIs, file system) are mocked to ensure:
- Tests run quickly and reliably
- No external service dependencies
- Predictable test results

Example:
```python
def test_complete_with_system_and_user(self, mock_openai_client):
    mock_response = Mock()
    mock_response.choices[0].message.content = "Test response"
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    client = OpenAIChatClient(client=mock_openai_client, model="gpt-4")
    response = client.complete(system="System", user="Hello")
    
    assert response == "Test response"
```

### 2. Test Naming Convention
Test methods follow the pattern: `test_<method>_<scenario>`

Examples:
- `test_transcribe_silent_audio_returns_empty`
- `test_from_env_missing_api_key_raises_error`
- `test_message_with_multiline_content`

### 3. Arrange-Act-Assert Pattern
Tests are structured in three clear phases:

```python
def test_example(self):
    # Arrange: Set up test data and mocks
    audio = np.zeros(16000, dtype=np.float32)
    
    # Act: Execute the code under test
    result = stt.transcribe(audio)
    
    # Assert: Verify the results
    assert result == ""
```

### 4. Test Isolation
Each test is independent and can run in any order. Tests use:
- Fresh instances of objects
- Temporary files/directories (cleaned up automatically)
- Environment variable cleanup

### 5. Fixtures
Common test fixtures are defined in `conftest.py`:
- `sample_chat_message`: Reusable ChatMessage instance
- `sample_audio_data`: Sample audio array for audio tests
- `mock_openai_client`: Mocked OpenAI client

## Notes on Untested Components

Some components are not tested due to environmental constraints:

### Audio Infrastructure
- `infrastructure/audio/listener.py` and `infrastructure/audio/speaker.py` require PortAudio library, which is not available in all test environments
- These components involve hardware interaction that is better suited for integration/manual testing

### Presentation Layer
- GUI components (`presentation/main_window.py`, `presentation/conversation_worker.py`) require Qt/PySide6 and are best tested with integration or E2E tests

### DI Container
- `di_container.py` depends on audio infrastructure components that require PortAudio
- The container's wiring logic is validated through integration testing when the application runs

## Adding New Tests

When adding new tests:

1. Follow the DDD structure - place tests in the corresponding directory
2. Create descriptive test names that explain the scenario
3. Mock external dependencies (APIs, file system, databases)
4. Use fixtures from `conftest.py` for common test data
5. Ensure tests are isolated and don't depend on execution order
6. Test both happy paths and error cases
7. Include boundary condition tests

Example:
```python
class TestNewFeature:
    """Test cases for NewFeature."""

    def test_feature_with_valid_input(self):
        """Test that feature works with valid input."""
        # Test implementation
        
    def test_feature_with_empty_input_raises_error(self):
        """Test that feature raises error on empty input."""
        # Test implementation
```
