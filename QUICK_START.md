# TestForge Quick Start

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Run TestForge

### Windows:
```bash
run.bat
```

### Linux/Mac:
```bash
streamlit run src/ui/app.py
```

## Usage

1. **Send HTTP Request**
   - Select HTTP method (GET/POST/PUT/DELETE)
   - Enter URL
   - Configure headers, params, body (JSON format)
   - Click "Send Request"

2. **Add Assertions**
   - Write Python expressions (one per line)
   - Examples:
     ```
     status == 200
     response['success'] == True
     elapsed_ms < 1000
     ```

3. **Save Test Cases**
   - Click "Save Current Test"
   - Test cases saved as YAML files in `./testcases`

4. **Load Test Cases**
   - Select from dropdown
   - Click "Load"

## Examples

### GET Request with Assertions:
```yaml
URL: https://httpbin.org/get
Method: GET
Assertions:
  status == 200
  response['url'] != None
```

### POST Request with JSON Body:
```yaml
URL: https://httpbin.org/post
Method: POST
Headers:
  {
    "Content-Type": "application/json"
  }
Body:
  {
    "test": "data"
  }
Assertions:
  status == 200
  response['json']['test'] == 'data'
```

## Architecture

```
TestForge
├── src/
│   ├── protocols/     # Protocol handlers (HTTP, Protobuf future)
│   ├── core/          # Business logic (Assertion engine)
│   ├── storage/       # Data persistence (YAML)
│   └── ui/            # Streamlit interface
└── testcases/         # Saved test cases
```

## Next Steps

- [ ] Try sending your first request
- [ ] Create and save a test case
- [ ] Add custom assertions
- [ ] Explore saved test cases

Happy testing! 🚀
