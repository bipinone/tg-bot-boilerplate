# Contributing to TeleCore

Thank you for investing your time in contributing to **TeleCore**!

## Development Setup

1. **Fork the repository** on GitHub.
2. **Clone your fork**:
   ```bash
   git clone https://github.com/<your-username>/tg-bot-boilerplate.git
   cd tg-bot-boilerplate
   ```
3. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Run the test suite**:
   ```bash
   python -m unittest discover tests
   ```

## Creating a Pull Request

1. Create a branch for your feature or fix:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Make your modifications following PEP 8 conventions.
3. Ensure all automated tests pass before submitting.
4. Submit a Pull Request targeting the `main` branch with a clear description of the problem and solution.
