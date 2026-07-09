# Contributing Guidelines

Thank you for your interest in contributing to the **Multi-Agent Anomaly Detection System**! We welcome bug reports, feature requests, documentation improvements, and code submissions.

To ensure high-quality contributions and maintainability, please adhere to the following development guidelines.

---

## 1. Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to the project maintainers.

## 2. Setting Up Your Development Environment

1.  **Fork and Clone** the repository:
    ```bash
    git clone https://github.com/Abhishektiwari050/multi-agent-anomaly-system.git
    cd multi-agent-anomaly-system
    ```
2.  **Create a Virtual Environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    pip install ruff mypy pytest pytest-cov pytest-asyncio pre-commit
    ```
4.  **Install Pre-Commit Hooks**:
    ```bash
    pre-commit install
    ```

---

## 3. Coding Style & Linting

We enforce clean, type-safe, and consistently formatted code using **Ruff** and **Mypy**:

*   **Linting**: Run `ruff check .` to check for code issues. Run `ruff check . --fix` to auto-resolve simple issues.
*   **Formatting**: Run `ruff format .` to auto-format files.
*   **Type Safety**: Run `mypy --ignore-missing-imports shared api agents execution-agent` to check static typing contracts.

---

## 4. Writing & Running Tests

Start a local RabbitMQ broker (e.g. via Docker Compose: `docker compose up -d rabbitmq`) and run the test suite:

*   **Run pytest**:
    ```bash
    pytest
    ```
*   **Run with coverage**:
    ```bash
    pytest --cov=shared --cov=api --cov=agents --cov-report=term-missing
    ```

Always add corresponding unit/integration tests when modifying logic.

---

## 5. Pull Request Workflow

1.  **Create a Branch**: Create a feature branch off of the `master` branch.
    ```bash
    git checkout -b feature/your-awesome-feature
    ```
2.  **Make Atomic Commits**: Keep changes small and write descriptive commit messages.
3.  **Format and Validate**: Ensure your code passes all lint and type tests locally before pushing.
4.  **Submit PR**: Push to your branch and open a Pull Request against the main repository `master` branch.
5.  **Address Review Feedback**: Collaborate with project maintainers to merge your branch.
